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

    # Si el agente falla (p. ej. un timeout de OpenAI), no perdemos la clasificación
    # ya lograda: devolvemos un resultado sin respuesta y con el error.
    def enrutar_protegido(entrada, config):
        try:
            return enrutador.invoke(entrada, config=config)
        except Exception as error:
            return {
                "departamento": entrada["clasificacion"]["departamento"],
                "respuesta": None,
                "fuentes": [],
                "contexto": "",
                "error": str(error),
            }

    # assign agrega claves al diccionario sin perder la consulta original.
    cadena = RunnablePassthrough.assign(clasificacion=orquestador) | RunnablePassthrough.assign(
        resultado=RunnableLambda(enrutar_protegido, name="enrutador")
    )
    return cadena.with_config(run_name="sistema_multiagente")


def validar_consulta(consulta):
    """Rechaza consultas vacías antes de gastar llamadas a la API."""
    if consulta is None or not consulta.strip():
        raise ValueError("La consulta está vacía: escribe una pregunta.")
    return consulta.strip()


def etapa_del_error(clasificacion, resultado):
    """En qué etapa falló la consulta: "clasificacion", "respuesta" o None."""
    if clasificacion.get("error"):
        return "clasificacion"
    if resultado.get("error"):
        return "respuesta"
    return None


def ejecutar_sistema(sistema, consulta, callbacks):
    """Invoca la cadena y aplana su salida en un solo diccionario."""
    salida = sistema.invoke({"consulta": consulta}, config={"callbacks": callbacks})
    clasificacion = salida["clasificacion"]
    resultado = salida["resultado"]
    etapa_error = etapa_del_error(clasificacion, resultado)
    error = None
    if etapa_error == "clasificacion":
        error = clasificacion["razon"]
    elif etapa_error == "respuesta":
        error = resultado["error"]
    return {
        "consulta": consulta,
        "departamento": resultado["departamento"],
        "confianza": clasificacion["confianza"],
        "razon": clasificacion["razon"],
        "respuesta": resultado["respuesta"],
        "fuentes": resultado["fuentes"],
        "contexto": resultado["contexto"],
        "error_clasificacion": clasificacion.get("error", False),
        "etapa_error": etapa_error,
        "error": error,
        # Completada = se clasificó bien y el agente generó su respuesta sin errores.
        "respuesta_completada": etapa_error is None,
        "trace_id": None,
        "evaluacion": None,
    }


def evaluar_si_corresponde(salida, llm_evaluador, callbacks):
    """Evalúa la respuesta RAG; None si no hubo RAG, si hubo error o si el juez falla."""
    if salida["departamento"] == FUERA_DE_DOMINIO or salida["etapa_error"] is not None:
        return None  # no hay una respuesta RAG que evaluar
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


def responder(consulta, config, sistema=None, con_evaluador=True, llm_evaluador=None, cliente="crear"):
    """Punto de entrada: una consulta -> respuesta (y una traza en Langfuse).

    cliente: "crear" lo crea aquí; también se puede pasar uno ya creado (o None para
    no trazar), así medir_test_queries comprueba la conexión una sola vez.
    """
    consulta = validar_consulta(consulta)
    if sistema is None:
        sistema = crear_sistema(config)
    if cliente == "crear":
        cliente = obtener_cliente_langfuse(config)

    if cliente is None:
        salida = procesar(consulta, config, sistema, con_evaluador, llm_evaluador, [], None, None)
    else:
        try:
            # Un span "padre": todo lo que pase adentro queda en UNA sola traza.
            with cliente.start_as_current_span(name="consulta_soporte", input={"consulta": consulta}) as span:
                callbacks = [crear_handler(config)]
                try:
                    salida = procesar(
                        consulta, config, sistema, con_evaluador, llm_evaluador,
                        callbacks, cliente, span.trace_id,
                    )
                except Exception as error:
                    # La traza queda marcada como error para encontrarla en Langfuse.
                    span.update(level="ERROR", status_message=str(error))
                    raise
                # Tags y metadata permiten filtrar en Langfuse (p. ej. baja confianza).
                span.update_trace(
                    tags=[salida["departamento"]],
                    metadata={
                        "confianza": salida["confianza"],
                        "razon": salida["razon"],
                        "error_clasificacion": salida["error_clasificacion"],
                        "etapa_error": salida["etapa_error"],
                    },
                    output={"respuesta": salida["respuesta"], "fuentes": salida["fuentes"]},
                )
                if salida["etapa_error"] is not None:
                    span.update(level="ERROR", status_message=salida["error"])
        finally:
            cliente.flush()  # envía las trazas aunque algo haya fallado

    del salida["contexto"]  # el contexto solo sirve internamente (evaluador)
    return salida


def proporcion(parte, total):
    """parte / total redondeado; None si no hay nada que dividir."""
    if total == 0:
        return None
    return round(parte / total, 3)


