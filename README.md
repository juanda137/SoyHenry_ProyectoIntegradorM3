# Sistema multiagente de soporte con RAG y Langfuse

Proyecto del Módulo 3 de AI Engineering (SoyHenry).

## 1. Descripción

En una empresa SaaS mediana, la mesa de soporte interna recibe consultas de áreas muy distintas: Recursos Humanos, Soporte de TI y Finanzas. Muchas llegan al equipo equivocado: preguntas de vacaciones terminan en TI, reintegros de gastos llegan a HR, etc.

Este proyecto resuelve ese problema con un **sistema multiagente**:

1. Un **Agente Orquestador** lee la consulta y clasifica su intención en `hr`, `tech`, `finance` o `fuera_de_dominio`.
2. Un **enrutamiento condicional** (`RunnableBranch` de LangChain) delega la consulta al **Agente RAG** del departamento correcto.
3. Cada agente RAG busca en **su propia colección** de documentos (Chroma) y responde usando **solo** esa documentación, citando las fuentes.
4. Todo el recorrido queda registrado en **Langfuse** como una traza, para depurar consultas mal enrutadas o respuestas incorrectas.
5. (Bonus) Un **Agente Evaluador** puntúa cada respuesta de 1 a 10 en relevance, completeness, accuracy y overall, y guarda los puntajes en la misma traza con la Score API de Langfuse.

La empresa del caso es **NubeGestor**, un SaaS ficticio de gestión de proyectos para pymes de Latinoamérica. Toda su documentación interna (en `data/`) es inventada para este proyecto.

```
consulta del usuario
   │
   ▼
[Orquestador]  ChatOpenAI.with_structured_output(Clasificacion)
   │           → {departamento: hr|tech|finance|fuera_de_dominio, confianza: 0–1, razon}
   ▼
RunnableBranch ──► hr_agent ─────┐
               ├─► tech_agent ───┤  retriever Chroma (k=4) + prompt de rol
               ├─► finance_agent ┤  "responde SOLO con el contexto; si no está, dilo"
               └─► respuesta_fuera_de_dominio (sin LLM, mensaje fijo)
                                 ▼
                 {consulta, departamento, confianza, respuesta, fuentes}
                                 │
                                 ▼
          [Evaluador] LLM-juez → relevance, completeness, accuracy, overall (1–10) + razon
                                 │
                                 ▼
                   Score API de Langfuse → 4 scores sobre la misma traza
```

## 2. Estructura del repositorio

| Ruta | Qué contiene |
|---|---|
| `multi_agent_system.ipynb` | Notebook principal, en 6 secciones; importa el código de `src/` |
| `src/config.py` | Configuración (`.env`), creación del modelo de chat y de embeddings |
| `src/indexacion.py` | Lectura de documentos, chunking y colecciones de Chroma |
| `src/agents/orchestrator.py` | Agente Orquestador (clasificación con structured output) |
| `src/agents/rag_base.py` | Lógica común de los agentes RAG |
| `src/agents/hr_agent.py`, `tech_agent.py`, `finance_agent.py` | Un agente RAG por departamento |
| `src/multi_agent_system.py` | Ensamblado con `RunnableBranch`, `responder()`, medición y CLI |
| `src/observabilidad.py` | Cliente y `CallbackHandler` de Langfuse |
| `src/evaluator.py` | Agente Evaluador y registro de scores (bonus) |
| `prompts/` | Los prompts en `.txt`, separados del código |
| `data/hr_docs/`, `data/tech_docs/`, `data/finance_docs/` | Base de conocimiento de cada agente (5 documentos `.md` por departamento) |
| `test_queries.json` | 15 consultas de prueba con el departamento esperado |
| `outputs/` | Resultados medidos de las test queries |
| `scripts/generar_notebook.py` | Regenera el notebook (sin outputs) |
| `tests/` | Tests offline (no gastan API) |

## 3. Instalación

Requiere Python 3.11 o superior (probado con Python 3.14).

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## 4. Configurar las API keys

Copia `.env.example` como `.env` y completa las claves:

