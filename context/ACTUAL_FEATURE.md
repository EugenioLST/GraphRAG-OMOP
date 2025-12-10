# FEATURE: Fase 1 - Construcción del Grafo OMOP

## OBJETIVO

Implementar el pipeline completo desde CSVs de OMOP hasta un grafo NetworkX navegable:

1. **preprocess.py** - Procesar y filtrar CSVs gigantes de OMOP
2. **graph.py** - Construir grafo MultiDiGraph con NetworkX
3. **Tests completos** - Validar con datos reales

**Caso de uso principal**: Dado un término médico (estándar o no estándar), encontrar el concepto estándar OMOP equivalente usando relaciones de mapeo.

---

## ESTRATEGIA DE FILTRADO

### CONCEPT.csv (565 MB)
- **Columnas**: `concept_id`, `concept_name`, `vocabulary_id`, `domain_id`, `standard_concept`
- **Filtros**:
  - Solo vocabularios: `SNOMED`, `RxNorm`, `LOINC`, `RxNorm Extension`
  - **Mantener términos estándar Y no estándar** (standard_concept = 'S', 'C', o NULL)
- **Razón**: Los términos no estándar son parte del proceso de búsqueda y mapeo

### RELATIONSHIP.csv (53 KB)
- Filtrar solo relaciones relevantes (~15-20 de 722 totales):
  - **Mapeo**: `Maps to` (44818977), `Mapped from` (44818976) - CRÍTICO
  - **Jerarquías**: `Is a`, `Subsumes`, `RxNorm is a`
  - **Composición**: `RxNorm has ing`, `Has form`, `Contains`, etc.

### CONCEPT_RELATIONSHIP.csv (1.7 GB)
- **Procesamiento por chunks** (obligatorio)
- Solo relaciones en whitelist
- Solo entre concept_ids que existen en CONCEPT filtrado
- **Optimización**: Filtrar en memoria cada chunk antes de concatenar

---

## ARCHIVOS A CREAR

### 1. preprocess.py (~250 líneas)

**Funciones**:
```python
def validate_input_files() -> None
    # Verificar que data/CONCEPT.csv, data/RELATIONSHIP.csv, data/CONCEPT_RELATIONSHIP.csv existen

def load_concept_data() -> pd.DataFrame
    # Cargar CONCEPT.csv con filtro de vocabularios
    # Columnas: concept_id, concept_name, vocabulary_id, domain_id, standard_concept
    # Retornar DataFrame con ~500k-1M conceptos (reducido de ~5M)

def load_relationship_mapping() -> dict
    # Cargar RELATIONSHIP.csv
    # Filtrar solo relaciones relevantes
    # Retornar dict: {relationship_id: relationship_name}

def load_concept_relationships(valid_concept_ids: set, valid_relationship_ids: set) -> pd.DataFrame
    # Cargar CONCEPT_RELATIONSHIP.csv por CHUNKS
    # Filtrar por valid_concept_ids y valid_relationship_ids en cada chunk
    # Mapear relationship_id → relationship_name
    # Retornar DataFrame: [concept_id_1, relationship_name, concept_id_2]

def preprocess() -> tuple[pd.DataFrame, pd.DataFrame]
    # Orquestar todo el proceso
    # Guardar nodes.csv y edges.csv
    # Retornar (nodes_df, edges_df)

if __name__ == '__main__':
    # Ejecutar preprocessing y mostrar estadísticas
```

**Relaciones a incluir (whitelist)**:
```python
RELEVANT_RELATIONSHIPS = {
    'Maps to',                # NO-ESTÁNDAR → ESTÁNDAR (CRÍTICO)
    'Mapped from',            # Inverso
    'Is a',                   # Jerarquías
    'Subsumes',
    'RxNorm is a',
    'RxNorm inverse is a',
    'RxNorm has ing',         # Ingredientes
    'RxNorm ing of',
    'Has form',               # Formas farmacéuticas
    'Form of',
    'RxNorm has dose form',
    'RxNorm dose form of',
    'Contains',               # Composición
    'Contained in',
    'Has tradename',          # Nombres comerciales
    'Tradename of',
}
```

