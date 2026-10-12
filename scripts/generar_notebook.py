"""Genera multi_agent_system.ipynb a partir de las celdas definidas aquí.

Uso: python scripts/generar_notebook.py
El notebook se genera SIN outputs; después se ejecuta para guardar resultados reales.
"""
from pathlib import Path

import nbformat

RAIZ = Path(__file__).resolve().parent.parent

CELDAS = [
    ("md", "# Sistema multiagente de soporte con RAG y Langfuse\n\n"
           "Un **Agente Orquestador** clasifica cada consulta (HR, Tech, Finance o fuera de dominio) "
           "y la delega con enrutamiento condicional a un **Agente RAG** especializado. "
           "Todo el flujo está trazado en **Langfuse** y un **Agente Evaluador** puntúa cada respuesta.\n\n"
           "El código vive en `src/`; este notebook lo importa y lo explica paso a paso. "
           "Ejecuta las celdas **en orden**."),
    ("md", "## 1. Setup e imports\n\nCargamos la configuración desde `.env`. "
           "Mostramos solo si cada clave está presente, nunca su valor."),
    ("code", "from src.config import cargar_config, crear_llm, DEPARTAMENTOS\n"
             "from src.indexacion import dividir_documentos, indexar_todo\n"
             "from src.agents.orchestrator import crear_orquestador\n"
             "from src.agents.hr_agent import crear_hr_agent\n"
             "from src.agents.tech_agent import crear_tech_agent\n"
             "from src.agents.finance_agent import crear_finance_agent\n"
             "from src.multi_agent_system import crear_sistema, responder, medir_test_queries\n"
             "from src.observabilidad import langfuse_configurado\n\n"
             "config = cargar_config()\n"
             "print('Modelo de chat:', config['modelo_chat'])\n"
             "print('Modelo de embeddings:', config['modelo_embeddings'])\n"
             "print('Clave de OpenAI presente:', bool(config['openai_api_key']))\n"
             "print('Langfuse configurado:', langfuse_configurado(config))"),
    ("md", "## 2. Carga de documentos y vector stores\n\n"
           "Cada departamento tiene su carpeta en `data/` y su propia colección en Chroma. "
           "Los documentos se dividen primero por títulos y luego en chunks de 500 caracteres."),
    ("code", "for departamento in DEPARTAMENTOS:\n"
             "    chunks = dividir_documentos(departamento)\n"
             "    print(f'{departamento}: {len(chunks)} chunks')\n\n"
             "ejemplo = dividir_documentos('finance')[0]\n"
             "print('\\nEjemplo de chunk:', ejemplo.metadata)\n"
             "print(ejemplo.page_content[:300])"),
    ("code", "# Crea los embeddings solo si las colecciones están vacías (la primera vez).\n"
             "conteos = indexar_todo(config)\n"
             "conteos"),
    ("md", "## 3. Definición de agentes\n\n"
           "Los tres agentes comparten la misma fábrica (`crear_agente_rag`): retriever de su colección "
           "+ prompt de rol + modelo. Probamos uno directamente, sin orquestador."),
    ("code", "agentes = {\n"
             "    'hr': crear_hr_agent(config),\n"
             "    'tech': crear_tech_agent(config),\n"
             "    'finance': crear_finance_agent(config),\n"
             "}\n"
             "salida = agentes['hr'].invoke({'consulta': '¿Cuántos días de vacaciones tengo el primer año?'})\n"
             "print(salida['respuesta'])\n"
             "print('Fuentes:', salida['fuentes'])"),
    ("md", "## 4. Orquestador y enrutamiento\n\n"
           "El orquestador devuelve una clasificación estructurada. `RunnableBranch` usa ese "
           "departamento para elegir el agente; lo que no es de nadie va a `fuera_de_dominio`."),
    ("code", "orquestador = crear_orquestador(crear_llm(config))\n"
             "for consulta in ['Me bloquearon la cuenta', '¿Cuánto son los viáticos nacionales?', 'Escríbeme un poema']:\n"
             "    print(consulta, '->', orquestador.invoke({'consulta': consulta}))\n\n"
             "sistema = crear_sistema(config, orquestador=orquestador, agentes=agentes)"),
    ("md", "## 5. Pruebas y ejemplos\n\n"
           "Primero tres consultas sueltas (sin evaluador) y después las 15 test queries de "
           "`test_queries.json` para medir el acierto de enrutamiento."),
    ("code", "for consulta in ['¿Cómo me reintegran el internet del home office?',\n"
             "                 'Empiezo el lunes, ¿cuándo me entregan la laptop?',\n"
             "                 '¿Qué tiempo hará mañana?']:\n"
             "    salida = responder(consulta, config, sistema=sistema, con_evaluador=False)\n"
             "    print(f\"[{salida['departamento']}] {consulta}\\n  {salida['respuesta']}\\n\")"),
    ("code", "metricas = medir_test_queries(config, 'test_queries.json',\n"
             "                              'outputs/resultados_notebook.json', con_evaluador=False)"),
    ("md", "## 6. Integración con Langfuse\n\n"
           "`responder()` abre un span en Langfuse y pasa el `CallbackHandler` a LangChain: cada consulta "
           "queda como **una traza** con la clasificación, los chunks recuperados y la generación. "
           "Con el `trace_id` se abre la traza en la interfaz de Langfuse para depurar."),
    ("md", "### Agente Evaluador (bonus)\n\n"
           "Un LLM-juez puntúa relevance, completeness, accuracy y overall (1 a 10). "
           "Los cuatro puntajes se registran en la misma traza con la Score API de Langfuse."),
    ("code", "salida = responder('Hice un curso de capacitación, ¿cómo presento la factura?', config, sistema=sistema)\n"
             "print('Departamento:', salida['departamento'])\n"
             "print('Respuesta:', salida['respuesta'])\n"
             "print('Trace ID:', salida['trace_id'])\n"
             "print('Evaluación:', salida['evaluacion'])"),
]


def main():
    notebook = nbformat.v4.new_notebook()
    for tipo, texto in CELDAS:
        if tipo == "md":
            notebook.cells.append(nbformat.v4.new_markdown_cell(texto))
        else:
            notebook.cells.append(nbformat.v4.new_code_cell(texto))
    notebook.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nbformat.write(notebook, RAIZ / "multi_agent_system.ipynb")
    print("Notebook generado: multi_agent_system.ipynb")


if __name__ == "__main__":
    main()
