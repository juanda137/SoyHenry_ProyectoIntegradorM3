"""El notebook existe y tiene las 6 secciones que exige la consigna."""
import json

from src.config import RAIZ

SECCIONES = [
    "## 1. Setup e imports",
    "## 2. Carga de documentos y vector stores",
    "## 3. Definición de agentes",
    "## 4. Orquestador y enrutamiento",
    "## 5. Pruebas y ejemplos",
    "## 6. Integración con Langfuse",
]


def test_notebook_tiene_las_seis_secciones_en_orden():
    notebook = json.loads((RAIZ / "multi_agent_system.ipynb").read_text(encoding="utf-8"))
    markdown = "\n".join(
        "".join(celda["source"]) for celda in notebook["cells"] if celda["cell_type"] == "markdown"
    )
    posiciones = [markdown.index(seccion) for seccion in SECCIONES]
    assert posiciones == sorted(posiciones)


def test_notebook_importa_desde_src():
    texto = (RAIZ / "multi_agent_system.ipynb").read_text(encoding="utf-8")
    assert "from src." in texto
