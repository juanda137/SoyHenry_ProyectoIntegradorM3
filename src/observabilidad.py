"""Observabilidad con Langfuse: cada consulta queda registrada como una traza.

Una traza muestra todo el camino de una consulta (clasificación, chunks recuperados,
generación, evaluación) para depurar respuestas mal enrutadas o incorrectas.
"""
import sys

from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

CLAVES_DE_EJEMPLO = ["pk-lf-xxx", "sk-lf-xxx"]


def langfuse_configurado(config):
    """True si hay claves reales de Langfuse (no las del .env.example)."""
    publica = config["langfuse_public_key"]
    secreta = config["langfuse_secret_key"]
    if not publica or not secreta:
        return False
    return publica not in CLAVES_DE_EJEMPLO and secreta not in CLAVES_DE_EJEMPLO


def obtener_cliente_langfuse(config):
    """Cliente de Langfuse, o None (con aviso) si no está configurado."""
    if not langfuse_configurado(config):
        print(
            "[aviso] Langfuse no está configurado: el sistema funciona, pero sin trazas.",
            file=sys.stderr,
        )
        return None
    return Langfuse(
        public_key=config["langfuse_public_key"],
        secret_key=config["langfuse_secret_key"],
        host=config["langfuse_host"],
    )


def crear_handler(config):
    """CallbackHandler: LangChain le avisa de cada paso y él lo envía a Langfuse."""
    if not langfuse_configurado(config):
        return None
    return CallbackHandler(public_key=config["langfuse_public_key"])
