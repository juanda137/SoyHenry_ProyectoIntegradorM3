"""Fábrica de agentes RAG: los tres departamentos comparten esta misma lógica.

RAG = Retrieval-Augmented Generation:
    1. Retrieval: buscar en Chroma los chunks más parecidos a la consulta.
    2. Augmented: pegar esos chunks en el prompt como "contexto".
    3. Generation: el modelo responde usando SOLO ese contexto (menos alucinaciones).
"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

MENSAJE_SIN_CONTEXTO = "No encontré esa información en la documentación de {departamento}."


def formatear_contexto(documentos):
    """Une los chunks en un texto numerado que se pega en el prompt."""
    partes = []
    for numero, documento in enumerate(documentos, start=1):
        fuente = documento.metadata.get("fuente", "?")
        seccion = documento.metadata.get("seccion", "")
        partes.append(f"[{numero}] {fuente} - {seccion}\n{documento.page_content}")
    return "\n\n".join(partes)


def extraer_fuentes(documentos):
    """Lista de fuentes (archivo + sección) sin repetir, para citar en la respuesta."""
    fuentes = []
    for documento in documentos:
        fuente = {
            "archivo": documento.metadata.get("fuente", ""),
            "seccion": documento.metadata.get("seccion", ""),
        }
        if fuente not in fuentes:
            fuentes.append(fuente)
    return fuentes


def crear_agente_rag(departamento, retriever, llm, prompt_sistema):
    """Devuelve un Runnable: {"consulta": ...} -> respuesta con fuentes."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_sistema),
            ("human", "Contexto de la documentación:\n{contexto}\n\nPregunta: {consulta}"),
        ]
    )
    generar = prompt | llm | StrOutputParser()

    def responder_con_rag(entrada, config):
        consulta = entrada["consulta"]
        documentos = retriever.invoke(consulta, config=config)
        contexto = formatear_contexto(documentos)
        if documentos:
            respuesta = generar.invoke({"contexto": contexto, "consulta": consulta}, config=config)
        else:
            # Sin evidencia no le preguntamos al modelo: así no puede inventar.
            respuesta = MENSAJE_SIN_CONTEXTO.format(departamento=departamento)
        return {
            "departamento": departamento,
            "respuesta": respuesta,
            "fuentes": extraer_fuentes(documentos),
            "contexto": contexto,
        }

    return RunnableLambda(responder_con_rag, name=f"agente_{departamento}")
