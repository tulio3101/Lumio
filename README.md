# Lumio
Lumio is an application that uses a modular monolithic architecture, aiming to provide support and foster independence for individuals with severe visual impairments. This is a project for the course "Software Innovation Supported by New Technologies" (2026-2).

## Desarrollo

```bash
python -m venv venv && source venv/bin/activate   # en Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                              # ajustar DATABASE_URL y JWT_SECRET
alembic upgrade head
uvicorn app.main:app --reload                     # OpenAPI en http://localhost:8000/docs
```

Pruebas y lint (no requieren PostgreSQL, usan SQLite en memoria):

```bash
pytest
ruff check .
```

## Autenticación

Cada inicio de sesión crea una sesión por dispositivo (`auth_sessions`); su id viaja como claim `jti` en el access y el refresh token.

- `POST /users` registra la cuenta; `POST /users/login` devuelve el par de tokens.
- `GET /users/me` y los endpoints protegidos exigen `Authorization: Bearer <access_token>`.
- `POST /users/refresh` rota la sesión: el refresh token usado deja de ser válido.
- `POST /users/logout` revoca la sesión y con ello ambos tokens.
- Login con Google y recuperación de contraseña siguen pendientes (501).
