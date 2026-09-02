# HANDOVER — GraphRAG-OMOP

> Traspaso del repo al LST (UPM), septiembre de 2026. Este fichero solo contiene lo que no
> tiene otro sitio: personas, dónde están físicamente los datos y las cuentas, decisiones de
> código no documentadas, y por dónde empezar. Todo lo demás está enlazado.

| Necesitas                                              | Ve a                                                                   |
| ------------------------------------------------------ | ---------------------------------------------------------------------- |
| Entender el problema y el pipeline                     | [EXPLICACION_PROBLEMA.md](EXPLICACION_PROBLEMA.md)                     |
| Qué hay hecho, qué falta, en qué orden y quién lo hace | [PLAN_MEJORAS.md](PLAN_MEJORAS.md)                                     |
| Diseño de la Fase 1 para Inetum                        | [FASE1_DISENO_EXTRACCION_INETUM.md](FASE1_DISENO_EXTRACCION_INETUM.md) |
| Instalar, generar datos, arrancar, troubleshooting     | [README.md](README.md)                                                 |
| API y validación manual                                | [backend/README.md](backend/README.md)                                 |

**Estado en una frase:** demo funcional de punta a punta, no producción. La Fase 1 de
producción la hace Inetum; la Fase 2 la mejora y despliega el LST.

---

## 1. Personas

| Tema                                | Quién                        | Notas                                                                                     |
| ----------------------------------- | ---------------------------- | ----------------------------------------------------------------------------------------- |
| Custodia del repo en el LST         | **Eugenio**                  | Recibe el repo en GitLab. A fecha del traspaso no hay sucesor técnico asignado.           |
| Fase 1 (extracción, PDF, LLM local) | **Adrián Carrasco (Inetum)** | Dueño de la Fase 1. `backend/PDF Extraction.ipynb` es su borrador inicial, no definitivo. |
| Fase 2 (mapeo OMOP, este código)    | Sin asignar                  | Lo hereda quien designe Eugenio.                                                          |

**Primera acción de quien herede esto:** escribir a Adrián Carrasco. No hubo reunión de
reparto (§0.1 de PLAN_MEJORAS) ni se le entregó la nota de diseño. Hay que saber si Inetum ha
avanzado en la Fase 1 y acordar el JSON de salida que consumirá `/phase2`.

---

## 2. Datos y cuentas

| Qué                                                                                 | Situación al traspaso                        | Qué hacer                                                                                                                      |
| ----------------------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `backend/data/` (28 GB: Athena, `processed/`, `embeddings/` con los 3,8M completos) | No estaba en ningún almacenamiento del grupo | Ruta en el grupo: `[RELLENAR]`. Si no existe, regenerar (README, "Generar Datos"; ~1 h con GPU, 4-8 h CPU, +1 h preprocesado). |
| Versión de la release de Athena                                                     | No registrada                                | Hueco `[RELLENAR]` en README, Paso 1.                                                                                          |
| `OPENAI_API_KEY` (`backend/.env`)                                                   | Cuenta personal del autor anterior, revocada | Key propia, o migrar a Ollama (PLAN_MEJORAS §1.3). Sin key el backend ni importa.                                              |
| Cuenta Athena                                                                       | Personal, no transferible                    | Crear una (gratis).                                                                                                            |
| SapBERT                                                                             | HuggingFace público, sin cuenta              | Se descarga solo (~440 MB) a `~/.cache/huggingface`.                                                                           |
| Servidores / BBDD del grupo                                                         | **Ninguno**, todo local                      | Neo4j/Qdrant solo existen en el plan (PLAN_MEJORAS §3).                                                                        |

---

## 3. Decisiones de código que no están escritas en otro sitio

Las decisiones de producto están en PLAN_MEJORAS parte 2. Estas son las del código tal
como está:

1. **Búsqueda solo entre estándar** (`standard_only=True`, `retrieve.py:341`). Simplifica la
   demo pero pierde el puente no-estándar → estándar. Marcado para quitar (v1).
2. **Umbral REVIEW = 0.7** (`retrieve.py:401`). Los docs recordaban 0.8. Se fija con golden dataset.
3. **FAISS aproximado**: `nprobe = 10` de 256 clusters (`retrieve.py:85`), ~4% del índice por
   consulta. Subirlo recupera precisión a cambio de latencia.
4. **Conceptos `C` se aceptan** si bajando la jerarquía (`Subsumes`, `Has ingredient`) hay un
   único `S` a la profundidad mínima (`graph.py:_resolve_classification_to_standard`). Varios → REVIEW.
5. **Metadatos por `nrows`** (`retrieve.py:97`): funciona porque `embeddings.py` embebe
   exactamente las primeras N filas de `nodes.csv` en orden. Otro orden o subconjunto cruza
   nombres **sin error**.
6. **NetworkX en RAM, no Neo4j**: para no depender de infraestructura en el POC. Coste:
   arranque de minutos y ~16 GB.
7. **Una sola llamada LLM hace extracción + traducción + expansión** (`prompts.py`, reglas 9
   y 10). Superseded por el diseño de Fase 1, pero es lo que corre.
8. **`/phase2` paraleliza con `asyncio.to_thread` sin semáforo** (`routers/phase2.py:60`).
   Seguro en CPU; con GPU compartida puede fallar.
9. **OpenAI en la Fase 1 fue una decisión de demo.** La versión real debe ser local (MedGemma)
   por privacidad/EHDS, y la hace Inetum.
10. **No hay tests.** Los que había apuntaban a rutas anteriores a `src/phase2/` y se borraron
    en el traspaso. Escribirlos de cero contra `src.phase2.*`, no recuperarlos del historial.

---

## 4. Por dónde empezar

1. Leer los cuatro documentos de la tabla de arriba.
2. Escribir a Adrián Carrasco antes de tocar código.
3. Conseguir o regenerar `backend/data/` en una máquina del grupo y arrancar la demo (README).
4. Rellenar los dos `[RELLENAR]` (ruta de datos aquí, versión de Athena en README).
5. Atacar PLAN_MEJORAS parte 1 en su orden: Fase A primero, que no necesita médico.
