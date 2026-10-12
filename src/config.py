"""Configuración del proyecto: lee el .env y crea los objetos de OpenAI.

Orden de prioridad (igual que en proyecto_1 y proyecto_2):
    1. lo que llega por línea de comandos ("sobrescrituras"),
    2. las variables de entorno (archivo .env),
    3. los valores por defecto definidos aquí.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Carpeta raíz del proyecto (la que contiene src/, data/, prompts/...).
RAIZ = Path(__file__).resolve().parent.parent
RUTA_DATOS = RAIZ / "data"
RUTA_PROMPTS = RAIZ / "prompts"

# Los tres departamentos con agente RAG propio, más la ruta para lo que no es de nadie.
DEPARTAMENTOS = ["hr", "tech", "finance"]
FUERA_DE_DOMINIO = "fuera_de_dominio"

# La consigna exige al menos 50 chunks por departamento.
MINIMO_CHUNKS = 50

VALORES_POR_DEFECTO = {
    "modelo_chat": "gpt-6-luna",  # el modelo más barato: la potencia no es prioridad
    "modelo_embeddings": "text-embedding-3-small",
    # "none": el modelo no gasta tokens ocultos "pensando" (se cobran como salida).
    "esfuerzo_razonamiento": "none",
    "rag_k": "4",  # cuántos chunks recupera cada agente
    "ruta_chroma": str(RAIZ / "chroma_db"),
}

# Qué variable de entorno corresponde a cada opción.
VARIABLES_DE_ENTORNO = {
    "modelo_chat": "OPENAI_MODEL",
    "modelo_embeddings": "OPENAI_EMBEDDING_MODEL",
    "esfuerzo_razonamiento": "OPENAI_REASONING_EFFORT",
    "rag_k": "RAG_K",
    "ruta_chroma": "CHROMA_DIR",
}

CLAVE_DE_EJEMPLO = "your-key-here"


def cargar_config(sobrescrituras=None, usar_dotenv=True):
    """Devuelve un diccionario con toda la configuración del proyecto.

    sobrescrituras: dict con valores que llegan de la CLI; un valor None se ignora.
    usar_dotenv: False en los tests, para que el .env real no interfiera.
    """
    if usar_dotenv:
        load_dotenv(RAIZ / ".env")

    config = {}
    for opcion, valor_por_defecto in VALORES_POR_DEFECTO.items():
        config[opcion] = os.getenv(VARIABLES_DE_ENTORNO[opcion], valor_por_defecto)
    config["rag_k"] = int(config["rag_k"])

    # Claves: nunca se escriben en el código, solo se leen del entorno.
    config["openai_api_key"] = os.getenv("OPENAI_API_KEY", "")
    config["langfuse_public_key"] = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    config["langfuse_secret_key"] = os.getenv("LANGFUSE_SECRET_KEY", "")
    config["langfuse_host"] = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if sobrescrituras:
        for opcion, valor in sobrescrituras.items():
            if valor is not None:
                config[opcion] = valor
    return config


def exigir_clave_openai(config):
    """Falla con un mensaje claro si no hay clave de OpenAI."""
    clave = config["openai_api_key"]
    if not clave or clave == CLAVE_DE_EJEMPLO:
        raise ValueError(
            "Falta OPENAI_API_KEY: copia .env.example como .env y escribe tu clave."
        )


def crear_llm(config):
    """Crea el modelo de chat de OpenAI que usan orquestador, agentes y evaluador."""
    exigir_clave_openai(config)
    opciones = {
        "model": config["modelo_chat"],
        "api_key": config["openai_api_key"],
        "max_retries": 2,
        "timeout": 60,
    }
    # Solo pasamos el esfuerzo de razonamiento si está definido (vacío = no enviarlo).
    if config["esfuerzo_razonamiento"]:
        opciones["reasoning_effort"] = config["esfuerzo_razonamiento"]
    return ChatOpenAI(**opciones)


def crear_embeddings(config):
    """Crea el modelo que convierte textos en vectores (embeddings)."""
    exigir_clave_openai(config)
    return OpenAIEmbeddings(
        model=config["modelo_embeddings"], api_key=config["openai_api_key"]
    )


def leer_prompt(nombre):
    """Lee un prompt de la carpeta prompts/ (los prompts no viven en el código)."""
    return (RUTA_PROMPTS / nombre).read_text(encoding="utf-8")
