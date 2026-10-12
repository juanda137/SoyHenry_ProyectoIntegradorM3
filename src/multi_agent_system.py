"""Sistema multiagente: orquestador + enrutamiento condicional + agentes RAG.

Flujo (todo con LCEL, el "lenguaje de tuberías" de LangChain):
    consulta -> orquestador (clasifica) -> RunnableBranch (elige agente) -> respuesta
"""
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnablePassthrough

from src.agents.finance_agent import crear_finance_agent
from src.agents.hr_agent import crear_hr_agent
from src.agents.orchestrator import crear_orquestador
from src.agents.tech_agent import crear_tech_agent
from src.config import FUERA_DE_DOMINIO, crear_llm
from src.indexacion import indexar_todo

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
