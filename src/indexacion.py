"""Indexación: de los documentos .md de cada departamento a colecciones de Chroma.

Pasos de un RAG antes de poder responder:
    1. leer los documentos,
    2. dividirlos en chunks (trozos pequeños que caben en el prompt),
    3. convertir cada chunk en un vector (embedding) y guardarlo en Chroma.
"""
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from src.config import RUTA_DATOS

TAMANO_CHUNK = 500  # caracteres por chunk
SOLAPAMIENTO = 50  # caracteres repetidos entre chunks vecinos, para no cortar ideas


def leer_documentos(departamento, carpeta_datos=RUTA_DATOS):
    """Lee los .md de data/<departamento>_docs/ como Documents de LangChain."""
    carpeta = Path(carpeta_datos) / f"{departamento}_docs"
    if not carpeta.is_dir():
        raise FileNotFoundError(f"No existe la carpeta de documentos {carpeta}")
    documentos = []
    for archivo in sorted(carpeta.glob("*.md")):
        texto = archivo.read_text(encoding="utf-8")  # utf-8: tildes y eñes en Windows
        documentos.append(
            Document(page_content=texto, metadata={"fuente": archivo.name})
        )
    return documentos


def dividir_documentos(departamento, carpeta_datos=RUTA_DATOS):
    """Divide los documentos en chunks de hasta 500 caracteres con su metadata."""
    # 1) Primero por títulos: así cada trozo "sabe" a qué sección pertenece.
    por_titulos = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "titulo"), ("##", "seccion")],
        strip_headers=False,
    )
    # 2) Después por tamaño, para que ningún chunk supere TAMANO_CHUNK.
    por_tamano = RecursiveCharacterTextSplitter(
        chunk_size=TAMANO_CHUNK, chunk_overlap=SOLAPAMIENTO
    )
    chunks = []
    for documento in leer_documentos(departamento, carpeta_datos):
        secciones = por_titulos.split_text(documento.page_content)
        for trozo in por_tamano.split_documents(secciones):
            seccion = trozo.metadata.get("seccion") or trozo.metadata.get("titulo", "")
            trozo.metadata = {
                "fuente": documento.metadata["fuente"],
                "seccion": seccion,
                "departamento": departamento,
            }
            chunks.append(trozo)
    return chunks
