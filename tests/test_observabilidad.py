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


def config_con_claves(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-real")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-real")
    return cargar_config(usar_dotenv=False)


def test_langfuse_caido_o_claves_rechazadas_desactiva_las_trazas(monkeypatch, capsys):
    from types import SimpleNamespace

    import src.observabilidad as observabilidad

    def caido():
        raise ConnectionError("host inalcanzable")

    monkeypatch.setattr(observabilidad, "Langfuse", lambda **datos: SimpleNamespace(auth_check=caido))
    assert observabilidad.obtener_cliente_langfuse(config_con_claves(monkeypatch)) is None
    assert "host inalcanzable" in capsys.readouterr().err


def test_langfuse_con_claves_validas_devuelve_el_cliente(monkeypatch):
    from types import SimpleNamespace

    import src.observabilidad as observabilidad

    cliente = SimpleNamespace(auth_check=lambda: True)
    monkeypatch.setattr(observabilidad, "Langfuse", lambda **datos: cliente)
    assert observabilidad.obtener_cliente_langfuse(config_con_claves(monkeypatch)) is cliente