```dotenv
OPENAI_API_KEY=your-key-here
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

- **OpenAI**: crea una clave en platform.openai.com > API keys. Es obligatoria.
- **Langfuse**: crea una cuenta gratuita en cloud.langfuse.com, crea un proyecto y copia las claves desde Settings > API Keys. Si tu proyecto está en la región de Estados Unidos, usa `LANGFUSE_HOST=https://us.cloud.langfuse.com`.

Sin las claves de Langfuse el sistema **funciona igual**, pero sin trazas ni scores: lo avisa por consola.

El `.env` está en `.gitignore`: nunca lo subas al repositorio.

## 5. Cómo ejecutar el notebook

1. Abre `multi_agent_system.ipynb` en VS Code o Jupyter (`jupyter notebook`).
2. Elige el kernel del entorno virtual `.venv`.
3. Ejecuta las celdas **en orden, de la sección 1 a la 6**:
   1. **Setup e imports**: carga la configuración y confirma que las claves estén presentes.
   2. **Carga de documentos y vector stores**: muestra los chunks por departamento y crea las colecciones de Chroma. La primera vez genera los embeddings (unos centavos de dólar); las siguientes veces reutiliza el índice guardado en `chroma_db/`.
   3. **Definición de agentes**: crea los tres agentes RAG y prueba uno directamente.
   4. **Orquestador y enrutamiento**: clasifica consultas de ejemplo y arma el sistema completo.
   5. **Pruebas y ejemplos**: responde consultas sueltas y mide el acierto de enrutamiento sobre las 15 test queries.
   6. **Integración con Langfuse**: responde una consulta con trazas y con el Agente Evaluador, y muestra el `trace_id` y los scores.

## 6. Ejemplos de uso

Desde el notebook:

- Para hacer una pregunta: la celda de la sección 5 con `responder(...)`.
- Para ver la clasificación sin responder: la celda de la sección 4.
- Para ver los scores del evaluador: la celda de la sección 6.

Desde la terminal (con el entorno activado):

```bash
python -m src.indexacion                     # crea los índices (solo la primera vez)
python -m src.indexacion --reconstruir       # los borra y los vuelve a crear
python -m src.multi_agent_system "¿Cuántos días de vacaciones tengo en mi primer año?"
python -m src.multi_agent_system "no puedo entrar" --sin-evaluador
python -m src.multi_agent_system --evaluar-queries    # corre las 15 test queries
python -m src.multi_agent_system "..." --model gpt-6-luna --k 6
```

La respuesta es un JSON con `consulta`, `departamento`, `confianza`, `razon`, `respuesta`, `fuentes`, `error_clasificacion`, `etapa_error` (`clasificacion`, `respuesta` o `null`), `error`, `respuesta_completada`, `trace_id` y `evaluacion`. Si el agente falla después de clasificar, la respuesta igual llega, con `respuesta: null` y el error, sin perder el departamento elegido.

## 7. Observabilidad con Langfuse

Cada llamada a `responder()` abre un span raíz (`consulta_soporte`) y le pasa el `CallbackHandler` de Langfuse a LangChain. Así, **una consulta produce una sola traza**, que contiene:

- el span del **orquestador**, con el prompt y la clasificación devuelta;
- el span del **retriever**, con los chunks recuperados de Chroma;
- la **generación** del agente RAG;
- la llamada del **Agente Evaluador** y sus **4 scores** (pestaña Scores).

Cada traza lleva como **tag** el departamento elegido y como **metadata** la confianza, la razón y si hubo error de clasificación. En Langfuse se puede filtrar, por ejemplo, por tag `finance` o por confianza baja para encontrar consultas mal enrutadas. La CLI con `--evaluar-queries` lista las consultas mal enrutadas con su `trace_id` para abrirlas directamente.

## 8. Resultados medidos

Ejecución real del 12/10/2026 con `gpt-6-luna`, `text-embedding-3-small` y Langfuse Cloud (`python -m src.multi_agent_system --evaluar-queries`). Detalle completo en `outputs/resultados_test_queries.json`.

