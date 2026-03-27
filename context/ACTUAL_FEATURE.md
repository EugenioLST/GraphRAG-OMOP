# GraphRAG-OMOP - Estado Actual del Proyecto

## 📋 Resumen General

**Proyecto:** Sistema de búsqueda semántica sobre grafo OMOP con embeddings médicos

**Estado Global:** ✅ Phase 1 y Phase 2 COMPLETADAS como Proof of Concept

---

## ✅ PHASE 1: Construcción del Grafo OMOP - COMPLETADA

### Objetivo
Pipeline completo desde CSVs de OMOP hasta un grafo NetworkX navegable.

### Completado
- [x] **preprocess.py** - Procesar y filtrar CSVs gigantes de OMOP
  - Filtrado de vocabularios (SNOMED, RxNorm, LOINC, RxNorm Extension)
  - Procesamiento por chunks de CONCEPT_RELATIONSHIP.csv (1.7 GB)
  - Generación de nodes.csv y edges.csv
- [x] **graph.py** - Construcción de grafo MultiDiGraph
  - 3,855,450 nodos
  - 17,124,839 aristas
  - Caching con pickle (~2 GB)
  - Funciones: `get_concept_info()`, `get_neighbors()`, `find_standard_mapping()`
- [x] **Tests completos** - Validación con datos reales
- [x] **Substring search** - Búsqueda básica por nombre de concepto
- [x] **Validación** - 5 términos obligatorios: metformin, diabetes, creatinine, ibuprofen, hypertension

### Archivos Clave Phase 1
- `src/preprocess.py` - Procesamiento de CSVs OMOP
- `src/graph.py` - Gestión del grafo NetworkX
- `data/nodes.csv` - 3.8M conceptos filtrados
- `data/edges.csv` - 17M relaciones
- `data/omop_graph.pkl` - Grafo cacheado (~2 GB)

### Performance Phase 1
- Carga del grafo: ~5 segundos (con cache)
- Búsqueda substring: <10ms
- Cobertura: 3.8M conceptos completos

---

## ✅ PHASE 2: Semantic Search - COMPLETADA (PoC con 100k embeddings)

### Objetivo
Implementar búsqueda semántica con embeddings médicos (SapBERT) para manejar typos, sinónimos y multi-lingual.

### Session 1: Setup + Test Pequeño (10k) - COMPLETADA
- [x] Crear PHASE2_PLAN.md con estrategia incremental
- [x] Actualizar requirements.txt (torch CPU-only, sentence-transformers)
- [x] Instalar dependencias
- [x] Crear src/embeddings.py con soporte para subsets
- [x] Generar embeddings para 10k conceptos (~1-2 min)
- [x] Validar tiempos de carga

### Session 2: Retrieval + Test Mediano (100k) - COMPLETADA
- [x] Reorganizar estructura: src/, data/, tests/, scripts/
- [x] Crear src/retrieve.py con SemanticRetriever
- [x] Implementar búsqueda semántica (cosine similarity)
- [x] Implementar filtros (vocabulary, domain, standard_only)
- [x] Generar embeddings para 100k conceptos (~10-15 min, ~300 MB)
- [x] **Bug crítico arreglado:** Graph expansion usaba solo 100k en vez de 3.8M
- [x] Crear scripts/validate_phase2.py
- [x] Validar 5 términos obligatorios (100% éxito)
- [x] Actualizar context/ARCHITECTURE.md

### Session 3: CLI + Validación - COMPLETADA
- [x] Crear main.py con CLI completo
- [x] Implementar argument parsing (argparse)
- [x] Implementar pretty printing de resultados
- [x] Implementar batch mode (CSV input/output)
- [x] **Añadir modo interactivo** - Preguntas simples al usuario
- [x] Crear scripts/compare_phase1_phase2.py
- [x] Documentar resultados (PHASE2_SESSION2_RESULTS.md, PHASE2_SESSION3_RESULTS.md)

### Archivos Clave Phase 2
- `main.py` - CLI interface (interactivo + programático + batch)
- `src/embeddings.py` - Generación de embeddings con SapBERT
- `src/retrieve.py` - Motor de búsqueda semántica
- `scripts/validate_phase2.py` - Validación automática de 5 términos
- `scripts/compare_phase1_phase2.py` - Comparación de enfoques
- `data/embeddings.npy` - 100k embeddings (~300 MB)
- `data/concept_id_to_index.pkl` - Mapeo de IDs (~2 MB)

