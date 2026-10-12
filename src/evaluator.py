"""Agente Evaluador (bonus): un LLM-juez puntúa cada respuesta RAG de 1 a 10.

Los puntajes se guardan en Langfuse con la Score API, sobre la misma traza de la
consulta: así se ven junto al camino que produjo la respuesta.
"""
import sys

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.config import leer_prompt

DIMENSIONES = ["relevance", "completeness", "accuracy", "overall"]


class Evaluacion(BaseModel):
    """Esquema que completa el juez. Field(ge=1, le=10) rechaza valores fuera de rango."""

    relevance: int = Field(ge=1, le=10, description="Responde lo que se preguntó")
    completeness: int = Field(ge=1, le=10, description="Incluye todos los datos necesarios")
    accuracy: int = Field(ge=1, le=10, description="Todo está respaldado por el contexto")
    overall: int = Field(ge=1, le=10, description="Calidad global")
    razon: str = Field(description="Motivo principal de los puntajes")


def validar_evaluacion(datos):
    """Valida (en Python, sin confiar en el modelo) y devuelve un diccionario."""
    return Evaluacion.model_validate(datos).model_dump()


def evaluar(consulta, respuesta, contexto, llm, config=None):
    """Pide al juez los 4 puntajes de una respuesta."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", leer_prompt("evaluador.txt")),
            (
                "human",
                "Consulta original:\n{consulta}\n\nContexto recuperado:\n{contexto}"
                "\n\nRespuesta final:\n{respuesta}",
            ),
        ]
    )
    juez = (prompt | llm.with_structured_output(Evaluacion)).with_config(
        run_name="agente_evaluador"
    )
    resultado = juez.invoke(
        {"consulta": consulta, "respuesta": respuesta, "contexto": contexto}, config=config
    )
    return validar_evaluacion(resultado)


def registrar_scores(cliente, trace_id, evaluacion):
    """Envía los 4 puntajes a Langfuse. Devuelve True si se pudieron registrar."""
    if cliente is None or trace_id is None:
        return False
    try:
        for dimension in DIMENSIONES:
            cliente.create_score(
                trace_id=trace_id,
                name=dimension,
                value=float(evaluacion[dimension]),
                data_type="NUMERIC",
                comment=evaluacion["razon"],
            )
    except Exception as error:
        # Si Langfuse falla, el usuario igual recibe su respuesta.
        print(f"[aviso] No se pudieron registrar los scores: {error}", file=sys.stderr)
        return False
    return True
