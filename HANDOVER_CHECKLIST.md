# Checklist de traspaso — antes del último día

> Fichero temporal de quien hace el traspaso. **Borrarlo en el último commit**, cuando todo esté marcado.

Orden recomendado. Cada punto dice qué, dónde y a quién avisar.

## A. Repo (hacer aquí, en este orden)

- [ ] **Rellenar la versión de Athena** en README, sección "Generar Datos", Paso 1, desde el
      portátil de trabajo (`backend/data/source/VOCABULARY.csv`, fila `None`, columna `vocabulary_version`).
- [ ] **Actualizar la URL de clonado** en README, sección "Instalación", cuando exista el proyecto en GitLab.

## B. Datos (portátil de trabajo)

- [ ] **Copiar `backend/data/` (28 GB) a almacenamiento del grupo.** Preguntar a Eugenio dónde
      (NAS del LST, OneDrive UPM, disco). Verificar que contiene `source/`, `processed/`
      (`nodes.csv`, `edges.csv`, `omop_graph.pkl`) y `embeddings/` (`embeddings.npy`,
      `faiss_index.bin`, `concept_id_to_index.pkl`). Anotar la ruta final en `HANDOVER.md` §2.
- [ ] **Borrar `backend/.env` del portátil de trabajo** antes de devolverlo. Contiene tu key.


## D. GitHub → GitLab (lo hace quien migra)

- [ ] Crear el proyecto en el GitLab del grupo (namespace del LST, **no el personal**).
      Visibilidad: privada/interna, según Eugenio.
- [ ] Subir todo, incluyendo historial. Si se reescribe el historial, hacerlo antes.

```bash
git remote rename origin github
git remote add origin <URL-GITLAB>
git push -u origin main
```

- [ ] **Permisos:** en GitLab, Project → Members → añadir a **Eugenio como Owner**. Después,
      bajar tu rol a Maintainer o quitarte. El proyecto debe sobrevivir a la baja de tu cuenta:
      si el proyecto está en un grupo del LST y Eugenio es Owner del grupo, está resuelto.
- [ ] Comprobar desde otra cuenta (o pedírselo a Eugenio) que ve el repo y `HANDOVER.md`.
- [ ] GitHub: dejar el repo privado como está o archivarlo (Settings → Archive). No borrarlo hasta
      que Eugenio confirme que GitLab está completo.

## E. Avisar

| A quién | Qué | Cuándo |
|---|---|---|
| **Eugenio** | URL GitLab, que es Owner, dónde están los 28 GB, que lea `HANDOVER.md`, confirmar licencia MIT (`LICENSE`) | Al subir a GitLab |

## F. Último día

- [ ] `git status` limpio en ambos portátiles. Nada sin subir.
- [ ] `backend/.env` borrado en ambos.
- [ ] Key de OpenAI revocada.
- [ ] Eugenio ha confirmado acceso a GitLab y a los datos.
- [ ] `git rm HANDOVER_CHECKLIST.md` y último commit.