### Capacidades Implementadas
1. ✅ **Búsqueda semántica** con SapBERT (100k conceptos)
2. ✅ **Graph expansion** usando grafo completo (3.8M nodos)
3. ✅ **CLI interactivo** - Modo pregunta/respuesta user-friendly
4. ✅ **CLI programático** - Argumentos para scripts
5. ✅ **Batch mode** - Procesar múltiples queries desde CSV
6. ✅ **Multi-lingual** - Español e inglés validados
7. ✅ **Filtros** - Por vocabulary, domain, standard concepts
8. ✅ **Validación completa** - 5/5 términos obligatorios encontrados

### Performance Phase 2
- Inicialización: ~15 segundos (una vez)
- Query: <1 segundo
- Cobertura: 100k embeddings + 3.8M graph expansion
- Multi-lingual: ✅ Funcional

### Resultados de Validación (100k subset)
| Término | Score | Estado |
|---------|-------|--------|
| Metformin | 0.952 | ✅ |
| Diabetes | 0.732 | ✅ |
| Creatinine | 0.606 | ✅ |
| Ibuprofen | 0.922 | ✅ |
| Hypertension | 0.606 | ✅ |

**Success Rate:** 5/5 (100%)

---

## 🎯 Sistema Actual Funcional

### 3 Modos de Uso del main.py

#### 1. Modo Interactivo ⭐ (Nuevo)
```bash
venv/Scripts/python.exe main.py
```
- Pregunta el concepto médico
- Pregunta número de resultados (default: 10)
- Pregunta si mostrar related concepts (y/n)
- Permite múltiples búsquedas en sesión

#### 2. Modo CLI (Programático)
```bash
# Búsqueda simple
venv/Scripts/python.exe main.py "metformina"

# Con opciones
venv/Scripts/python.exe main.py "diabetes" --expand --top-k 5

# Con filtros
venv/Scripts/python.exe main.py "ibuprofen" --domain Drug --standard-only
```

#### 3. Modo Batch
```bash
venv/Scripts/python.exe main.py --batch queries.csv --output results.csv
```

---

## 📊 Comparación Phase 1 vs Phase 2

| Característica | Phase 1 (Substring) | Phase 2 (Semantic) |
|----------------|---------------------|---------------------|
| Velocidad | <10ms | <1s |
| Cobertura | 3.8M conceptos | 100k embeddings + 3.8M graph |
| Typos | ❌ No | ✅ Sí (parcial) |
| Sinónimos | ❌ No | ✅ Sí |
| Multi-lingual | ❌ No | ✅ Sí |
| Graph expansion | ✅ Sí | ✅ Sí (mejorado) |

---

## ⚠️ Pendiente (Opcional - NO Crítico)

### Session 4: Full Dataset (NO INICIADO)
- [ ] Generar embeddings para 3.8M conceptos completos
  - ⏱️ Tiempo: 4-8 horas CPU
  - 💾 Espacio: ~11 GB
  - 📝 Comando: `venv/Scripts/python.exe src/embeddings.py --max-concepts 3800000`
- [ ] Re-validar con dataset completo
- [ ] Documentar resultados finales
- [ ] Optimizaciones de performance

### Session 5: Model Comparison (NO INICIADO)
- [ ] Añadir soporte ModernPubMedBERT a embeddings.py
- [ ] Generar embeddings con ModernPubMedBERT (100k)
- [ ] Comparar SapBERT vs ModernPubMedBERT
- [ ] Benchmark: accuracy, speed, memory
- [ ] Decisión: mantener SapBERT o cambiar

---

## 🎓 Decisiones Técnicas Clave

### ¿Por qué 100k en lugar de 3.8M?
**Decisión:** Proof of Concept con 100k conceptos
**Razón:**
- Validación rápida (~15 min vs 4-8 horas)
- Suficiente para demostrar capacidades
- Permite iteración rápida
- Graph expansion compensa con grafo completo

**Resultado:** ✅ Sistema funcional que demuestra el concepto exitosamente

### ¿Por qué SapBERT?
**Decisión:** SapBERT como modelo principal
**Razón:**
- Estado del arte para UMLS/SNOMED CT
- Entrenado específicamente en conceptos médicos
- F1-Score 0.853 en normalización médica
- Validado en producción (papers 2024)

