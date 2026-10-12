"""Tests de responder() y de las métricas, sin OpenAI ni Langfuse."""
from types import SimpleNamespace

import pytest
from langchain_core.runnables import RunnableLambda

from src.config import cargar_config
from src.multi_agent_system import calcular_metricas, responder

EVALUACION = {"relevance": 8, "completeness": 6, "accuracy": 10, "overall": 8, "razon": "ok"}


@pytest.fixture
def config(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    return cargar_config(usar_dotenv=False)


def sistema_falso(departamento):
    def correr(entrada):
        return {
            "consulta": entrada["consulta"],
            "clasificacion": {"departamento": departamento, "confianza": 0.8, "razon": "r", "error": False},
            "resultado": {"departamento": departamento, "respuesta": "resp", "fuentes": [], "contexto": "ctx"},
        }
    return RunnableLambda(correr)


def juez_falso():
    return SimpleNamespace(with_structured_output=lambda esquema: RunnableLambda(lambda p: EVALUACION))


@pytest.mark.parametrize("consulta", ["", "   ", None])
def test_consulta_vacia_falla_antes_de_gastar_api(config, consulta):
    with pytest.raises(ValueError, match="vacía"):
        responder(consulta, config, sistema=sistema_falso("hr"), con_evaluador=False)


def test_responder_sin_langfuse_ni_evaluador(config):
    salida = responder("  ¿vacaciones?  ", config, sistema=sistema_falso("hr"), con_evaluador=False)
    assert salida["consulta"] == "¿vacaciones?"
    assert salida["departamento"] == "hr"
    assert salida["trace_id"] is None
    assert salida["evaluacion"] is None
    assert "contexto" not in salida


def test_responder_con_evaluador(config):
    salida = responder("¿vacaciones?", config, sistema=sistema_falso("hr"), llm_evaluador=juez_falso())
    assert salida["evaluacion"] == EVALUACION


def test_fuera_de_dominio_no_se_evalua(config):
    salida = responder("poema", config, sistema=sistema_falso("fuera_de_dominio"), llm_evaluador=juez_falso())
    assert salida["evaluacion"] is None


def test_si_el_evaluador_falla_la_respuesta_se_entrega(config, capsys):
    def explotar(prompt):
        raise RuntimeError("juez caído")
    juez = SimpleNamespace(with_structured_output=lambda esquema: RunnableLambda(explotar))
    salida = responder("¿vacaciones?", config, sistema=sistema_falso("hr"), llm_evaluador=juez)
    assert salida["respuesta"] == "resp"
    assert salida["evaluacion"] is None
    assert "juez caído" in capsys.readouterr().err


def fila(id, esperado, obtenido, etapa_error=None, evaluacion=None, trace_id=None):
    """Fila de resultado como la arma medir_test_queries."""
    return {
        "id": id, "consulta": f"consulta {id}", "departamento_esperado": esperado,
        "departamento_obtenido": obtenido, "etapa_error": etapa_error,
        "error": "falla" if etapa_error else None,
        "respuesta_completada": etapa_error is None and obtenido is not None,
        "trace_id": trace_id, "evaluacion": evaluacion,
    }


def test_calcular_metricas_separa_acierto_de_errores_tecnicos():
    resultados = [
        fila(1, "hr", "hr", evaluacion=EVALUACION, trace_id="t1"),
        fila(2, "hr", "finance", trace_id="t2"),
        # El clasificador falló y cayó en fuera_de_dominio: NO es un acierto.
        fila(3, "fuera_de_dominio", "fuera_de_dominio", etapa_error="clasificacion"),
        # Clasificó bien pero falló la generación: el routing correcto se conserva.
        fila(4, "tech", "tech", etapa_error="respuesta", trace_id="t4"),
    ]
    metricas = calcular_metricas(resultados)
    assert metricas["total"] == 4
    assert metricas["clasificaciones_validas"] == 3
    assert metricas["cobertura"] == 0.75
    assert metricas["aciertos"] == 2
    assert metricas["acierto_clasificacion"] == 0.667
    assert metricas["por_departamento"]["hr"] == {"total": 2, "validas": 2, "aciertos": 1, "acierto": 0.5}
    assert metricas["por_departamento"]["fuera_de_dominio"]["acierto"] is None
    assert [m["id"] for m in metricas["mal_enrutadas"]] == [2]
    assert metricas["mal_enrutadas"][0]["trace_id"] == "t2"
    assert metricas["errores_tecnicos"] == {"clasificacion": 1, "respuesta": 1}
    assert [e["id"] for e in metricas["detalle_errores"]] == [3, 4]
    assert metricas["respuestas_completadas"] == 2
    assert metricas["promedios_evaluador"]["completeness"] == 6.0
    assert metricas["respuestas_evaluadas"] == 1


def test_calcular_metricas_sin_resultados():
    metricas = calcular_metricas([])
    assert metricas["acierto_clasificacion"] is None
    assert metricas["cobertura"] == 0.0
    assert metricas["promedios_evaluador"] == {}


def sistema_con(clasificacion_error=False, error_respuesta=None, departamento="hr"):
    """Sistema falso que simula fallas del clasificador o del agente."""
    def correr(entrada):
        resultado = {"departamento": departamento, "respuesta": "resp", "fuentes": [], "contexto": "ctx"}
        if error_respuesta:
            resultado = {"departamento": departamento, "respuesta": None, "fuentes": [], "contexto": "", "error": error_respuesta}
        return {
            "consulta": entrada["consulta"],
            "clasificacion": {"departamento": departamento, "confianza": 0.0 if clasificacion_error else 0.8,
                              "razon": "Error al clasificar: 503" if clasificacion_error else "r",
                              "error": clasificacion_error},
            "resultado": resultado,
        }
    return RunnableLambda(correr)


def test_falla_de_generacion_conserva_la_clasificacion(config):
    salida = responder("¿vacaciones?", config, sistema=sistema_con(error_respuesta="timeout"), llm_evaluador=juez_falso())
    assert salida["departamento"] == "hr"
    assert salida["etapa_error"] == "respuesta"
    assert "timeout" in salida["error"]
    assert salida["respuesta_completada"] is False
    assert salida["evaluacion"] is None  # no se evalúa una respuesta que no existe


def test_falla_del_clasificador_se_marca_como_error_tecnico(config):
    salida = responder("hola", config, sistema=sistema_con(clasificacion_error=True, departamento="fuera_de_dominio"), con_evaluador=False)
    assert salida["etapa_error"] == "clasificacion"
    assert salida["respuesta_completada"] is False


def test_respuesta_normal_no_tiene_error(config):
    salida = responder("¿vacaciones?", config, sistema=sistema_con(), con_evaluador=False)
    assert salida["etapa_error"] is None
    assert salida["error"] is None
    assert salida["respuesta_completada"] is True


def cliente_langfuse_falso(registro):
    """Imita el cliente de Langfuse 3.x y anota cada llamada en 'registro'."""
    from contextlib import contextmanager

    span = SimpleNamespace(
        trace_id="traza-1",
        update_trace=lambda **datos: registro.append(("update_trace", datos)),
        update=lambda **datos: registro.append(("update", datos)),
    )

    @contextmanager
    def start_as_current_span(**datos):
        yield span

    return SimpleNamespace(
        start_as_current_span=start_as_current_span,
        create_score=lambda **datos: registro.append(("score", datos)),
        flush=lambda: registro.append(("flush", {})),
    )


@pytest.fixture
def con_langfuse_falso(monkeypatch):
    from langchain_core.callbacks import BaseCallbackHandler

    import src.multi_agent_system as sistema_mod

    registro = []
    monkeypatch.setattr(sistema_mod, "obtener_cliente_langfuse", lambda config: cliente_langfuse_falso(registro))
    monkeypatch.setattr(sistema_mod, "crear_handler", lambda config: BaseCallbackHandler())
    return registro


def test_con_langfuse_una_traza_con_scores_tags_y_flush(config, con_langfuse_falso):
    salida = responder("¿vacaciones?", config, sistema=sistema_falso("hr"), llm_evaluador=juez_falso())
    nombres = [nombre for nombre, datos in con_langfuse_falso]
    assert salida["trace_id"] == "traza-1"
    assert nombres.count("score") == 4
    assert next(d for n, d in con_langfuse_falso if n == "update_trace")["tags"] == ["hr"]
    assert nombres[-1] == "flush"


def test_con_langfuse_un_error_marca_el_span_y_hace_flush(config, con_langfuse_falso):
    def explotar(entrada):
        raise RuntimeError("falla inesperada")

    with pytest.raises(RuntimeError):
        responder("¿vacaciones?", config, sistema=RunnableLambda(explotar), con_evaluador=False)
    nombres = [nombre for nombre, datos in con_langfuse_falso]
    assert ("update", {"level": "ERROR", "status_message": "falla inesperada"}) in con_langfuse_falso
    assert nombres[-1] == "flush"


def test_con_langfuse_un_error_de_respuesta_marca_el_span(config, con_langfuse_falso):
    responder("¿vacaciones?", config, sistema=sistema_con(error_respuesta="timeout"), con_evaluador=False)
    assert any(n == "update" and d["level"] == "ERROR" for n, d in con_langfuse_falso)