def calcular_metricas(resultados):
    """Acierto de clasificación, errores técnicos y calidad, medidos por separado.

    Un error técnico no se mezcla con el acierto de routing:
    - si falló el clasificador, la fila NO cuenta como clasificación válida
      (aunque haya caído en fuera_de_dominio por accidente);
    - si falló la respuesta, la clasificación lograda SÍ cuenta.
    """
    validas = 0
    aciertos = 0
    por_departamento = {}
    mal_enrutadas = []
    errores_tecnicos = {}
    detalle_errores = []
    completadas = 0
    sumas = {dimension: 0.0 for dimension in DIMENSIONES}
    evaluadas = 0
    for fila in resultados:
        esperado = fila["departamento_esperado"]
        if esperado not in por_departamento:
            por_departamento[esperado] = {"total": 0, "validas": 0, "aciertos": 0}
        por_departamento[esperado]["total"] += 1

        etapa = fila["etapa_error"]
        if etapa is not None:
            errores_tecnicos[etapa] = errores_tecnicos.get(etapa, 0) + 1
            detalle_errores.append({
                "id": fila["id"], "etapa": etapa, "error": fila["error"], "trace_id": fila["trace_id"],
            })
        if fila["respuesta_completada"]:
            completadas += 1

        clasificacion_valida = fila["departamento_obtenido"] is not None and etapa != "clasificacion"
        if clasificacion_valida:
            validas += 1
            por_departamento[esperado]["validas"] += 1
            if fila["departamento_obtenido"] == esperado:
                aciertos += 1
                por_departamento[esperado]["aciertos"] += 1
            else:
                mal_enrutadas.append({
                    "id": fila["id"], "consulta": fila["consulta"], "esperado": esperado,
                    "obtenido": fila["departamento_obtenido"], "trace_id": fila["trace_id"],
                })

        if fila["evaluacion"]:
            evaluadas += 1
            for dimension in DIMENSIONES:
                sumas[dimension] += fila["evaluacion"][dimension]

    for datos in por_departamento.values():
        datos["acierto"] = proporcion(datos["aciertos"], datos["validas"])
    promedios = {}
    if evaluadas:
        promedios = {dimension: round(sumas[dimension] / evaluadas, 2) for dimension in DIMENSIONES}
    return {
        "total": len(resultados),
        "clasificaciones_validas": validas,
        "cobertura": proporcion(validas, len(resultados)) or 0.0,
        "aciertos": aciertos,
        "acierto_clasificacion": proporcion(aciertos, validas),
        "por_departamento": por_departamento,
        "mal_enrutadas": mal_enrutadas,
        "errores_tecnicos": errores_tecnicos,
        "detalle_errores": detalle_errores,
        "respuestas_completadas": completadas,
        "promedios_evaluador": promedios,
        "respuestas_evaluadas": evaluadas,
    }


def imprimir_resumen(metricas):
    print(f"\nClasificaciones válidas: {metricas['clasificaciones_validas']}/{metricas['total']} "
          f"(cobertura {metricas['cobertura']:.1%})")
    if metricas["acierto_clasificacion"] is not None:
        print(f"Acierto de clasificación: {metricas['aciertos']}/{metricas['clasificaciones_validas']} "
              f"({metricas['acierto_clasificacion']:.1%})")
    for departamento, datos in metricas["por_departamento"].items():
        print(f"  {departamento:<17} {datos['aciertos']}/{datos['validas']} válidas "
              f"({datos['total']} consultas)")
    for fila in metricas["mal_enrutadas"]:
        print(f"  MAL #{fila['id']}: esperado {fila['esperado']}, obtenido {fila['obtenido']} "
              f"(traza {fila['trace_id']})")
    print(f"Errores técnicos por etapa: {metricas['errores_tecnicos'] or 'ninguno'}")
    for fila in metricas["detalle_errores"]:
        print(f"  ERROR #{fila['id']} ({fila['etapa']}): {fila['error']} (traza {fila['trace_id']})")
    print(f"Respuestas completadas: {metricas['respuestas_completadas']}/{metricas['total']}")
    if metricas["promedios_evaluador"]:
        print(f"Promedios del evaluador ({metricas['respuestas_evaluadas']} respuestas): "
              f"{metricas['promedios_evaluador']}")


def medir_test_queries(config, ruta_queries, ruta_salida, con_evaluador=True):
    """Corre todas las test queries; un error en una no detiene a las demás."""
    consultas = json.loads(Path(ruta_queries).read_text(encoding="utf-8"))
    sistema = crear_sistema(config)
    cliente = obtener_cliente_langfuse(config)  # una sola vez para todas las consultas
    resultados = []
    for caso in consultas:
        fila = {
            "id": caso["id"], "consulta": caso["consulta"], "tipo": caso["tipo"],
            "departamento_esperado": caso["departamento_esperado"],
            "departamento_obtenido": None, "respuesta": None, "trace_id": None,
            "evaluacion": None, "etapa_error": None, "error": None,
            "respuesta_completada": False,
        }
        try:
            salida = responder(
                caso["consulta"], config, sistema=sistema,
                con_evaluador=con_evaluador, cliente=cliente,
            )
            for clave in ["respuesta", "trace_id", "evaluacion", "etapa_error", "error", "respuesta_completada"]:
                fila[clave] = salida[clave]
            fila["departamento_obtenido"] = salida["departamento"]
        except Exception as error:
            # Error que ni siquiera dejó una clasificación: etapa desconocida.
            fila["etapa_error"] = "desconocida"
            fila["error"] = str(error)
        print(f"[{caso['id']}] esperado={fila['departamento_esperado']} "
              f"obtenido={fila['departamento_obtenido']} error={fila['etapa_error']}")
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
