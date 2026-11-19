# Axioma

Aplicación móvil multiplataforma (**Android / iOS**) para resolver problemas de **Matemáticas, Física, Química e Ingeniería** a partir de texto, fórmulas LaTeX o fotografías.

## Arquitectura

- **`mobile/`**: App en React Native + Expo + TypeScript, renderizado LaTeX con KaTeX y autenticación/almacenamiento con Supabase.
- **`backend/`**: API en Python 3.13 + FastAPI que combina **Google Gemini** (comprensión multimodal y explicación paso a paso) con motores deterministas (**SymPy, NumPy y Pint**), optimizada para despliegue sin costo en **Vercel Hobby**.
- **`supabase/`**: Migraciones PostgreSQL con Row-Level Security (RLS), control atómico de cuota diaria (`free` vs `pro`) y bucket privado `problem-images`.

## Modelo Freemium

- **Plan Free**: Hasta **5 resoluciones diarias** + resultado final verificado.
- **Axioma Pro**: Resoluciones **ilimitadas**, explicación **paso a paso completa**, **gráficas 2D** y almacenamiento en historial.

## Puesta en marcha local

### 1. Backend (Python 3.13)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
# Completa GEMINI_API_KEY y SUPABASE_SERVICE_ROLE_KEY en .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Pruebas automatizadas del backend:

```bash
cd backend
pytest -v
```

### Despliegue gratuito en Vercel (`backend/`)

El backend incluye `backend/vercel.json`, `backend/.python-version` y `backend/requirements.txt` aligerado para desplegar en **Vercel Hobby (\$0)** configurando `Root Directory` = `backend` y definiendo las variables de entorno en Vercel (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `FREE_DAILY_LIMIT`, `ENVIRONMENT`, `ALLOWED_ORIGINS`).

### 2. App Móvil (Expo)

```bash
cd mobile
npm install
copy .env.example .env
npx expo start
```
