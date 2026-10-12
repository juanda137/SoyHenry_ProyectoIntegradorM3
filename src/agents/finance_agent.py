"""Agente RAG de Finanzas: busca solo en la colección 'finance' de Chroma."""
from src.agents.rag_base import crear_agente_rag
from src.config import crear_llm, leer_prompt
from src.indexacion import obtener_vectorstore


def crear_finance_agent(config):
    vectorstore = obtener_vectorstore("finance", config)
    # k = cuántos chunks se recuperan por consulta.
    retriever = vectorstore.as_retriever(search_kwargs={"k": config["rag_k"]})
    return crear_agente_rag("finance", retriever, crear_llm(config), leer_prompt("agente_finance.txt"))
