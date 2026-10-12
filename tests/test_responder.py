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


def test_calcular_metricas():
    resultados = [
        {"id": 1, "consulta": "a", "departamento_esperado": "hr", "departamento_obtenido": "hr", "trace_id": "t1", "evaluacion": EVALUACION, "error": None},
        {"id": 2, "consulta": "b", "departamento_esperado": "hr", "departamento_obtenido": "finance", "trace_id": "t2", "evaluacion": None, "error": None},
        {"id": 3, "consulta": "c", "departamento_esperado": "tech", "departamento_obtenido": None, "trace_id": None, "evaluacion": None, "error": "503"},
    ]
    metricas = calcular_metricas(resultados)
    assert metricas["total"] == 3
    assert metricas["aciertos"] == 1
    assert metricas["acierto_total"] == 0.333
    assert metricas["por_departamento"]["hr"] == {"total": 2, "aciertos": 1, "acierto": 0.5}
    assert [fila["id"] for fila in metricas["mal_enrutadas"]] == [2, 3]
    assert metricas["mal_enrutadas"][0]["trace_id"] == "t2"
    assert metricas["mal_enrutadas"][1]["error"] == "503"
    assert metricas["promedios_evaluador"]["completeness"] == 6.0
    assert metricas["respuestas_evaluadas"] == 1


def test_calcular_metricas_sin_resultados():
    metricas = calcular_metricas([])
    assert metricas["acierto_total"] == 0.0
    assert metricas["promedios_evaluador"] == {}
