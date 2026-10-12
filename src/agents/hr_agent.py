"""Agente RAG de Recursos Humanos: busca solo en la colección 'hr' de Chroma."""
from src.agents.rag_base import crear_agente_rag
from src.config import crear_llm, leer_prompt
from src.indexacion import obtener_vectorstore


def crear_hr_agent(config):
    vectorstore = obtener_vectorstore("hr", config)
    # k = cuántos chunks se recuperan por consulta.
    retriever = vectorstore.as_retriever(search_kwargs={"k": config["rag_k"]})
    return crear_agente_rag("hr", retriever, crear_llm(config), leer_prompt("agente_hr.txt"))
