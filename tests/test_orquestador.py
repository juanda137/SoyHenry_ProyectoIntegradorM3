"""Tests del orquestador con un LLM falso: no llaman a OpenAI."""
from types import SimpleNamespace

from langchain_core.runnables import RunnableLambda

from src.agents.orchestrator import Clasificacion, crear_orquestador


def llm_falso(funcion):
    """Imita un ChatOpenAI: with_structured_output devuelve un Runnable que llama a 'funcion'."""
    return SimpleNamespace(with_structured_output=lambda esquema: RunnableLambda(funcion))


def test_clasificacion_valida():
    llm = llm_falso(lambda prompt: Clasificacion(departamento="finance", confianza=0.9, razon="viáticos"))
    salida = crear_orquestador(llm).invoke({"consulta": "¿Cuánto son los viáticos?"})
    assert salida == {"departamento": "finance", "confianza": 0.9, "razon": "viáticos", "error": False}


def test_el_prompt_incluye_la_consulta():
    vistos = []

    def registrar(prompt):
        vistos.append(prompt.to_string())
        return Clasificacion(departamento="hr", confianza=1.0, razon="x")

    crear_orquestador(llm_falso(registrar)).invoke({"consulta": "mis vacaciones"})
    assert "mis vacaciones" in vistos[0]


def test_departamento_invalido_va_a_fuera_de_dominio():
    llm = llm_falso(lambda prompt: {"departamento": "ventas", "confianza": 0.8, "razon": "x"})
    salida = crear_orquestador(llm).invoke({"consulta": "hola"})
    assert salida["departamento"] == "fuera_de_dominio"
    assert salida["confianza"] == 0.0
    assert salida["error"] is True


def test_error_del_modelo_va_a_fuera_de_dominio():
    def explotar(prompt):
        raise RuntimeError("503 del proveedor")

    salida = crear_orquestador(llm_falso(explotar)).invoke({"consulta": "hola"})
    assert salida["departamento"] == "fuera_de_dominio"
    assert "503" in salida["razon"]


def test_respuesta_vacia_va_a_fuera_de_dominio():
    salida = crear_orquestador(llm_falso(lambda prompt: None)).invoke({"consulta": "hola"})
    assert salida["error"] is True