### Bug Crítico Encontrado y Arreglado
**Problema:** Graph expansion solo mostraba vecinos en 100k embeddings
**Causa:** `expand_graph()` usaba `self.concept_metadata` (100k) en lugar del grafo completo
**Solución:** Cambiar a obtener metadata de `self.graph.nodes` (3.8M)
**Impacto:** Graph expansion ahora funciona con cobertura total

---

## 📝 Comandos Útiles

### Validación
```bash
# Validar 5 términos obligatorios
venv/Scripts/python.exe scripts/validate_phase2.py

# Comparar Phase 1 vs Phase 2
venv/Scripts/python.exe scripts/compare_phase1_phase2.py
```

### Generar embeddings (si se necesita más cobertura)
```bash
# 100k (actual)
venv/Scripts/python.exe src/embeddings.py --max-concepts 100000

# 500k (más cobertura)
venv/Scripts/python.exe src/embeddings.py --max-concepts 500000

# Full 3.8M (producción, 4-8 horas)
venv/Scripts/python.exe src/embeddings.py --max-concepts 3800000
```

---

## 🚀 Próximos Pasos Recomendados

### Opción A: Concluir como PoC ✅ RECOMENDADO
**El estado actual es suficiente para:**
- ✅ Demostración del concepto
- ✅ Validación técnica completa
- ✅ Toma de decisiones arquitectónicas
- ✅ Presentación a stakeholders

**Acción:** Documentar conclusión de proyecto como PoC exitoso

### Opción B: Escalar a Producción
**Si se necesita deployment:**
1. Generar 3.8M embeddings (4-8 horas)
2. 100% cobertura de conceptos OMOP
3. Sistema production-ready

### Opción C: Investigación/Optimización
**Si se necesita mejora científica:**
1. Comparar SapBERT vs ModernPubMedBERT
2. Validación científica rigurosa
3. Posibles mejoras de accuracy

---

## 📈 Métricas de Éxito Alcanzadas

### Cuantitativo
- ✅ 5/5 términos obligatorios encontrados (100%)
- ✅ Velocidad <1s por query (objetivo cumplido)
- ✅ Multi-lingual funcional (español/inglés validado)
- ✅ Graph expansion funcional con cobertura completa
- ✅ Sistema escalable validado (10k → 100k → 3.8M posible)

### Cualitativo
- ✅ Sistema user-friendly (modo interactivo)
- ✅ Búsqueda semántica funcional (sinónimos, typos)
- ✅ Arquitectura modular y bien documentada
- ✅ CLI versátil (3 modos de uso)
- ✅ Código bien estructurado y testeado

---

## 📚 Documentación Completa

### Archivos de Planificación
1. `context/PHASE2_PLAN.md` - Plan de implementación Phase 2
2. `context/ACTUAL_FEATURE.md` - Este archivo (estado actual)

### Archivos de Arquitectura
3. `context/ARCHITECTURE.md` - Arquitectura completa del sistema
4. `README.md` - Setup e instrucciones generales

### Archivos de Resultados
5. `context/PHASE2_SESSION2_RESULTS.md` - Resultados Session 2 (Retrieval + 100k)
6. `context/PHASE2_SESSION3_RESULTS.md` - Resultados Session 3 (CLI + Validación)

---

## 📁 Estructura de Archivos Actual

```
GraphRAG-OMOP/
├── main.py                          # CLI interface (3 modos)
│
├── src/
│   ├── preprocess.py                # Phase 1: Procesar CSVs OMOP
│   ├── graph.py                     # Phase 1: Grafo NetworkX
│   ├── embeddings.py                # Phase 2: Generar embeddings SapBERT
│   └── retrieve.py                  # Phase 2: Búsqueda semántica
│
├── scripts/
│   ├── validate_phase2.py           # Validación automática 5 términos
│   └── compare_phase1_phase2.py     # Comparación Phase 1 vs 2
│
├── tests/
│   ├── test_retrieve_quick.py       # Tests rápidos semantic search
│   └── (otros tests Phase 1)
│
├── data/
│   ├── nodes.csv                    # 3.8M conceptos OMOP
│   ├── edges.csv                    # 17M relaciones
│   ├── omop_graph.pkl               # Grafo cacheado (~2 GB)
│   ├── embeddings.npy               # 100k embeddings (~300 MB)
│   └── concept_id_to_index.pkl      # Mapeo de IDs
│
├── context/
│   ├── PHASE2_PLAN.md               # Plan Phase 2
│   ├── ARCHITECTURE.md              # Arquitectura completa
│   ├── PHASE2_SESSION2_RESULTS.md   # Resultados Session 2
│   ├── PHASE2_SESSION3_RESULTS.md   # Resultados Session 3
│   └── ACTUAL_FEATURE.md            # Este archivo
│
├── venv/                            # Virtual environment
├── requirements.txt                 # Dependencias Python
└── README.md                        # Instrucciones generales
```

