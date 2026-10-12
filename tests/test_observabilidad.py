"""Sin claves de Langfuse el sistema debe seguir funcionando."""
from src.config import cargar_config
from src.observabilidad import crear_handler, langfuse_configurado, obtener_cliente_langfuse


def test_sin_claves_no_hay_handler_ni_cliente(monkeypatch, capsys):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    config = cargar_config(usar_dotenv=False)
    assert langfuse_configurado(config) is False
    assert crear_handler(config) is None
    assert obtener_cliente_langfuse(config) is None
    assert "Langfuse" in capsys.readouterr().err


def test_claves_de_ejemplo_cuentan_como_faltantes(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-xxx")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-xxx")
    assert langfuse_configurado(cargar_config(usar_dotenv=False)) is False