---

### 2. graph.py (~200 líneas)

**Funciones**:
```python
def validate_graph_files() -> None
    # Verificar que nodes.csv y edges.csv existen

def load_nodes() -> pd.DataFrame
    # Cargar nodes.csv

def load_edges() -> pd.DataFrame
    # Cargar edges.csv

def build_graph(nodes_df: pd.DataFrame, edges_df: pd.DataFrame) -> nx.MultiDiGraph
    # Crear MultiDiGraph
    # Añadir nodos con atributos: concept_name, vocabulary_id, domain_id, standard_concept
    # Añadir aristas dirigidas con atributo: relationship

def get_concept_info(G: nx.MultiDiGraph, concept_id: int) -> dict
    # Retornar info del concepto
    # {concept_id, concept_name, vocabulary_id, domain_id, standard_concept}

def get_neighbors(G: nx.MultiDiGraph, concept_id: int, max_neighbors: int = 10) -> list[dict]
    # Obtener vecinos 1-hop (incoming + outgoing)
    # Retornar lista de: {relationship, direction, target_id, target_name, ...}

def find_standard_mapping(G: nx.MultiDiGraph, concept_id: int) -> dict | None
    # NUEVO - Función clave para el PoC
    # Si el concepto ya es estándar, retornar su info
    # Si no, seguir cadena "Maps to" hasta encontrar concepto estándar
    # Retornar concepto estándar encontrado o None

def load_graph() -> nx.MultiDiGraph
    # Función principal: validar, cargar, construir
    # Retornar grafo listo para usar

if __name__ == '__main__':
    # Cargar grafo y mostrar estadísticas
    # Ejemplo de uso con conceptos de prueba
```

---

### 3. tests/test_preprocess.py (~150 líneas)

**Tests**:
```python
def test_validate_input_files_success()
    # Verificar que los archivos reales existen

def test_validate_input_files_missing()
    # Simular archivo faltante → debe lanzar FileNotFoundError

def test_load_concept_data()
    # Cargar CONCEPT real
    # Verificar que solo contiene SNOMED, RxNorm, LOINC
    # Verificar que tiene columnas correctas
    # Verificar que filtra correctamente

def test_load_relationship_mapping()
    # Cargar RELATIONSHIP
    # Verificar que contiene relaciones esperadas
    # Verificar formato de dict

def test_load_concept_relationships()
    # Cargar CONCEPT_RELATIONSHIP con subset de IDs válidos
    # Verificar que filtra correctamente
    # Verificar que mapea relationship_id → name

def test_preprocess_full_pipeline()
    # Ejecutar preprocess() completo
    # Verificar que genera nodes.csv y edges.csv
    # Verificar tamaños razonables

def test_preprocess_generates_valid_nodes()
    # Verificar estructura de nodes.csv
    # Verificar no hay nulls en concept_name

def test_preprocess_generates_valid_edges()
    # Verificar estructura de edges.csv
    # Verificar que todos concept_id_1 y concept_id_2 existen en nodes

def test_empty_concept_file()
    # Edge case: CSV vacío

def test_invalid_vocabulary()
    # Edge case: Vocabulario no existente en filtro
```

---

### 4. tests/test_graph.py (~150 líneas)

**Tests**:
```python
def test_validate_graph_files_success()
    # Después de ejecutar preprocess, archivos deben existir

def test_validate_graph_files_missing()
    # Archivos faltantes → FileNotFoundError

def test_build_graph()
    # Construir grafo con datos reales
    # Verificar que es MultiDiGraph
    # Verificar número de nodos > 0

def test_get_concept_info_exists()
    # Buscar concepto conocido (ej: Metformin)
    # Verificar que retorna dict con campos correctos

def test_get_concept_info_not_exists()
    # Concepto inexistente → retornar None o {}

def test_get_neighbors_with_relationships()
    # Concepto con vecinos
    # Verificar que retorna lista con relaciones

def test_get_neighbors_isolated_node()
    # Edge case: Concepto sin relaciones

def test_find_standard_mapping_already_standard()
    # Concepto ya estándar → retornar el mismo

def test_find_standard_mapping_non_standard()
    # Concepto no estándar con "Maps to"
    # Verificar que sigue la cadena hasta estándar

def test_find_standard_mapping_no_mapping()
    # Edge case: No estándar sin "Maps to" → None

def test_load_graph_full()
    # Cargar grafo completo
    # Verificar estadísticas (nodos, aristas)
```

