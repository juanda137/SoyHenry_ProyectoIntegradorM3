"""Tests del chunking. No generan embeddings ni llaman a la red."""
import pytest

from src.config import DEPARTAMENTOS, MINIMO_CHUNKS
from src.indexacion import dividir_documentos


@pytest.mark.parametrize("departamento", DEPARTAMENTOS)
def test_cada_departamento_tiene_al_menos_50_chunks(departamento):
    chunks = dividir_documentos(departamento)
    assert len(chunks) >= MINIMO_CHUNKS


@pytest.mark.parametrize("departamento", DEPARTAMENTOS)
def test_metadata_de_los_chunks(departamento):
    for chunk in dividir_documentos(departamento):
        assert chunk.metadata["departamento"] == departamento
        assert chunk.metadata["fuente"].endswith(".md")
        assert "seccion" in chunk.metadata
        assert len(chunk.page_content) <= 500


def test_respeta_tildes_y_enies(tmp_path):
    carpeta = tmp_path / "hr_docs"
    carpeta.mkdir()
    texto = "# Política\n\n## Año de servicio\n\nLa compañía otorga días según antigüedad."
    (carpeta / "prueba.md").write_text(texto, encoding="utf-8")
    chunks = dividir_documentos("hr", carpeta_datos=tmp_path)
    assert "antigüedad" in chunks[0].page_content
    assert chunks[0].metadata["seccion"] == "Año de servicio"


def test_carpeta_inexistente_falla_con_mensaje(tmp_path):
    with pytest.raises(FileNotFoundError, match="hr_docs"):
        dividir_documentos("hr", carpeta_datos=tmp_path)
