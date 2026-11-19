# Reglas de Git y Entregas en Axioma

- **Commits atómicos por funcionalidad:** Cada vez que implementes o corrijas una funcionalidad, función o conjunto cohesivo de archivos relacionados y verifiques que funciona, crea un commit atómico que agrupe únicamente esos archivos relacionados.
- **Formato de mensajes de commit (Conventional Commits en español):** Todos los mensajes de commit deben usar los prefijos convencionales (`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `style:`, `perf:`, `ci:`, con alcance opcional como `feat(mobile): ...` o `fix(backend): ...`) y redactarse **siempre en español** (ej. `feat(mobile): agregar pantalla de perfil`, `fix(backend): corregir balanceo químico con hidratos`).
- **No acumular trabajo sin commitear:** No dejes cambios completados y verificados sin commitear al finalizar una tarea. Si una solicitud incluye múltiples funcionalidades independientes, sepáralas en commits lógicos distintos antes de subirlos.
- **Push inmediato a la rama remota:** Después de cada commit verificado, ejecuta `git push` a la rama remota actual (`origin/<rama>`).
- **Guardrails obligatorios antes de commitear:**
  1. Verifica primero con `pytest`, `npm run typecheck` o la comprobación pertinente según los archivos modificados.
  2. Revisa `git status` antes de hacer `git add` y **nunca** incluyas archivos sensibles o generados (`.env`, `.venv/`, `node_modules/`, claves o credenciales).
  3. Ten en cuenta que los cambios subidos en `backend/` a `main` disparan automáticamente un nuevo despliegue en Vercel.
