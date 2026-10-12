"""Sistema multiagente: orquestador + enrutamiento condicional + agentes RAG.

Flujo (todo con LCEL, el "lenguaje de tuberías" de LangChain):
    consulta -> orquestador (clasifica) -> RunnableBranch (elige agente) -> respuesta
"""
import argparse
import json
import sys
from pathlib import Path

from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnablePassthrough

from src.agents.finance_agent import crear_finance_agent
from src.agents.hr_agent import crear_hr_agent
from src.agents.orchestrator import crear_orquestador
from src.agents.tech_agent import crear_tech_agent
from src.config import FUERA_DE_DOMINIO, RAIZ, cargar_config, crear_llm
from src.evaluator import DIMENSIONES, evaluar, registrar_scores
from src.indexacion import indexar_todo
from src.observabilidad import crear_handler, obtener_cliente_langfuse

MENSAJE_FUERA_DE_DOMINIO = (
    "Solo puedo ayudarte con consultas de Recursos Humanos, Soporte de TI o Finanzas "
    "de NubeGestor. ¿Puedes reformular tu pregunta sobre alguno de esos temas?"
)


def respuesta_fuera_de_dominio(entrada):
    """Ruta sin LLM ni retriever: no gastamos API en lo que no es de ningún área."""
    return {
        "departamento": FUERA_DE_DOMINIO,
        "respuesta": MENSAJE_FUERA_DE_DOMINIO,
        "fuentes": [],
        "contexto": "",
    }


def es_departamento(nombre):
    """Crea la condición que usa RunnableBranch para una ruta."""

    def condicion(entrada):
        return entrada["clasificacion"]["departamento"] == nombre

    return condicion


def crear_sistema(config, orquestador=None, agentes=None):
    """Arma la cadena completa. orquestador y agentes se pueden inyectar en los tests."""
    if orquestador is None:
        orquestador = crear_orquestador(crear_llm(config))
    if agentes is None:
        indexar_todo(config)  # si falta el índice, se crea (si existe, no gasta nada)
        agentes = {
            "hr": crear_hr_agent(config),
            "tech": crear_tech_agent(config),
            "finance": crear_finance_agent(config),
        }
    # RunnableBranch prueba las condiciones en orden; la última opción es el default.
    enrutador = RunnableBranch(
        (es_departamento("hr"), agentes["hr"]),
        (es_departamento("tech"), agentes["tech"]),
        (es_departamento("finance"), agentes["finance"]),
        RunnableLambda(respuesta_fuera_de_dominio, name="fuera_de_dominio"),
    )
    # assign agrega claves al diccionario sin perder la consulta original.
    cadena = RunnablePassthrough.assign(clasificacion=orquestador) | RunnablePassthrough.assign(
        resultado=enrutador
    )
    return cadena.with_config(run_name="sistema_multiagente")


def validar_consulta(consulta):
    """Rechaza consultas vacías antes de gastar llamadas a la API."""
    if consulta is None or not consulta.strip():
        raise ValueError("La consulta está vacía: escribe una pregunta.")
    return consulta.strip()


def ejecutar_sistema(sistema, consulta, callbacks):
    """Invoca la cadena y aplana su salida en un solo diccionario."""
    salida = sistema.invoke({"consulta": consulta}, config={"callbacks": callbacks})
    clasificacion = salida["clasificacion"]
    resultado = salida["resultado"]
    return {
        "consulta": consulta,
        "departamento": resultado["departamento"],
        "confianza": clasificacion["confianza"],
        "razon": clasificacion["razon"],
        "respuesta": resultado["respuesta"],
        "fuentes": resultado["fuentes"],
        "contexto": resultado["contexto"],
        "error_clasificacion": clasificacion.get("error", False),
        "trace_id": None,
        "evaluacion": None,
    }


def evaluar_si_corresponde(salida, llm_evaluador, callbacks):
    """Evalúa la respuesta RAG; None si es fuera de dominio o si el juez falla."""
    if salida["departamento"] == FUERA_DE_DOMINIO:
        return None  # no hubo RAG: no hay nada que evaluar
    try:
        return evaluar(
            salida["consulta"], salida["respuesta"], salida["contexto"],
            llm_evaluador, config={"callbacks": callbacks},
        )
    except Exception as error:
        print(f"[aviso] El evaluador falló: {error}", file=sys.stderr)
        return None


def procesar(consulta, config, sistema, con_evaluador, llm_evaluador, callbacks, cliente, trace_id):
    """Corre el sistema y, si corresponde, el evaluador con sus scores."""
    salida = ejecutar_sistema(sistema, consulta, callbacks)
    salida["trace_id"] = trace_id
    if con_evaluador:
        if llm_evaluador is None:
            llm_evaluador = crear_llm(config)
        salida["evaluacion"] = evaluar_si_corresponde(salida, llm_evaluador, callbacks)
        if salida["evaluacion"] is not None:
            registrar_scores(cliente, trace_id, salida["evaluacion"])
    return salida


def responder(consulta, config, sistema=None, con_evaluador=True, llm_evaluador=None):
    """Punto de entrada: una consulta -> respuesta (y una traza en Langfuse)."""
    consulta = validar_consulta(consulta)
    if sistema is None:
        sistema = crear_sistema(config)
    cliente = obtener_cliente_langfuse(config)

    if cliente is None:
        salida = procesar(consulta, config, sistema, con_evaluador, llm_evaluador, [], None, None)
    else:
        # Un span "padre": todo lo que pase adentro queda en UNA sola traza.
        with cliente.start_as_current_span(name="consulta_soporte", input={"consulta": consulta}) as span:
            callbacks = [crear_handler(config)]
            salida = procesar(
                consulta, config, sistema, con_evaluador, llm_evaluador,
                callbacks, cliente, span.trace_id,
            )
            # Tags y metadata permiten filtrar en Langfuse (p. ej. baja confianza).
            span.update_trace(
                tags=[salida["departamento"]],
                metadata={
                    "confianza": salida["confianza"],
                    "razon": salida["razon"],
                    "error_clasificacion": salida["error_clasificacion"],
                },
                output={"respuesta": salida["respuesta"], "fuentes": salida["fuentes"]},
            )
        cliente.flush()  # envía las trazas antes de terminar

    del salida["contexto"]  # el contexto solo sirve internamente (evaluador)
    return salida


