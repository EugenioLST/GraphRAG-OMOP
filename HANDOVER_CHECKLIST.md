# Checklist de traspaso — antes del último día

> Fichero temporal de quien hace el traspaso. **Borrarlo en el último commit**, cuando todo esté marcado.

Orden recomendado. Cada punto dice qué, dónde y a quién avisar.

## A. Repo (hacer aquí, en este orden)

- [ ] **Actualizar la URL de clonado** en README, sección "Instalación", cuando exista el proyecto en GitLab.



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
| **Eugenio** | URL GitLab, que es Owner, que los datos se regeneran (README), que lea `HANDOVER.md`, confirmar licencia MIT (`LICENSE`) | Al subir a GitLab |

## F. Último día

- [ ] `git status` limpio en ambos portátiles. Nada sin subir.
- [ ] `backend/.env` borrado en ambos.
- [ ] Key de OpenAI revocada.
- [ ] Eugenio ha confirmado acceso a GitLab y a los datos.
- [ ] `git rm HANDOVER_CHECKLIST.md` y último commit.