| Métrica | Primera medición | Después del ajuste del prompt |
|---|---|---|
| Clasificaciones válidas (cobertura) | 15/15 (100 %) | 15/15 (100 %) |
| Acierto de clasificación | 14/15 (93,3 %) | **15/15 (100 %)** |
| hr / tech / finance / fuera de dominio | 3/3 · 4/5 · 5/5 · 2/2 | 3/3 · 5/5 · 5/5 · 2/2 |
| Errores técnicos | ninguno | ninguno |
| Respuestas completadas | 15/15 | 15/15 |
| Evaluador: relevance / completeness / accuracy / overall | 9,83 / 9,67 / 10,0 / 9,67 (12 respuestas) | 9,85 / 9,46 / 9,92 / 9,46 (13 respuestas) |

**Qué falló y qué se cambió.** En la primera medición, la consulta 6 ("¿Cuál es el límite de solicitudes a la API en el plan Pro?") se enrutó a `fuera_de_dominio`. Repetida tres veces, el orquestador la mandó una vez a `fuera_de_dominio` y dos a `finance`: al leer "plan Pro" la asociaba a precios. Al prompt le faltaba una regla que la documentación ya establece ("Límites de la API y funciones técnicas de cada plan: Tech", en `facturacion_y_planes.md`). Se agregó esa regla a `prompts/orquestador.txt` y se volvió a medir. El resultado de la primera medición queda en `outputs/resultados_test_queries_v1.json`.

**Cuidado al leer estos números.** Son 15 consultas: un 100 % aquí no garantiza el mismo acierto con consultas reales. El evaluador usa el mismo modelo que genera las respuestas, así que sus notas altas pueden ser indulgentes (ver limitaciones). El modelo no es determinista: otra corrida puede variar en una o dos consultas.

Cómo se mide (para no mezclar errores técnicos con errores de routing):

- **Clasificaciones válidas y cobertura**: consultas en las que el orquestador respondió sin error, sobre el total.
- **Acierto de clasificación**: aciertos solo entre las clasificaciones válidas. Si el clasificador falla y la consulta cae en `fuera_de_dominio` por emergencia, **no** cuenta como acierto. Si la clasificación fue correcta pero falló la generación, el acierto de routing **sí** se conserva.
- **Errores técnicos por etapa**: `clasificacion`, `respuesta` o `desconocida`, con su `trace_id`.
- **Respuestas completadas**: consultas clasificadas y respondidas sin errores.
- **Promedios del evaluador**: solo sobre respuestas RAG completadas.

## 9. Decisiones técnicas

