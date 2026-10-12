"""Tests del enrutamiento con orquestador y agentes falsos."""
import pytest
from langchain_core.runnables import RunnableLambda

from src.config import cargar_config
from src.multi_agent_system import MENSAJE_FUERA_DE_DOMINIO, crear_sistema


def orquestador_fijo(departamento):
    return RunnableLambda(
        lambda entrada: {"departamento": departamento, "confianza": 0.9, "razon": "test", "error": False}
    )


def agente_falso(nombre):
    return RunnableLambda(
        lambda entrada: {"departamento": nombre, "respuesta": f"respuesta de {nombre}", "fuentes": [], "contexto": "c"}
    )


AGENTES = {"hr": agente_falso("hr"), "tech": agente_falso("tech"), "finance": agente_falso("finance")}


@pytest.mark.parametrize("departamento", ["hr", "tech", "finance"])
def test_enruta_al_agente_correcto(departamento):
    config = cargar_config(usar_dotenv=False)
    sistema = crear_sistema(config, orquestador=orquestador_fijo(departamento), agentes=AGENTES)
    salida = sistema.invoke({"consulta": "algo"})
    assert salida["resultado"]["respuesta"] == f"respuesta de {departamento}"
    assert salida["clasificacion"]["departamento"] == departamento
    assert salida["consulta"] == "algo"


def test_fuera_de_dominio_responde_mensaje_fijo():
    config = cargar_config(usar_dotenv=False)
    sistema = crear_sistema(config, orquestador=orquestador_fijo("fuera_de_dominio"), agentes=AGENTES)
    salida = sistema.invoke({"consulta": "un poema"})
    assert salida["resultado"]["respuesta"] == MENSAJE_FUERA_DE_DOMINIO
    assert salida["resultado"]["departamento"] == "fuera_de_dominio"
    assert salida["resultado"]["fuentes"] == []


def test_si_el_agente_falla_se_conserva_la_clasificacion():
    def explotar(entrada):
        raise RuntimeError("timeout de OpenAI")

    agentes = {**AGENTES, "hr": RunnableLambda(explotar)}
    config = cargar_config(usar_dotenv=False)
    sistema = crear_sistema(config, orquestador=orquestador_fijo("hr"), agentes=agentes)
    salida = sistema.invoke({"consulta": "vacaciones"})
    assert salida["clasificacion"]["departamento"] == "hr"
    assert salida["resultado"]["departamento"] == "hr"
    assert salida["resultado"]["respuesta"] is None
    assert "timeout de OpenAI" in salida["resultado"]["error"]
