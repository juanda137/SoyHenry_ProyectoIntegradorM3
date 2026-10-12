"""Agente RAG de Soporte de TI: busca solo en la colección 'tech' de Chroma."""
from src.agents.rag_base import crear_agente_rag
from src.config import crear_llm, leer_prompt
from src.indexacion import obtener_vectorstore


def crear_tech_agent(config):
    vectorstore = obtener_vectorstore("tech", config)
    # k = cuántos chunks se recuperan por consulta.
    retriever = vectorstore.as_retriever(search_kwargs={"k": config["rag_k"]})
    return crear_agente_rag("tech", retriever, crear_llm(config), leer_prompt("agente_tech.txt"))
