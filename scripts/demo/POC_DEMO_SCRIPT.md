# 🎯 PoC Demo Script - GraphRAG-OMOP

**Objetivo:** Demostrar capacidades clave del sistema en 5-10 minutos

---

## ✅ Palabras que FUNCIONAN con tus 100k Embeddings

### 📊 Resumen Rápido
- **99,643 medicamentos** (Drug domain)
- **149 condiciones médicas** (SNOMED)
- **834 conceptos con "insulin"**
- **440 conceptos con "aspirin"**
- **751 conceptos con "vitamin"**

---

## 🎬 DEMO FLOW RECOMENDADO (5 minutos)

### Demo 1: Búsqueda Básica de Medicamento
```bash
python main.py
```

**Query:** `insulin`
- **Resultados esperados:** 834 matches
- **Qué muestra:** Búsqueda semántica básica
- **Ejemplo resultado:** "insulin aspart", "insulin glargine", etc.

---

### Demo 2: Multi-lingual Support (Español/Inglés)
**Query 1:** `metformin`
**Query 2:** `metformina`

- **Qué muestra:** Mismo concepto en diferentes idiomas
- **Score esperado:** >0.90 (alta confianza)
- **Concepto encontrado:** Metformin (concept_id: 1503297 o similar)

---

### Demo 3: Graph Expansion (Relaciones)
**Query:** `metformin`
- **Top-k:** 3 resultados
- **Graph expansion:** YES

**Qué muestra:**
- Resultados semánticos (metformin combinations)
- Relaciones del grafo:
  - "Has tradename" → Janumet
  - "RxNorm has dose form" → Oral Tablet
  - "Ingredient of" → Combinations with sitagliptin

**Impacto:** Demuestra que no solo busca, sino que expande contexto médico

---

### Demo 4: Condiciones Médicas (SNOMED)
**Query:** `hallucination`

- **Resultados esperados:**
  - "Somatic hallucination"
  - "Visual hallucinations" (formed/unformed)
  - "Scenic visual hallucinations"
- **Qué muestra:** Funciona para condiciones médicas, no solo medicamentos

---

### Demo 5: Búsqueda de Vitaminas/Suplementos
**Query:** `vitamin b12`

- **Resultados esperados:** >100 matches
- **Qué muestra:** Encuentra combinaciones complejas (vitamin B12 + B6 + folic acid)

---

## 🚀 QUERIES GARANTIZADAS PARA PoC

### ✅ Tier 1: SIEMPRE Funcionan (>500 matches)
```
insulin           → 834 matches
vitamin           → 751 matches
aspirin           → 440 matches
```

### ✅ Tier 2: MUY Fiables (>50 matches)
```
pain              → 368 matches
ibuprofen         → varios
metformin         → varios
fever             → 73 matches
heart             → 47 matches
```

### ✅ Tier 3: Específicas (1-20 matches)
```
hallucination     → varios (SNOMED conditions)
diabetes          → 1 match (Prediabetes)
infection         → 9 matches
blood             → 10 matches
pressure          → 13 matches
```

---

## 🎯 MEJORES DEMOS POR CASO DE USO

### Si quieres mostrar: **Semantic Search**
**Query:** `insulin` o `aspirin`
- Mucha variedad de resultados
- Diferentes formas/dosis
- Demuestra poder semántico

### Si quieres mostrar: **Multi-lingual**
**Queries:**
1. `metformin` (English)
2. `metformina` (Spanish)
- Mismo concepto, diferentes idiomas
- Scores altos (>0.90)

### Si quieres mostrar: **Graph Expansion**
**Query:** `metformin` + expansion YES
- Muestra combinaciones (Janumet)
- Relaciones OMOP reales
- Contexto clínico ampliado

### Si quieres mostrar: **Medical Terminology**
**Query:** `hallucination`
- Condiciones SNOMED específicas
- No solo medicamentos
- Terminología clínica precisa

---

## 📝 SCRIPT PARA DEMO EN VIVO (Copy-Paste)

```bash
# Terminal listo
cd c:\Users\aviguera\Documents\GitHub\GraphRAG-OMOP
python main.py

# Demo 1: Búsqueda básica
insulin
10
n
n

# Demo 2: Multi-lingual
metformina
5
n
n

# Demo 3: Graph expansion
metformin
3
y
n

# Demo 4: Medical condition
hallucination
5
n
n

# Demo 5: Complex search
vitamin b12
5
n
q
```

---

## ⚠️ QUERIES que NO Funcionarán Bien (Evitar en PoC)

❌ **Tests de laboratorio genéricos** (solo 19 LOINC)
- "hemoglobin test"
- "glucose measurement"

❌ **Procedimientos quirúrgicos** (solo 95 en embeddings)
- "appendectomy"
- "cardiac bypass"

❌ **Dispositivos médicos** (solo 4 concepts)
- "pacemaker"
- "stent"

---

## 💡 MENSAJES CLAVE DEL PoC

1. **"No es búsqueda por texto"** → Es búsqueda semántica (entiende significado)
2. **"Multi-lingual"** → Español e inglés funcionan igual
3. **"Expande contexto"** → Graph expansion añade relaciones clínicas
4. **"99,643 medicamentos"** → Cobertura amplia de farmacología
5. **"Escalable a 3.8M"** → Actualmente 100k, expandible a todos los conceptos OMOP

---

## 🎤 PITCH de 30 segundos

> "GraphRAG-OMOP convierte términos médicos en conceptos OMOP estandarizados
> usando embeddings semánticos. A diferencia de búsqueda por texto, entiende
> el significado: 'metformina' y 'metformin' encuentran el mismo concepto.
> Funciona en español e inglés, cubre 99k medicamentos, y expande el grafo
> para mostrar relaciones clínicas. Este PoC usa 100k conceptos, pero escala
> a 3.8M para cobertura completa de OMOP."

---

## ✅ Checklist Pre-Demo

- [ ] Terminal abierto en directorio del proyecto
- [ ] Virtual environment activado
- [ ] Ejecutar `python main.py` una vez para cargar embeddings (~15 seg)
- [ ] Tener lista de queries a mano (este documento)
- [ ] Saber explicar diferencia entre semantic search y substring match
- [ ] Poder explicar qué es graph expansion

---

## 🔧 Troubleshooting Durante Demo

**Si algo no funciona:**

1. **"No encuentra resultados"**
   → Usar queries de Tier 1 (insulin, vitamin, aspirin)

2. **"Carga muy lento"**
   → Primera carga tarda ~15 seg (embeddings), explicar que es caching

3. **"No hay graph expansion"**
   → Asegurar que seleccionas "y" cuando pregunta por expansion

4. **"Pide más ejemplos"**
   → Ir a Category 5 del análisis (834 matches de "insulin")

---

## 📊 Números para Impresionar

- **100,000** conceptos con embeddings (2.6% de OMOP)
- **99,643** medicamentos cubiertos
- **3.8M** conceptos totales en grafo OMOP
- **17.1M** relaciones en el grafo
- **<1 segundo** tiempo de búsqueda (después de carga inicial)
- **768 dimensiones** embeddings médicos (SapBERT)
- **~15 segundos** inicialización (caching optimizado)

---

¡LISTO PARA DEMO! 🚀