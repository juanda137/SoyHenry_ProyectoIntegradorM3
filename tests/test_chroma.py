"""Tests de Chroma con embeddings falsos: no llaman a OpenAI."""
import pytest
from langchain_core.embeddings import FakeEmbeddings

from src.config import cargar_config
from src.indexacion import contar_chunks, dividir_documentos, indexar_todo, obtener_vectorstore


@pytest.fixture
def config(tmp_path):
    return cargar_config({"ruta_chroma": str(tmp_path / "chroma")}, usar_dotenv=False)


def test_indexar_crea_las_tres_colecciones(config):
    falsos = FakeEmbeddings(size=16)
    conteos = indexar_todo(config, embeddings=falsos)
    for departamento in ["hr", "tech", "finance"]:
        assert conteos[departamento] == len(dividir_documentos(departamento))


def test_segunda_ejecucion_no_duplica(config):
    falsos = FakeEmbeddings(size=16)
    primera = indexar_todo(config, embeddings=falsos)
    segunda = indexar_todo(config, embeddings=falsos)
    assert primera == segunda


def test_indice_parcial_solo_completa_lo_que_falta(config):
    falsos = FakeEmbeddings(size=16)
    indexar_todo(config, embeddings=falsos)
    # Simulamos que la colección de finance se perdió.
    obtener_vectorstore("finance", config, embeddings=falsos).delete_collection()
    conteos = indexar_todo(config, embeddings=falsos)
    assert conteos["finance"] == len(dividir_documentos("finance"))
    assert conteos["hr"] == len(dividir_documentos("hr"))


def test_reconstruir_vuelve_a_crear(config):
    falsos = FakeEmbeddings(size=16)
    indexar_todo(config, embeddings=falsos)
    conteos = indexar_todo(config, reconstruir=True, embeddings=falsos)
    assert conteos["tech"] == len(dividir_documentos("tech"))
    assert contar_chunks(obtener_vectorstore("tech", config, embeddings=falsos)) == conteos["tech"]


def test_falla_si_un_departamento_tiene_menos_de_50_chunks(config, tmp_path):
    for departamento in ["hr", "tech", "finance"]:
        carpeta = tmp_path / f"{departamento}_docs"
        carpeta.mkdir()
        (carpeta / "corto.md").write_text("# Corto\n\nPoco texto.", encoding="utf-8")
    with pytest.raises(ValueError, match="menos de 50"):
        indexar_todo(config, embeddings=FakeEmbeddings(size=16), carpeta_datos=tmp_path)


def test_los_avisos_de_indexacion_van_a_stderr(config, capsys):
    # stdout queda libre para el JSON de la respuesta (la CLI se puede encadenar).
    indexar_todo(config, embeddings=FakeEmbeddings(size=16))
    salida = capsys.readouterr()
    assert salida.out == ""
    assert "[indexación] hr" in salida.err
