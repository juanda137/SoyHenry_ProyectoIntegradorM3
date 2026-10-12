"""El archivo de test queries cumple lo que pide la consigna."""
import json

from src.config import RAIZ

CAMPOS = {"id", "consulta", "departamento_esperado", "tipo"}


def cargar():
    return json.loads((RAIZ / "test_queries.json").read_text(encoding="utf-8"))


def test_al_menos_10_consultas_con_todos_los_campos():
    consultas = cargar()
    assert len(consultas) >= 10
    for consulta in consultas:
        assert set(consulta) == CAMPOS


def test_cubre_todos_los_departamentos_y_casos_borde():
    consultas = cargar()
    esperados = {consulta["departamento_esperado"] for consulta in consultas}
    assert esperados == {"hr", "tech", "finance", "fuera_de_dominio"}
    tipos = {consulta["tipo"] for consulta in consultas}
    assert {"clara", "fronteriza", "fuera_de_dominio", "ambigua"} <= tipos


def test_ids_unicos():
    ids = [consulta["id"] for consulta in cargar()]
    assert len(ids) == len(set(ids))
