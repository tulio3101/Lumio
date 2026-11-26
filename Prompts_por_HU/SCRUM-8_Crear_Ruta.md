# SCRUM-8 · HU: Crear Ruta

| | |
|---|---|
| Responsable (Jira) | Daniel Patiño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 22 (9 backend, 13 iOS; 2026-11-08) |
| Rama | `SCRUM-8-hu-crear-ruta` |
| Depende de | SCRUM-313 (destino por voz, aún pendiente), SCRUM-43/45 (árbitro de audio) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero indicar un destino y obtener una ruta peatonal para desplazarme hasta
> él con asistencia de navegación.

**Criterios de aceptación**
- El usuario indica el destino por voz (SCRUM-313).
- Se obtiene la ubicación actual.
- El destino confirmado se convierte en una ubicación válida.
- Se calcula una ruta peatonal entre la ubicación actual y el destino.
- Se generan instrucciones paso a paso como mensajes de navegación (prioridad 2).
- La ruta activa se guarda en una copia local y se persiste en el backend.
- Se informa por audio cuando la ruta está lista, o que no hay ruta disponible.

## Prompts · Backend

### Prompt 1 · Modelo de la ruta activa (commit `ce95d31`)

```text
Vamos con Crear Ruta (SCRUM-8). El cálculo lo hace el teléfono con MapKit; el backend solo
guarda la ruta que el teléfono ya calculó. En app/modules/places:
- models.py: la ruta ya tiene origin, destination y steps en JSON, current_step, status,
  started_at y finished_at. Agrega los campos de resumen distance_meters y
  expected_travel_time_seconds.
- Restricciones en la base: CHECK de status (active, paused, completed, cancelled), CHECK
  current_step >= 0 y el índice único parcial uq_routes_one_open_per_user sobre user_id cuando
  la ruta está abierta (active o paused): cada usuario tiene como máximo una.
- schemas.py: ActiveRouteCreate y ActiveRoute con validación (lat/lon en rango, distancia y
  duración no negativas, al menos un paso).
- migración 0002_active_route_constraints.py con su downgrade.
```

### Prompt 2 · Errores uniformes e identificación provisional (commit `31bbf29`)

```text
Quiero que todos los errores propios del backend tengan el mismo formato para que la app los
locute: {"detail": <mensaje en español>, "code": <identificador>}. Crea app/core/errors.py con
una excepción base con status, code y detail, y regístrala en main.py. Crea
places/exceptions.py (active_route_not_found, etc.). Mientras el login no está en develop,
identifica al usuario con el header X-User-Id (UUID de un usuario existente) en
users/dependencies.py; 401 si falta o no existe.
```

### Prompt 3 · Endpoints de ruta activa (commit `618dd1c`)

```text
Implementa en places:
- PUT /places/routes/active: guarda la ruta que manda el teléfono; si había una abierta, la
  cancela (deja de ser activa y pasa al historial) en la misma transacción.
- GET /places/routes/active: ruta activa o pausada del usuario; 404 active_route_not_found.
Separa router, service y repository. Agrega app/scripts/seed_dev_user.py, que crea un usuario de
desarrollo e imprime su UUID para LumioDevUserID. Actualiza test_openapi.
```

### Prompt 4 · Pruebas unitarias (commit `5fd3511`)

```text
Escribe pruebas unitarias sin base de datos: tests/factories.py para armar rutas válidas,
tests/modules/places/fakes.py con un repositorio en memoria, y test_schemas, test_service y
test_router de places, además de test_dependencies para X-User-Id (falta, inválido, inexistente).
```

### Prompt 5 · Integración con Postgres en CI (commit `0be01cf`)

```text
Agrega tests/integration con su conftest (TEST_DATABASE_URL, migraciones con Alembic, vaciar
tablas) y dos suites: test_active_route_api (crear, consultar, reemplazar la abierta, 404) y
test_route_persistence (la restricción de una sola ruta abierta en la base). En ci.yml levanta
un servicio postgres:16 con healthcheck pg_isready y corre `pytest -rs` con TEST_DATABASE_URL.
Marca las de integración para que se omitan si no hay base.
```

### Prompt 6 · Docker para probar desde el iPhone (commits `b5867d2`, `1aa0fca`)