---

## ✅ Conclusión

### Estado del Proyecto
**✅ PHASE 1 y PHASE 2 COMPLETADAS como Proof of Concept exitoso**

### Lo que funciona
- ✅ Grafo OMOP completo (3.8M conceptos, 17M relaciones)
- ✅ Búsqueda semántica con embeddings médicos (100k)
- ✅ Graph expansion con cobertura total (3.8M)
- ✅ CLI user-friendly (interactivo + programático + batch)
- ✅ Multi-lingual support (español/inglés)
- ✅ Validación completa (5/5 términos)
- ✅ Documentación exhaustiva

### Sistema listo para
- ✅ Demostraciones técnicas
- ✅ Testing con usuarios reales
- ✅ Evaluación de escalabilidad
- ✅ Decisión de deployment a producción

### Tiempo Invertido
- **Phase 1:** ~6-8 horas (según estimado original)
- **Phase 2:** ~6-8 horas (según PHASE2_PLAN.md)
- **Total:** ~12-16 horas

### Próximo Paso Recomendado
**Documentar conclusión del proyecto y presentar resultados del PoC a stakeholders para decidir si escalar a producción (3.8M embeddings) o mantener como PoC.**

---

## 📊 Métricas Finales

| Métrica | Objetivo | Alcanzado | Estado |
|---------|----------|-----------|--------|
| Términos obligatorios | 5/5 | 5/5 | ✅ |
| Velocidad query | <1s | <1s | ✅ |
| Multi-lingual | Sí | Sí | ✅ |
| Graph expansion | Funcional | Funcional | ✅ |
| CLI user-friendly | Sí | Sí | ✅ |
| Documentación | Completa | Completa | ✅ |

**Estado Final:** ✅ **PROYECTO EXITOSO - PoC COMPLETADO**

---

## 🎨 NEXT PHASE: Visual Dashboard (PLANNED)

### Objetivo
Crear un dashboard visual con Next.js + TypeScript para demos en vivo con médicos.

### Estado
🔵 **PLANNED** - Plan completo en `context/DASHBOARD_PLAN.md`

### Scope
- **Backend:** FastAPI wrapper del pipeline existente
- **Frontend:** Next.js 14 con TypeScript + Tailwind CSS
- **Features:**
  - Input de texto clínico + ejemplos pre-cargados
  - Visualización de resultados en tabla interactiva
  - Exportación a CSV
  - UI profesional para audiencia médica

### Timeline Estimado
- **Total:** 29-42 horas (~4-6 días)
- **Fases:** 10 fases incrementales
- **Prioridad:** Media (demo enhancement)

### Documentación
- Plan detallado: `context/DASHBOARD_PLAN.md`
- Setup guide: (pending) `DASHBOARD_SETUP.md`
- Demo guide: (pending) `DASHBOARD_DEMO_GUIDE.md`

---

## 🕐 FEATURE: Temporal Detection + Patient Journey Timeline

### Objetivo
Extraer información temporal de cada concepto médico en Phase 1 y visualizar un timeline tipo "patient journey" en el dashboard.

### Estado
✅ **IMPLEMENTED** — All 14 steps completed, frontend builds successfully

---

### 1. Contexto y Motivación

El pipeline actual extrae conceptos médicos y los mapea a OMOP, pero **no captura cuándo ocurrió cada evento**. Para una demo clínica efectiva, se necesita:
- Saber que "diabetes" fue diagnosticada en 2019
- Que "metformina" se inició en enero 2024
- Que "disnea" es actual

Esto permite mostrar un **patient journey**: una línea temporal visual con eventos médicos distribuidos cronológicamente.