def calcular_metricas(resultados):
    """Acierto de enrutamiento, mal enrutadas y promedios del evaluador."""
    aciertos = 0
    por_departamento = {}
    mal_enrutadas = []
    sumas = {dimension: 0.0 for dimension in DIMENSIONES}
    evaluadas = 0
    for fila in resultados:
        esperado = fila["departamento_esperado"]
        if esperado not in por_departamento:
            por_departamento[esperado] = {"total": 0, "aciertos": 0}
        por_departamento[esperado]["total"] += 1
        if fila["departamento_obtenido"] == esperado:
            aciertos += 1
            por_departamento[esperado]["aciertos"] += 1
        else:
            mal_enrutadas.append({
                "id": fila["id"], "consulta": fila["consulta"], "esperado": esperado,
                "obtenido": fila["departamento_obtenido"], "trace_id": fila["trace_id"],
                "error": fila["error"],
            })
        if fila["evaluacion"]:
            evaluadas += 1
            for dimension in DIMENSIONES:
                sumas[dimension] += fila["evaluacion"][dimension]
    for datos in por_departamento.values():
        datos["acierto"] = round(datos["aciertos"] / datos["total"], 3)
    promedios = {}
    if evaluadas:
        promedios = {dimension: round(sumas[dimension] / evaluadas, 2) for dimension in DIMENSIONES}
    return {
        "total": len(resultados),
        "aciertos": aciertos,
        "acierto_total": round(aciertos / len(resultados), 3) if resultados else 0.0,
        "por_departamento": por_departamento,
        "mal_enrutadas": mal_enrutadas,
        "promedios_evaluador": promedios,
        "respuestas_evaluadas": evaluadas,
    }


def imprimir_resumen(metricas):
    print(f"\nAcierto de enrutamiento: {metricas['aciertos']}/{metricas['total']} "
          f"({metricas['acierto_total']:.1%})")
    for departamento, datos in metricas["por_departamento"].items():
        print(f"  {departamento:<17} {datos['aciertos']}/{datos['total']}")
    for fila in metricas["mal_enrutadas"]:
        print(f"  MAL #{fila['id']}: esperado {fila['esperado']}, obtenido {fila['obtenido']} "
              f"(traza {fila['trace_id']}, error {fila['error']})")
    if metricas["promedios_evaluador"]:
        print(f"Promedios del evaluador: {metricas['promedios_evaluador']}")


def medir_test_queries(config, ruta_queries, ruta_salida, con_evaluador=True):
    """Corre todas las test queries; un error en una no detiene a las demás."""
    consultas = json.loads(Path(ruta_queries).read_text(encoding="utf-8"))
    sistema = crear_sistema(config)
    resultados = []
    for caso in consultas:
        fila = {
            "id": caso["id"], "consulta": caso["consulta"], "tipo": caso["tipo"],
            "departamento_esperado": caso["departamento_esperado"],
            "departamento_obtenido": None, "respuesta": None, "trace_id": None,
            "evaluacion": None, "error": None,
        }
        try:
            salida = responder(caso["consulta"], config, sistema=sistema, con_evaluador=con_evaluador)
            fila["departamento_obtenido"] = salida["departamento"]
            fila["respuesta"] = salida["respuesta"]
            fila["trace_id"] = salida["trace_id"]
            fila["evaluacion"] = salida["evaluacion"]
        except Exception as error:
            fila["error"] = str(error)
        print(f"[{caso['id']}] esperado={fila['departamento_esperado']} obtenido={fila['departamento_obtenido']}")
        resultados.append(fila)
    metricas = calcular_metricas(resultados)
    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
    Path(ruta_salida).write_text(
        json.dumps({"metricas": metricas, "resultados": resultados}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    imprimir_resumen(metricas)
    return metricas


def main(argumentos=None):
    sys.stdout.reconfigure(encoding="utf-8")  # tildes en la consola de Windows
    parser = argparse.ArgumentParser(description="Sistema multiagente de soporte de NubeGestor.")
    parser.add_argument("consulta", nargs="?", help="pregunta del usuario")
    parser.add_argument("--evaluar-queries", action="store_true", help="corre test_queries.json")
    parser.add_argument("--sin-evaluador", action="store_true", help="no puntúa las respuestas")
    parser.add_argument("--model", help="modelo de chat (sobrescribe OPENAI_MODEL)")
    parser.add_argument("--k", type=int, help="chunks por consulta (sobrescribe RAG_K)")
    args = parser.parse_args(argumentos)
    config = cargar_config({"modelo_chat": args.model, "rag_k": args.k})
    con_evaluador = not args.sin_evaluador

    if args.evaluar_queries:
        medir_test_queries(
            config, RAIZ / "test_queries.json",
            RAIZ / "outputs" / "resultados_test_queries.json", con_evaluador,
        )
        return
    if not args.consulta:
        parser.error("escribe una consulta entre comillas o usa --evaluar-queries")
    salida = responder(args.consulta, config, con_evaluador=con_evaluador)
    print(json.dumps(salida, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