| Tema | Decisión | Por qué |
|---|---|---|
| Orquestación | LCEL: clasificador con `with_structured_output` + `RunnableBranch` | Es LangChain puro, como pide la consigna. El enrutamiento es determinista (depende de un campo validado, no de interpretar texto) y se puede medir contra las test queries. |
| Clasificación | Structured output con Pydantic (`Clasificacion`) | El departamento solo puede ser uno de 4 valores; si el modelo devuelve otra cosa, Pydantic lo rechaza y la consulta va a `fuera_de_dominio` en vez de enrutarse mal. |
| Vector store | Chroma (`langchain-chroma`), una colección por departamento, persistida en disco | Los embeddings se pagan una sola vez y se reutilizan; cada agente busca solo en su dominio; los metadatos (archivo, sección) son fáciles de inspeccionar. |
| Chunking | Primero por títulos (`MarkdownHeaderTextSplitter`), luego `RecursiveCharacterTextSplitter` de 500 caracteres con 50 de solapamiento | Cada chunk conserva su sección (sirve para citar fuentes) y es lo bastante chico para que el contexto sea preciso. Se obtienen entre 70 y 86 chunks por departamento (la consigna pide 50). |
| Recuperación | Similitud con `k=4` | Suficiente para cubrir respuestas que combinan 2–3 secciones sin llenar el prompt de ruido. Configurable con `RAG_K` o `--k`. |
| Lectura de documentos | `pathlib` en vez de `DirectoryLoader` | Evita depender de `langchain-community` y fuerza `utf-8`, necesario para tildes en Windows. |
| Fuera de dominio | Ruta sin LLM ni retriever, con un mensaje fijo | No se gasta API en consultas que no son de ningún área y no hay riesgo de que el modelo invente. |
| Sin contexto | Si el retriever no devuelve nada, se responde "No encontré…" sin llamar al modelo | Sin evidencia, el modelo no tiene con qué responder: mejor decirlo que inventar. |
| Evaluador | LLM-juez fuera de la cadena principal, con scores vía Score API | Si el evaluador falla, la respuesta igual llega al usuario. Los scores quedan en la misma traza que la respuesta. |
| Conexión con Langfuse | `auth_check()` una vez al crear el cliente | El SDK envía trazas y scores en segundo plano y no avisa si fallan; si el host no responde o las claves son inválidas, el sistema sigue sin trazas y lo avisa por consola. |
| Modelo | `gpt-6-luna` con `reasoning_effort=none` y `text-embedding-3-small` | Son los más baratos; para este caso la potencia no es prioridad. `none` evita tokens de razonamiento ocultos, que se cobran al precio de salida. |
| Prompts | Archivos `.txt` en `prompts/` | Se pueden ajustar sin tocar el código. |
| Langfuse | SDK 4.17: span raíz con `start_as_current_observation` + `CallbackHandler` + `propagate_attributes` (tags y metadata) + `create_score` | Langfuse Cloud ya no acepta en la vista de trazas los datos del SDK 3.x para organizaciones creadas desde el 16/09/2026: se comprobó que los spans del SDK 3.15 nunca aparecían y los del 4.17 sí. |

Alternativas descartadas:

- **LangGraph (`StateGraph`)**: más potente para flujos con ciclos, pero suma otra librería y este flujo es lineal (clasificar → delegar → responder).
- **Agente con tools** (cada agente RAG como herramienta del orquestador): el enrutamiento deja de ser determinista y es más difícil de medir contra las test queries.
- **FAISS** o **`InMemoryVectorStore`**: FAISS guarda un índice binario poco inspeccionable; el store en memoria vuelve a generar los embeddings en cada ejecución.

## 10. Configuración

Todas las opciones se leen del `.env`. Prioridad: flag de la CLI → variable de entorno → valor por defecto.

| Variable | Por defecto | Qué hace |
|---|---|---|
| `OPENAI_API_KEY` | — (obligatoria) | Clave de OpenAI |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | — (opcionales) | Claves de Langfuse; sin ellas no hay trazas |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Región de Langfuse |
| `OPENAI_MODEL` | `gpt-6-luna` | Modelo de chat (orquestador, agentes y evaluador) |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Modelo de embeddings |
| `OPENAI_REASONING_EFFORT` | `none` | Esfuerzo de razonamiento; vacío para no enviarlo |
| `RAG_K` | `4` | Chunks recuperados por consulta |
| `CHROMA_DIR` | `chroma_db/` | Carpeta donde Chroma guarda los índices |

Si cambias el modelo de embeddings, reconstruye el índice con `python -m src.indexacion --reconstruir`: los vectores de modelos distintos no son comparables.

## 11. Tests

```bash
python -m pytest tests/ -q
```

Los tests no llaman a OpenAI ni a Langfuse: usan modelos, retrievers y embeddings falsos. Comprueban, entre otras cosas, que cada dominio tenga al menos 50 chunks, que el enrutamiento elija el agente correcto, que una consulta vacía se rechace antes de gastar API y que el sistema siga respondiendo si Langfuse o el evaluador fallan.

## 12. Limitaciones conocidas

- El juez usa el mismo modelo barato que genera las respuestas: puede ser indulgente consigo mismo.
- Las consultas que mezclan dos departamentos se enrutan a uno solo.
- Los documentos son ficticios; el sistema no conoce políticas reales.
- La confianza del orquestador la declara el propio modelo y no está calibrada.
- La ejecución completa requiere una cuenta de OpenAI (de pago) y una de Langfuse (gratuita).