### 2. Decisiones de Diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Granularidad temporal | Variable ("2024", "2024-03", "2024-03-15") | No inventar precisión que no existe en el texto |
| Fecha de referencia | Auto-detectada por GPT-4, fallback: input del usuario o fecha actual | Necesaria para resolver "hace 3 meses" |
| Asociación concepto-fecha | Solo si es explícita en el texto | Evitar asociaciones incorrectas |
| Sin fecha | `null` (no inventar) | Honestidad > completitud |
| Visualización | CSS/Tailwind puro, sin librería de charts | Sin dependencias nuevas (RULES.md §6) |

### 3. Plan de Implementación

#### Paso 1: Backend Schema Phase 1
**Archivo:** `backend/src/phase1/schema.py`
**Tiempo estimado:** 5 min

Añadir campos temporales a `MedicalConcept` y `reference_date` a `ExtractionResult`:

```python
class MedicalConcept(BaseModel):
    # ... campos existentes ...
    date: Optional[str] = Field(default=None, description="ISO date: YYYY, YYYY-MM, or YYYY-MM-DD")
    date_original: Optional[str] = Field(default=None, description="Original temporal expression from text")

class ExtractionResult(BaseModel):
    reference_date: Optional[str] = Field(default=None, description="Document reference date YYYY-MM-DD")
    concepts: List[MedicalConcept] = Field(default_factory=list)
```

#### Paso 2: Backend Prompt Phase 1
**Archivo:** `backend/src/phase1/prompts.py`
**Tiempo estimado:** 20 min

- Añadir placeholder `{reference_date}` al prompt
- Añadir reglas 12-15 de extracción temporal
- Añadir tabla de ejemplos temporales
- Regla clave: solo asociar fecha si es explícita, null si no hay info temporal

#### Paso 3: Backend Extractor
**Archivo:** `backend/src/phase1/extractor.py`
**Tiempo estimado:** 10 min

- `extract_medical_entities()` acepta `reference_date` opcional
- Fallback a `datetime.now().strftime("%Y-%m-%d")` si no se provee
- Pasar `reference_date` a `chain.invoke()`

#### Paso 4: Backend Main Phase 1
**Archivo:** `backend/src/phase1/main.py`
**Tiempo estimado:** 5 min

- `run_extraction()` acepta y pasa `reference_date`

#### Paso 5: Backend API Schemas
**Archivo:** `backend/schemas.py`
**Tiempo estimado:** 10 min

- `Phase1Request`: añadir `reference_date: Optional[str]`
- `Phase1Response`: añadir `reference_date: Optional[str]`
- `ConceptSchema`: añadir `date`, `date_original`
- `MappingSchema`: añadir `date`, `date_original`

#### Paso 6: Backend Router Phase 1
**Archivo:** `backend/routers/phase1.py`
**Tiempo estimado:** 5 min

- Pasar `request.reference_date` a `run_extraction()`

#### Paso 7: Backend Router Phase 2
**Archivo:** `backend/routers/phase2.py`
**Tiempo estimado:** 5 min

- Pass-through de `date` y `date_original` en `process_concept()`

#### Paso 8: Frontend Types
**Archivo:** `frontend/lib/types.ts`
**Tiempo estimado:** 10 min

- Añadir `date`, `date_original` a `ExtractedConcept` y `ConceptMapping`
- Añadir `reference_date` a `Phase1Request` y `Phase1Response`
- Añadir `DOMAIN_DOT_COLORS` para los dots del timeline

#### Paso 9: Frontend API Client
**Archivo:** `frontend/lib/api.ts`
**Tiempo estimado:** 10 min

- `extractConcepts()` acepta `referenceDate?: string`
- Incluir en request body si está presente

#### Paso 10: Frontend InputSection
**Archivo:** `frontend/components/InputSection.tsx`
**Tiempo estimado:** 15 min

- Añadir props: `referenceDate`, `onReferenceDateChange`
- Añadir `<input type="date">` nativo con botón Clear
- Texto: "Document date (optional): If empty, auto-detected from text"

#### Paso 11: Frontend TimelineView (NUEVO)
**Archivo:** `frontend/components/TimelineView.tsx`
**Tiempo estimado:** 45 min

