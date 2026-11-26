# SCRUM-317 · HU: Crear esqueleto del backend FastAPI y contratos de API

| | |
|---|---|
| Responsable (Jira) | Tulio Riaño |
| Estado Jira | Finalizado |
| Repositorio | `Lumio` (backend) |
| Commits | 11 (2026-10-23 → 2026-10-26) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como equipo de desarrollo, queremos un esqueleto del backend con contratos de API definidos para
> que iOS y backend avancen en paralelo.

**Criterios de aceptación**
- Repositorio FastAPI con monolito modular: `users`, `voice`, `vision-orchestration`, `narration`, `places`.
- Contratos de request y response con Pydantic, agnósticos del cliente.
- OpenAPI publicada como referencia para iOS.
- Endpoint de salud y configuración por entorno.
- Pruebas en CI.
- Contratos para el estado de la ruta activa y el historial, persistidos en el backend.

## Prompts

### Prompt 1 · Configuración del proyecto (commit `0180147`)

```text
Vamos a crear el backend de Lumio en Python con FastAPI, como monolito modular. Empieza por la
configuración del proyecto:
- pyproject.toml con ruff (line-length 100, reglas E,F,I,UP,B) y pytest (testpaths = tests);
- requirements.txt con fastapi, uvicorn[standard], pydantic-settings, SQLAlchemy 2, psycopg 3,
  alembic, argon2-cffi, PyJWT, httpx y pytest;
- .env.example con ENVIRONMENT, DATABASE_URL, TEST_DATABASE_URL y JWT_SECRET (valor de ejemplo
  claramente inseguro). Nada de secretos reales.
```

### Prompt 2 · Núcleo: settings, base de datos y seguridad (commit `74363b8`)

```text
Crea app/core con:
- config.py: Settings con pydantic-settings leyendo .env; environment (local/dev/prod),
  database_url, jwt_secret, jwt_algorithm="HS256", access_token_minutes=15,
  refresh_token_days=30. Un get_settings() cacheado.
- db.py: engine y SessionLocal de SQLAlchemy 2, Base declarativa y la dependencia get_db().
- security.py: hash_password / verify_password con argon2 (PasswordHasher) y
  create_access_token / decode_token con PyJWT. verify_password devuelve False ante un hash
  inválido en lugar de lanzar.
```

### Prompt 3 · Esqueleto de módulos y modelo de usuarios (commit `847436a`)

```text
Crea app/modules con un paquete por módulo: users, voice, vision_orchestration, narration y
places. Cada uno con su router.py (APIRouter con prefijo y tag). En users agrega models.py
(User: id UUID, email único en minúsculas, password_hash, created_at), repository.py,
schemas.py y service.py vacíos pero con la responsabilidad de cada capa documentada.
Inicializa Alembic (alembic.ini, env.py leyendo DATABASE_URL de Settings y Base.metadata).
Crea también tests/modules/<módulo>/__init__.py para cada uno.
```

### Prompt 4 · Entrada FastAPI y salud (commit `a799240`)

```text
Crea app/main.py con la app FastAPI, incluye todos los routers y un GET /health que responda
{"status": "ok", "environment": <env>}. Agrega tests/conftest.py con un TestClient y
tests/test_health.py que compruebe el 200 y el cuerpo.
```

### Prompt 5 · Contratos Pydantic y endpoints stub (commit `a12c1f8`)

```text
Define los contratos de todos los módulos con Pydantic v2 en cada schemas.py, pensados para que
el cliente iOS los consuma sin saber nada de la base:
- users: registro, login, tokens, perfil.
- places: ActiveRoute (destino, coordenadas, pasos, distancia, duración, estado) e historial.
- voice, vision_orchestration y narration: request/response mínimos.
En cada router agrega los endpoints con su response_model. Los que todavía no tienen lógica
deben responder 501 Not Implemented con un detail claro, no datos falsos.
Escribe tests/test_schemas.py que valide ejemplos válidos e inválidos de cada contrato.
```

### Prompt 6 · Modelo de rutas y primera migración (commit `6f10f71`)

```text
Agrega app/modules/places/models.py con la tabla de rutas (usuario, destino, coordenadas de
origen y destino, pasos en JSON, estado activo/completado/cancelado, started_at, finished_at).
Registra los modelos en alembic/env.py y crea la migración
alembic/versions/0001_create_users_and_routes.py con users y routes. Comprueba que
`alembic upgrade head` y `alembic downgrade base` funcionan.
```

### Prompt 7 · Metadatos OpenAPI y pruebas de contrato (commit `10167c5`)

```text
Completa los metadatos de OpenAPI en main.py (título Lumio API, versión, descripción y tags por
módulo) para que /docs sirva de referencia al equipo iOS. Agrega tests/test_openapi.py que
compruebe que el esquema publica las rutas esperadas de cada módulo y los nombres de los schemas.
```

### Prompt 8 · CI con ruff y pytest (commit `d45fa8e`)

```text
Crea .github/workflows/ci.yml: en push y pull_request, Python 3.12, instalar requirements,
`ruff check .` y `pytest`. Que falle si alguno falla.
```

### Prompt 9 · Pruebas de seguridad y fixtures compartidas (commits `b62580a`, `ee7c9b7`)

```text
Escribe tests/test_security.py: el hash no es la contraseña, verify acepta la correcta y
rechaza la incorrecta y un hash corrupto, el JWT lleva sub y exp y un token vencido o firmado
con otro secreto no se acepta. Si algo de security.py no es testeable, ajústalo.
Luego mueve las fixtures de usuario repetidas en test_login, test_logout, test_me y test_refresh
a tests/modules/users/conftest.py.
```

### Prompt 10 · Documentación (commit `2b90065`)

```text
Escribe el README del backend: cómo levantarlo (venv, requirements, .env, Postgres, alembic
upgrade head, uvicorn), cómo correr las pruebas, dónde ver /docs y el flujo de autenticación
(registro, login, access token de 15 min, refresh de 30 días con rotación, logout).
```

## Verificación final

- `ruff check .` y `pytest` pasan en local y en CI.
- `/health` responde y `/docs` publica todos los módulos.
- Los módulos sin lógica responden 501 (voice, vision_orchestration, narration).

## Commits cubiertos

| Commit | Fecha | Mensaje |
|---|---|---|
| `0180147` | 2026-10-23 | Add project config, dependencies and env template |
| `74363b8` | 2026-10-23 | Add core settings, database and security modules |
| `847436a` | 2026-10-23 | Add modular monolith skeleton and users model |
| `a799240` | 2026-10-23 | Add FastAPI entrypoint with health endpoint and test |
| `a12c1f8` | 2026-10-23 | Add Pydantic contracts and stub endpoints for all modules |
| `6f10f71` | 2026-10-23 | Add routes model and initial Alembic migration |
| `10167c5` | 2026-10-23 | Add OpenAPI metadata and contract tests |
| `d45fa8e` | 2026-10-23 | Add CI workflow with ruff and pytest |
| `b62580a` | 2026-10-26 | Add security helper tests |
| `ee7c9b7` | 2026-10-26 | Share user test fixtures |
| `2b90065` | 2026-10-26 | Document setup and auth flow in README |
