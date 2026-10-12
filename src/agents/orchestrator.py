"""Agente Orquestador: clasifica la intención de la consulta por departamento.

Usa "structured output": le pedimos al modelo que responda con un objeto que respeta
un esquema (la clase Clasificacion), en vez de texto libre. Así el enrutamiento no
depende de interpretar frases del modelo.
"""
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field

from src.config import FUERA_DE_DOMINIO, leer_prompt


class Clasificacion(BaseModel):
    """Esquema que el modelo debe completar (Pydantic valida los valores)."""

    departamento: Literal["hr", "tech", "finance", "fuera_de_dominio"] = Field(
        description="Departamento al que corresponde la consulta"
    )
    confianza: float = Field(ge=0, le=1, description="Seguridad de 0 a 1")
    razon: str = Field(description="Frase corta que justifica la elección")


def clasificacion_de_emergencia(motivo):
    """Clasificación segura cuando el modelo falla: mejor no responder que enrutar mal."""
    return {
        "departamento": FUERA_DE_DOMINIO,
        "confianza": 0.0,
        "razon": f"Error al clasificar: {motivo}",
        "error": True,
    }


def crear_orquestador(llm):
    """Devuelve un Runnable: {"consulta": ...} -> diccionario de clasificación."""
    prompt = ChatPromptTemplate.from_messages(
        [("system", leer_prompt("orquestador.txt")), ("human", "{consulta}")]
    )
    cadena = prompt | llm.with_structured_output(Clasificacion)

    # 'config' lo pasa LangChain: lleva los callbacks (Langfuse) a la llamada interna.
    def clasificar(entrada, config):
        try:
            resultado = cadena.invoke({"consulta": entrada["consulta"]}, config=config)
            # model_validate revisa el resultado aunque llegue como dict o como None.
            datos = Clasificacion.model_validate(resultado).model_dump()
        except Exception as error:
            return clasificacion_de_emergencia(str(error))
        datos["error"] = False
        return datos

    return RunnableLambda(clasificar, name="orquestador")
