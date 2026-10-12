"""Comprueba que los archivos de entrega cumplan lo que pide la rúbrica."""
import re

from src.config import RAIZ

PAQUETES_EXIGIDOS = [
    "langchain", "langchain-openai", "langfuse", "openai", "langchain-chroma",
    "tiktoken", "python-dotenv", "jupyter", "ipykernel",
]


def nombres_en_requirements():
    nombres = []
    for linea in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#"):
            # Nos quedamos con lo que está antes de ==, >=, <, [, etc.
            nombres.append(re.split(r"[<>=~!\[; ]", linea)[0].lower())
    return nombres


def test_requirements_tiene_los_paquetes_exigidos():
    nombres = nombres_en_requirements()
    for paquete in PAQUETES_EXIGIDOS:
        assert paquete in nombres, f"Falta {paquete} en requirements.txt"
    assert len(nombres) >= 9


def test_env_example_tiene_las_cuatro_variables():
    texto = (RAIZ / ".env.example").read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=your-key-here" in texto
    assert "LANGFUSE_PUBLIC_KEY=pk-lf-xxx" in texto
    assert "LANGFUSE_SECRET_KEY=sk-lf-xxx" in texto
    assert "LANGFUSE_HOST=https://cloud.langfuse.com" in texto
