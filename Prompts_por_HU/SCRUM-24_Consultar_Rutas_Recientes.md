# SCRUM-24 · HU: Consultar Rutas Recientes

| | |
|---|---|
| Responsable (Jira) | Daniel Patiño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 11 (5 backend, 6 iOS; 2026-11-08) |
| Nota | En Confluence «Rutas recientes» figura fuera del MVP; en Jira está Finalizado. |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero consultar mis rutas recientes para revisar destinos usados
> anteriormente y poder reutilizarlos.

**Criterios de aceptación**
- Cada ruta finalizada se guarda siempre en el historial.
- Se consultan por voz o con VoiceOver.
- Se listan de la más reciente a la más antigua.
- Se puede elegir un destino del historial e iniciar con él una ruta nueva.
- Si no hay rutas recientes, se informa.

## Prompts · Backend

### Prompt 1 · Consulta del historial (commit `87ea108`)

```text
Agrega a places la consulta del historial: rutas completadas o canceladas del usuario (las
canceladas incluyen las que se reemplazaron al iniciar otra), ordenadas por finished_at
descendente, sin la ruta abierta. Paginación con limit y offset. En el modelo separa
CLOSED_ROUTE_STATUSES = ("completed", "cancelled") de los abiertos para reutilizarlo.
```

### Prompt 2 · Endpoint y pruebas (commits `6daae52`, `233b9ef`, `e0614dc`, `941817e`)

```text
Expón GET /places/routes/history?limit=20&offset=0 (limit 1–100, 422 fuera de rango) con un
schema RouteHistoryItem. Pruebas unitarias con el repositorio falso e integración en
tests/integration/test_route_history_api.py: orden, paginación, no incluye la abierta, solo las
del usuario, sin token 401. Actualiza test_openapi y el README.
```

## Prompts · iOS

### Prompt 3 · Destinos recientes (commit `e7e0a20`)

```text
Crea RecentRoutes.swift y RecentRoutesService (RecentRoutesQuerying). RecentRoutesPolicy.grouped
agrupa por lugar (mismo nombre sin mayúsculas ni tildes, a 25 m o menos) con la vez más reciente,
cómo terminó y cuántas veces se fue. Al abrir la pantalla locuta un resumen corto (contexto
recent-routes): cuántos destinos y el más reciente, o «No tienes rutas recientes».
```

### Prompt 4 · Traer del backend y guardar copia (commit `2c6065e`)

```text
Implementa RemoteRouteHistoryService (GET /places/routes/history?limit=50 con
AuthorizedHTTPClient) con un BackendDate que lea las fechas de Pydantic (Z o +00:00, con
microsegundos) y FileRecentRoutesStore, que guarda cada lista recibida. Sin backend se usa esa
copia (.savedCopy, avisando); sin copia, RecentRoutesError.unavailable. SignOutService borra la
copia al cerrar sesión.
```

### Prompt 5 · Pantalla y reutilizar un destino (commit `b58a375`)

```text
Crea RecentRoutesView: destinos con fecha, cómo terminó y cuántas veces, legibles con VoiceOver.
Elegir uno envía DestinationRequest.place (sin geocodificar otra vez) a Crear Ruta o, si hay
ruta activa, a Modificar Ruta. El destino de la ruta activa aparece sin poder elegirse. En
RoutePlannerView, con el campo vacío, muestra hasta 5 recientes. Agrega la entrada «Rutas
recientes» en DestinationView.
```

### Prompt 6 · Pruebas y documentación (commits `2cfc22b`, `664d085`, `9c5a8f2`)

```text
Escribe RecentRoutesTests (agrupación por nombre y distancia, orden, copia sin backend, sin copia)
y RecentRoutesIntegrationTests con sesión y árbitro reales: resumen al abrir, crear ruta desde un
reciente, cerrar sesión borra la copia. Documenta el flujo en docs/ARCHITECTURE.md y el README.
```

## Verificación final

- Backend: `pytest -rs` cubre orden, paginación y aislamiento por usuario.
- iOS: tras finalizar dos rutas, «Rutas recientes» las muestra; elegir una crea la ruta sin
  escribir; en modo avión se ve la copia guardada con aviso.

## Commits cubiertos

| Commit | Repo | Mensaje |
|---|---|---|
| `87ea108` | Lumio | Query the history of completed and cancelled routes |
| `6daae52` | Lumio | Implement the route history endpoint |
| `233b9ef` | Lumio | Add unit tests for the route history |
| `e0614dc` | Lumio | Add Postgres integration tests for the route history |
| `941817e` | Lumio | Document the route history endpoint |
| `e7e0a20` | LumioFrontend | Load recent destinations and say when there are none |
| `2c6065e` | LumioFrontend | Fetch the route history from the backend and keep a copy on the phone |
| `b58a375` | LumioFrontend | Show recent destinations and start a route from one |
| `2cfc22b` | LumioFrontend | Add unit tests for recent routes |
| `664d085` | LumioFrontend | Add integration tests for recent routes with session and audio |
| `9c5a8f2` | LumioFrontend | Document recent routes |