```text
Quiero probar la app en un iPhone contra mi portátil. Crea Dockerfile y docker-compose.yml con
la API y Postgres 16; docker/api/entrypoint.sh que aplica `alembic upgrade head` y arranca
uvicorn en 0.0.0.0:8000; docker/postgres/create-test-database.sql que crea lumio_test.
Documenta en el README: docker compose up, el seed del usuario de desarrollo, cómo usar la IP
del equipo en LumioAPIBaseURL, abrir el puerto 8000 y comprobar /health desde Safari.
```

### Prompt 7 · Reparar el merge con develop (commit `f3f218a`)

```text
Al mezclar develop entró la migración 0002_create_auth_sessions de SCRUM-2 y choca con mi
0002_active_route_constraints; además el merge borró helpers de auth en users/dependencies.py y
users/repository.py. Renumera la mía a 0003 (down_revision a la de sesiones), restaura los
helpers y comprueba que `alembic upgrade head` funciona desde cero.
```

## Prompts · iOS

### Prompt 8 · Modelo y contratos (commit `00ed7b0`)

```text
En la app, en Features/Navigation/Domain, define ActiveRoute (id local, remoteID opcional,
destino, origen, pasos con instrucción, distancia y coordenada de maniobra, distancia total,
duración, currentStep, revisión, createdAt) y NavigationContracts con los puertos:
CurrentLocationProviding, DestinationGeocoding, WalkingRouteCalculating, ActiveRouteStoring,
ActiveRouteSyncing, RouteCreating y DestinationRequest (.query(texto) | .place(lugar)).
```

### Prompt 9 · Instrucciones habladas P2 (commit `c0fc413`)

```text
Crea NavigationInstructions.swift con NavigationInstructionBuilder: normaliza los pasos de
MapKit al español (quita pasos vacíos, redondea distancias, «En 50 metros, gira a la
derecha en…») y crea un AudioMessage P2 por paso con contextID por ruta (route-<id>) y clave
de deduplicación step-<n>, más los mensajes «Ruta lista hacia X» y la primera instrucción.
```

### Prompt 10 · Ubicación actual (commit `40882cf`)

```text
Implementa CoreLocationCurrentLocationProvider: pide permiso «cuando se usa la app» si no está
decidido, hace una lectura nueva (no una cacheada vieja), exige precisión razonable y traduce
denegado, restringido, servicios apagados y timeout a errores propios. Agrega
NSLocationWhenInUseUsageDescription en Info.plist y project.yml con un texto que explique para
qué se usa.
```

### Prompt 11 · Geocodificar y calcular con MapKit (commit `4b93bba`)

```text
En MapKitNavigationAdapters.swift implementa MapKitDestinationGeocoder (MKLocalSearch con la
región cerca del usuario, primer resultado relevante; sin resultados = destino no encontrado) y
MapKitWalkingRouteCalculator (MKDirections con transportType .walking; sin rutas = sin ruta
disponible). Convierte MKRoute a los pasos del dominio.
```

### Prompt 12 · Copia local y persistencia en el backend (commit `bb5de5a`)

```text
- Core/Configuration/AppConfiguration: lee LumioAPIBaseURL y LumioDevUserID del Info.plist.
- FileActiveRouteStore: guarda la ruta activa en JSON en Application Support (escritura atómica).
- ActiveRouteDTO + RemoteActiveRouteService: PUT /places/routes/active con el header X-User-Id
  provisional y guarda el remoteID devuelto.
La ruta está lista en cuanto existe la copia local: si el backend falla, queda pendiente
(remoteID nil) y no se bloquea la guía.
```

### Prompt 13 · Orquestar y anunciar (commit `a922845`)

```text
Crea RouteCreationService: ubicación → geocodificar → calcular → construir instrucciones →
guardar copia local → anunciar por el árbitro «Ruta lista…» + primera instrucción (P2) con
háptica de éxito → sincronizar con el backend en segundo plano. Cada fallo es un
RouteCreationError (sin permiso, sin ubicación, destino no encontrado, sin ruta, error al
guardar) con su texto en RouteAnnouncements, locutado por el servicio, nunca desde la vista.
Agrega UIKitHapticFeedback.
```

### Prompt 14 · Pantallas (commit `94b7e70`)

