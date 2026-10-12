"""Tests de la configuración. No llaman a ninguna API."""
import pytest

from src.config import DEPARTAMENTOS, cargar_config, crear_llm, leer_prompt


def test_valores_por_defecto(monkeypatch):
    # Borramos las variables para ver los valores por defecto.
    for variable in ["OPENAI_MODEL", "RAG_K", "OPENAI_REASONING_EFFORT"]:
        monkeypatch.delenv(variable, raising=False)
    config = cargar_config(usar_dotenv=False)
    assert config["modelo_chat"] == "gpt-6-luna"
    assert config["esfuerzo_razonamiento"] == "none"
    assert config["rag_k"] == 4


def test_variable_de_entorno_gana_al_default(monkeypatch):
    monkeypatch.setenv("RAG_K", "7")
    assert cargar_config(usar_dotenv=False)["rag_k"] == 7


def test_sobrescritura_gana_a_la_variable(monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "modelo-del-env")
    config = cargar_config({"modelo_chat": "modelo-cli", "rag_k": None}, usar_dotenv=False)
    assert config["modelo_chat"] == "modelo-cli"
    assert config["rag_k"] == 4  # None significa "no sobrescribir"


def test_crear_llm_sin_clave_falla_con_mensaje_claro(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = cargar_config(usar_dotenv=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        crear_llm(config)


def test_clave_de_ejemplo_cuenta_como_faltante(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "your-key-here")
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        crear_llm(cargar_config(usar_dotenv=False))


def test_departamentos():
    assert DEPARTAMENTOS == ["hr", "tech", "finance"]


def test_leer_prompt_inexistente_falla():
    with pytest.raises(FileNotFoundError):
        leer_prompt("no_existe.txt")