---

## MODIFICACIONES A ARCHIVOS EXISTENTES

### README.md
- Actualizar `raw/` → `data/` en todas las referencias
- Actualizar instrucciones de setup

### context/ARCHITECTURE.md
- Actualizar `raw/` → `data/` en diagramas y paths
- Documentar función `find_standard_mapping()` nueva

---

## ESTIMACIÓN DE TIEMPO

| Tarea | Tiempo | Complejidad |
|-------|--------|-------------|
| preprocess.py | 2-3h | Media-Alta |
| graph.py | 1-2h | Media |
| test_preprocess.py | 1h | Baja |
| test_graph.py | 1h | Baja |
| Actualizar docs | 30min | Baja |
| Testing con datos reales | 1-2h | Media |
| **TOTAL** | **6-9 horas** | |

---

## CONSIDERACIONES TÉCNICAS

### Manejo de memoria (preprocess.py):
```python
# Lectura de CONCEPT con optimización
df = pd.read_csv(
    'data/CONCEPT.csv',
    sep='\t',
    usecols=['concept_id', 'concept_name', 'vocabulary_id', 'domain_id', 'standard_concept'],
    dtype={'concept_id': 'int32'},
    on_bad_lines='skip'
)

# Filtrar vocabularios
df = df[df['vocabulary_id'].isin(['SNOMED', 'RxNorm', 'LOINC', 'RxNorm Extension'])]

# Procesamiento por chunks de CONCEPT_RELATIONSHIP
chunks = []
for chunk in pd.read_csv('data/CONCEPT_RELATIONSHIP.csv', sep='\t', chunksize=500000):
    # Filtrar en cada chunk
    filtered = chunk[
        chunk['concept_id_1'].isin(valid_ids) &
        chunk['concept_id_2'].isin(valid_ids) &
        chunk['relationship_id'].isin(valid_rel_ids)
    ]
    chunks.append(filtered)

edges_df = pd.concat(chunks, ignore_index=True)
```

### Estructura del grafo (graph.py):
```python
G = nx.MultiDiGraph()

# Añadir nodos
for _, row in nodes_df.iterrows():
    G.add_node(
        row['concept_id'],
        concept_name=row['concept_name'],
        vocabulary_id=row['vocabulary_id'],
        domain_id=row['domain_id'],
        standard_concept=row['standard_concept']
    )

# Añadir aristas
for _, row in edges_df.iterrows():
    G.add_edge(
        row['concept_id_1'],
        row['concept_id_2'],
        relationship=row['relationship_name']
    )
```

---

## CRITERIOS DE ÉXITO

- [ ] preprocess.py genera nodes.csv y edges.csv sin errores de memoria
- [ ] nodes.csv contiene solo SNOMED/RxNorm/LOINC, tanto estándar como no estándar
- [ ] edges.csv contiene solo relaciones de la whitelist
- [ ] graph.py carga el grafo en < 30 segundos
- [ ] `find_standard_mapping()` mapea correctamente términos no estándar → estándar
- [ ] Todos los tests pasan (expected, edge, failure cases)
- [ ] Documentación actualizada con paths correctos

---

## NEXT STEPS (después de Fase 1)

Una vez completada la Fase 1:
- **Fase 2**: Implementar embeddings.py (sentence-transformers)
- **Fase 3**: Implementar retrieve.py (búsqueda semántica + expansión grafo)
- **Fase 4**: Implementar main.py (CLI interactivo)
