### TASK CLAVE PARA EL FUTURO (no borrar, cualquier texto que generes, arriba de esto)

La clave para evaular este proyecto es evaluar los embeddings. Son los que generan los vectores, luego la búsqueda es matemática.

Por eso, necesitamos unos embeddings buenos. Tocará crear un dataset de evaluación con conceptos y estándares para que cada modelo de embedding sea evaluado.

Los LLMs aquí solo son para darle formato a la respuesta

Embeddings a probar o usar: 



# 🏆 **1. SapBERT (el mejor para terminología médica y ontologías)**

 **Especializado en UMLS / SNOMED / vocabularios clínicos** .

Es el embedding más adecuado para concept linking médico.

👉 **HuggingFace:**

[https://huggingface.co/cambridgeltl/SapBERT-from-PubMedBERT-fulltext](https://huggingface.co/cambridgeltl/SapBERT-from-PubMedBERT-fulltext)

(Autor: Cambridge Language Technology Lab)

**Por qué es el mejor para tu caso:**

* Entrenado específicamente en entidades biomédicas estándar
* Excelente en normalización de conceptos
* Entiende sinónimos clínicos
* Superior a modelos generales en tareas UMLS, SNOMED, RxNorm

---

# ⭐ **2. BioBERT / PubMedBERT — embeddings biomédicos generales**

Modelos entrenados en PubMed.

No son tan buenos como SapBERT en ontologías, pero mucho mejores que embeddings generalistas.

👉 **BioBERT Base v1.1 (HuggingFace):**

[https://huggingface.co/dmis-lab/biobert-base-cased-v1.1](https://huggingface.co/dmis-lab/biobert-base-cased-v1.1)

👉 **PubMedBERT (full-text):**

[https://huggingface.co/microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext]()

**Por qué usarlos:**

* Capturan vocabulario biomédico mejor que modelos generalistas
* Funcionan bien cuando los conceptos no están exactamente en SNOMED
* Robustez ante términos clínicos y síntomas

---

# ✔️ **3. All-MiniLM-L6-v2 (baseline generalista sorprendentemente robusto)**

Modelo pequeño, rápido y muy eficiente, ideal como baseline o fallback.

👉 **HuggingFace:**

[https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

**Cuándo usarlo:**

* Para comparar rendimiento con modelos biomédicos
* Para PoC rápidos
* Cuando quieres velocidad y carga ligera

**Advertencia:**

* Funciona bien con términos comunes
* Pero falla en casos clínicos especializados
* No entiende jerarquías médicas ni sinónimos complejos como SapBERT
