"""Tests de los agentes RAG con retriever y LLM falsos."""
from langchain_core.documents import Document
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.runnables import RunnableLambda

from src.agents.rag_base import MENSAJE_SIN_CONTEXTO, crear_agente_rag, extraer_fuentes

DOCUMENTOS = [
    Document(page_content="Viáticos: USD 60 por día.", metadata={"fuente": "viaticos.md", "seccion": "Montos"}),
    Document(page_content="Internacional: USD 90.", metadata={"fuente": "viaticos.md", "seccion": "Montos"}),
]


def test_responde_con_el_llm_y_cita_fuentes():
    agente = crear_agente_rag(
        "finance",
        RunnableLambda(lambda consulta: DOCUMENTOS),
        FakeListChatModel(responses=["Son USD 60 por día."]),
        "Eres el agente de Finanzas.",
    )
    salida = agente.invoke({"consulta": "¿viáticos?"})
    assert salida["departamento"] == "finance"
    assert salida["respuesta"] == "Son USD 60 por día."
    assert salida["fuentes"] == [{"archivo": "viaticos.md", "seccion": "Montos"}]
    assert "USD 60" in salida["contexto"]


def test_sin_documentos_no_llama_al_llm_ni_inventa():
    agente = crear_agente_rag(
        "tech",
        RunnableLambda(lambda consulta: []),
        FakeListChatModel(responses=["RESPUESTA INVENTADA"]),
        "Eres el agente de TI.",
    )
    salida = agente.invoke({"consulta": "¿algo?"})
    assert salida["respuesta"] == MENSAJE_SIN_CONTEXTO.format(departamento="tech")
    assert salida["fuentes"] == []


def test_extraer_fuentes_sin_duplicados():
    assert len(extraer_fuentes(DOCUMENTOS)) == 1


def test_prompts_de_agentes_sin_llaves():
    from src.config import leer_prompt
    for nombre in ["agente_hr.txt", "agente_tech.txt", "agente_finance.txt"]:
        texto = leer_prompt(nombre)
        assert "{" not in texto and "}" not in texto