Componente de timeline horizontal puro CSS/Tailwind:
- Agrupa eventos por fecha, ordena cronológicamente
- Pills coloreados por dominio (reutiliza DOMAIN_COLORS)
- Tooltips con detalles (shadcn Tooltip existente)
- Scroll horizontal si hay muchos puntos (`overflow-x-auto`)
- Sección "Sin fecha" para conceptos sin temporalidad
- Envuelto en Card de shadcn

#### Paso 12: Frontend Page.tsx
**Archivo:** `frontend/app/page.tsx`
**Tiempo estimado:** 10 min

- Estado: `referenceDate`
- Pasar a InputSection y a `extractConcepts()`
- Insertar `<TimelineView>` entre SummaryStats y ResultsTable

#### Paso 13: Frontend CSV Export
**Archivo:** `frontend/lib/csv-export.ts`
**Tiempo estimado:** 5 min

- Añadir columnas "Date" y "Date Original"

#### Paso 14: Frontend ConceptRow
**Archivo:** `frontend/components/ConceptRow.tsx`
**Tiempo estimado:** 5 min

- Mostrar fecha en vista expandida si existe

### 4. Archivos a Crear/Modificar

| Archivo | Acción | Líneas estimadas |
|---|---|---|
| `backend/src/phase1/schema.py` | Modificar | +6 |
| `backend/src/phase1/prompts.py` | Modificar | +40 |
| `backend/src/phase1/extractor.py` | Modificar | +5 |
| `backend/src/phase1/main.py` | Modificar | +3 |
| `backend/schemas.py` | Modificar | +8 |
| `backend/routers/phase1.py` | Modificar | +2 |
| `backend/routers/phase2.py` | Modificar | +4 |
| `frontend/lib/types.ts` | Modificar | +15 |
| `frontend/lib/api.ts` | Modificar | +8 |
| `frontend/components/InputSection.tsx` | Modificar | +20 |
| **`frontend/components/TimelineView.tsx`** | **CREAR** | ~200 |
| `frontend/app/page.tsx` | Modificar | +10 |
| `frontend/lib/csv-export.ts` | Modificar | +4 |
| `frontend/components/ConceptRow.tsx` | Modificar | +8 |

**Total:** 13 archivos modificados + 1 archivo nuevo

### 5. Tests Necesarios

| Test | Tipo | Descripción |
|---|---|---|
| Temporal extraction con fechas absolutas | Expected | "diagnosticado en 2019" → date="2019" |
| Temporal extraction con fechas relativas | Expected | "hace 3 meses" → date calculada |
| Conceptos sin fecha | Edge case | "tiene hipertensión" → date=null |
| Granularidad variable | Edge case | "2024" vs "2024-03" vs "2024-03-15" |
| Texto sin ninguna fecha | Edge case | Todos los conceptos con date=null |
| Reference date fallback | Edge case | Sin fecha de referencia → usa fecha actual |
| Pass-through Phase 2 | Integration | date/date_original llegan al frontend |
| Timeline con mezcla dated/undated | UI | Ambas secciones se renderizan |
| Timeline vacío (sin fechas) | Edge case | Componente no se renderiza |
| CSV export con fechas | Expected | Columnas Date y Date Original presentes |

**Verificación end-to-end:**
1. Reiniciar backend
2. Probar: "Paciente diagnosticado de DM tipo 2 en 2019. En enero 2024 inicia metformina 850mg. Actualmente presenta disnea."
3. Verificar: timeline muestra 2019, 2024-01, fecha actual
4. Verificar: conceptos sin fecha en sección separada
5. Verificar: CSV exporta columnas temporales

### 6. Estimación de Tiempo

| Bloque | Tiempo |
|---|---|
| Backend schemas + prompt (pasos 1-7) | 1 hora |
| Frontend types + API + InputSection (pasos 8-10) | 35 min |
| TimelineView nuevo componente (paso 11) | 45 min |
| Page.tsx + CSV + ConceptRow (pasos 12-14) | 20 min |
| Testing y ajustes | 30 min |
| **Total estimado** | **~3 horas** |

### 7. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| GPT-4 asocia mal fecha↔concepto | Media | Regla 15: solo asociar si es explícito |
| Fechas relativas mal calculadas | Baja | Ejemplos claros en prompt + date_original para verificar |
| Prompt más largo → más tokens/coste | Inevitable | ~200 tokens extra, insignificante |
| Timeline horizontal overflow | Baja | `overflow-x-auto` con scroll |
| Backward compatibility | Nula | Todos los campos son Optional/nullable |
