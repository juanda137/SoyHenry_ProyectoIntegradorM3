"""Indexación: de los documentos .md de cada departamento a colecciones de Chroma.

Pasos de un RAG antes de poder responder:
    1. leer los documentos,
    2. dividirlos en chunks (trozos pequeños que caben en el prompt),
    3. convertir cada chunk en un vector (embedding) y guardarlo en Chroma.
"""
import argparse
import sys
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from src.config import DEPARTAMENTOS, MINIMO_CHUNKS, RUTA_DATOS, cargar_config, crear_embeddings

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


def obtener_vectorstore(departamento, config, embeddings=None):
    """Abre (o crea vacía) la colección de Chroma de un departamento.

    Chroma guarda los vectores en disco (config["ruta_chroma"]): los embeddings se
    pagan una sola vez y se reutilizan en las siguientes ejecuciones.
    """
    if embeddings is None:
        embeddings = crear_embeddings(config)
    return Chroma(
        # Chroma exige nombres de al menos 3 caracteres ("hr" no alcanza).
        collection_name=f"docs_{departamento}",
        embedding_function=embeddings,
        persist_directory=config["ruta_chroma"],
    )


def contar_chunks(vectorstore):
    """Cuántos chunks tiene guardados una colección."""
    return len(vectorstore.get(include=[])["ids"])


def indexar_todo(config, reconstruir=False, embeddings=None, carpeta_datos=RUTA_DATOS):
    """Indexa los tres departamentos. Solo embebe las colecciones vacías.

    Devuelve un diccionario {departamento: cantidad de chunks en Chroma}.
    """
    conteos = {}
    for departamento in DEPARTAMENTOS:
        chunks = dividir_documentos(departamento, carpeta_datos)
        if len(chunks) < MINIMO_CHUNKS:
            raise ValueError(
                f"{departamento} tiene {len(chunks)} chunks: menos de {MINIMO_CHUNKS}."
            )
        vectorstore = obtener_vectorstore(departamento, config, embeddings)
        if reconstruir:
            vectorstore.delete_collection()
            vectorstore = obtener_vectorstore(departamento, config, embeddings)
        if contar_chunks(vectorstore) == 0:
            # IDs fijos: si algo se repite, Chroma reemplaza en vez de duplicar.
            ids = [f"{departamento}-{numero}" for numero in range(len(chunks))]
            vectorstore.add_documents(chunks, ids=ids)
        conteos[departamento] = contar_chunks(vectorstore)
        print(f"[indexación] {departamento}: {conteos[departamento]} chunks", file=sys.stderr)
    return conteos


def main():
    parser = argparse.ArgumentParser(description="Indexa los documentos en Chroma.")
    parser.add_argument(
        "--reconstruir", action="store_true", help="borra y vuelve a crear los índices"
    )
    argumentos = parser.parse_args()
    indexar_todo(cargar_config(), reconstruir=argumentos.reconstruir)


if __name__ == "__main__":
    main()
