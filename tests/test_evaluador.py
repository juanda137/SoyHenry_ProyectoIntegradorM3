"""Tests del evaluador con LLM y cliente de Langfuse falsos."""
from types import SimpleNamespace

import pytest
from langchain_core.runnables import RunnableLambda

from src.evaluator import DIMENSIONES, evaluar, registrar_scores, validar_evaluacion

EVALUACION = {"relevance": 8, "completeness": 7, "accuracy": 9, "overall": 8, "razon": "bien"}


def test_validar_acepta_valores_en_rango():
    assert validar_evaluacion(EVALUACION) == EVALUACION


@pytest.mark.parametrize("valor", [0, 11, -3])
def test_validar_rechaza_fuera_de_rango(valor):
    with pytest.raises(ValueError):
        validar_evaluacion({**EVALUACION, "accuracy": valor})


def test_evaluar_usa_consulta_respuesta_y_contexto():
    vistos = []

    def juez(prompt):
        vistos.append(prompt.to_string())
        return EVALUACION

    llm = SimpleNamespace(with_structured_output=lambda esquema: RunnableLambda(juez))
    resultado = evaluar("¿viáticos?", "USD 60", "contexto X", llm)
    assert resultado == EVALUACION
    assert "¿viáticos?" in vistos[0] and "USD 60" in vistos[0] and "contexto X" in vistos[0]


def test_registrar_scores_envia_las_cuatro_dimensiones():
    llamadas = []
    cliente = SimpleNamespace(create_score=lambda **datos: llamadas.append(datos))
    assert registrar_scores(cliente, "traza-1", EVALUACION) is True
    assert [llamada["name"] for llamada in llamadas] == DIMENSIONES
    assert all(llamada["trace_id"] == "traza-1" for llamada in llamadas)
    assert llamadas[0]["value"] == 8.0


def test_registrar_scores_sin_cliente_o_sin_traza():
    assert registrar_scores(None, "traza-1", EVALUACION) is False
    assert registrar_scores(SimpleNamespace(create_score=print), None, EVALUACION) is False


def test_registrar_scores_tolera_que_langfuse_falle(capsys):
    def explotar(**datos):
        raise ConnectionError("Langfuse caído")

    assert registrar_scores(SimpleNamespace(create_score=explotar), "t", EVALUACION) is False
    assert "Langfuse caído" in capsys.readouterr().err