```text
Conecta todo en DestinationView, RoutePlannerView y ActiveRouteView con un DestinationViewModel
compartido:
- DestinationView: una acción principal según haya ruta activa o no.
- RoutePlannerView: campo de destino con sugerencias (MapKitDestinationSuggester con
  MKLocalSearchCompleter: 0,3 s después de la última tecla, mínimo 3 letras, máximo 5). Elegir
  una sugerencia envía .place; si no se puede ubicar, su texto va como .query.
- ActiveRouteView: resumen, estado de guardado y pasos como línea de tiempo.
El ViewModel clasifica cada fallo por la salida (corregir destino, abrir Ajustes, reintentar)
para mostrar el botón adecuado. Al volver a la pantalla, restoreActiveRoute() reintenta subir la
ruta pendiente. Agrega componentes comunes a LumioComponents y LumioTheme. En SwiftPM usa
UnavailableNavigationService.
```

### Prompt 15 · Pruebas (commits `e5d79cf`, `f30debb`)

```text
Escribe con dobles de prueba (NavigationTestDoubles): RouteCreationServiceTests (cada fallo y su
anuncio, ruta pendiente si falla el backend), NavigationInstructionTests, ActiveRoutePersistenceTests
(guardar/leer/borrar, archivo dañado) y DestinationSuggestionTests (espera, mínimo, máximo).
Después RouteCreationIntegrationTests con el AudioArbiterService real y un reproductor falso:
se oye «Ruta lista» y luego la primera instrucción, y un fallo se oye una sola vez.
```

### Prompt 16 · Documentación e ícono (commits `4807e61`, `657343b`, `5add182`, `8c027f6`, `bce2557`)

```text
Documenta en docs/ARCHITECTURE.md el flujo de Crear Ruta (pantallas, adaptadores, orden de pasos,
qué pasa si falla el backend) y los contratos para SCRUM-313 y SCRUM-312. En el README explica
LumioAPIBaseURL y LumioDevUserID. Por último, ajusta el AppIcon a 1024×1024 sin transparencia.
```

## Verificación final

- Backend: `pytest -rs` con Postgres en CI; `docker compose up` y `/health` desde el iPhone.
- iOS: `swift test` y en el iPhone crear una ruta a un lugar cercano: se oye «Ruta lista» y la
  primera instrucción; en modo avión la ruta queda pendiente y se sube al volver.
- **Pendiente:** el destino todavía se escribe; el dictado es SCRUM-313 (Por hacer).

## Commits cubiertos

| Commit | Repo | Mensaje |
|---|---|---|
| `ce95d31` | Lumio | Add route summary fields and active route constraints |
| `31bbf29` | Lumio | Add uniform error responses and provisional user identification |
| `618dd1c` | Lumio | Implement endpoints to start and get the active route |
| `5fd3511` | Lumio | Add unit tests for active route contract, service and API |
| `0be01cf` | Lumio | Add Postgres integration tests and run them in CI |
| `b5867d2` | Lumio | Dockerize API and database for local testing |
| `1aa0fca` | Lumio | Document Docker setup, dev user and test commands |
| `657343b` | Lumio | Lumio Branding |
| `f3f218a` | Lumio | Fix develop merge restoring auth helpers and renumbering route migration |
| `00ed7b0` | LumioFrontend | Add active route model and route creation contracts |
| `c0fc413` | LumioFrontend | Generate spoken step-by-step instructions as priority 2 messages |
| `40882cf` | LumioFrontend | Get current user location with CoreLocation |
| `4b93bba` | LumioFrontend | Geocode destination and calculate walking route with MapKit |
| `bb5de5a` | LumioFrontend | Store active route locally and persist it in the backend |
| `a922845` | LumioFrontend | Orchestrate route creation and announce result or failure |
| `94b7e70` | LumioFrontend | Connect route creation to trip, planner and route screens |
| `e5d79cf` | LumioFrontend | Add unit tests for route creation, instructions, persistence and suggestions |
| `f30debb` | LumioFrontend | Add integration tests for route creation with audio arbiter |
| `4807e61` | LumioFrontend | Document route creation flow and backend configuration |
| `5add182` | LumioFrontend | App icon resized |
| `8c027f6` | LumioFrontend | App icon deleted |
| `bce2557` | LumioFrontend | App icon restored and resized |
