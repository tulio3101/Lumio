# SCRUM-10 · HU: Finalizar Ruta

| | |
|---|---|
| Responsable (Jira) | Daniel Patiño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 13 (5 backend, 8 iOS; 2026-11-08) |
| Depende de | SCRUM-8, SCRUM-9, SCRUM-24 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero finalizar una ruta activa para detener el proceso de navegación cuando
> haya llegado a mi destino o ya no necesite asistencia.

**Criterios de aceptación**
- Se puede finalizar a mano una ruta activa.
- Se identifica la llegada al destino.
- Se detienen las instrucciones de navegación.
- La ruta deja de ser activa y se borra su copia local.
- Se informa por audio y háptica que terminó.
- La ruta finalizada se guarda siempre en el historial del backend.
- Sin red, el historial se sincroniza al volver la conexión.

## Prompts · Backend

### Prompt 1 · Cerrar rutas y guardar las finalizadas sin conexión (commit `4c6dbf7`)

```text
En places agrega dos operaciones:
- finish_route(route_id, status completed|cancelled, finished_at): cierra la ruta abierta del
  usuario con la hora del dispositivo, acotada entre started_at y ahora. Si ya estaba cerrada no
  cambia nada (idempotente). 404 route_not_found.
- save_finished_route(cuerpo de crear ruta + id, status, started_at, finished_at): para una ruta
  que se terminó sin conexión y nunca llegó al backend. No toca la ruta activa. Reenviar el mismo
  id no la duplica; si el id es de otro usuario, 409 route_id_conflict.
```

### Prompt 2 · Endpoints y pruebas (commits `49fc0aa`, `6d844fd`, `fff82f4`, `b7feb8c`)

```text
Expón POST /places/routes/{route_id}/finish y POST /places/routes/history. Pruebas unitarias
(acotar finished_at, idempotencia, conflicto) e integración en
tests/integration/test_route_finish_api.py (la ruta finalizada aparece en el historial y deja de
ser la activa; reenviar la misma offline no la duplica). Documenta ambos en el README.
```

## Prompts · iOS

### Prompt 3 · Cortar las instrucciones en el árbitro (commit `dca8b54`)

```text
Agrega a AudioArbitrating cancel(contextIDs:): detiene el mensaje que suena si es de esos
contextos y descarta los pendientes de ellos, sin tocar los demás (seguridad y narración siguen).
Pruebas con el doble de prueba.
```

### Prompt 4 · Finalizar y encolar hasta que llegue al historial (commit `2d18ce4`)

```text
Crea RouteFinishService (RouteFinishing) para los dos casos (a mano y llegada):
1. cancel(contextIDs:) del contexto de la ruta;
2. PendingHistorySyncing.enqueue y DESPUÉS ActiveRouteStoring.clear(), para que la ruta no se
   pierda si la app se cierra en medio;
3. anuncio (contexto route-finished) y HapticCue.routeFinished;
4. FinishedRouteSynchronizer.flush() sin esperar a la red.
Modela FinishedRoute. Crear y Modificar Ruta deben vaciar la cola antes de subir una ruta nueva
(si no, el backend cancelaría la anterior que sigue abierta), RecentRoutesService antes de leer
el historial, y SignOutService al cerrar sesión, descartando lo que no llegue.
```

### Prompt 5 · Detectar la llegada (commit `a874c8e`)

```text
Crea CoreLocationRouteTracker (lecturas continuas, también con el teléfono bloqueado gracias a
UIBackgroundModes = location) y ArrivalMonitor: finaliza como completed cuando dos lecturas
seguidas con precisión <= 20 m caen a <= 25 m del destino. Las imprecisas no cuentan ni
reinician; una precisa lejos reinicia; un cambio de destino también. Se activa al crear, cambiar
o restaurar la ruta y se detiene al finalizarla.
```

### Prompt 6 · Enviar al backend y reintentar al volver la red (commit `6b467e2`)

```text
Implementa FileFinishedRoutesStore (cola en orden en disco), RemoteFinishedRouteService y
Core/Networking/ConnectivityMonitor (NWPathMonitor). FinishedRouteSynchronizer: ruta con remoteID
→ POST /places/routes/{id}/finish (enviando antes un cambio de destino pendiente); sin remoteID,
404 o ya cerrada → POST /places/routes/history con el id del teléfono. Un fallo de red detiene la
cola; un 4xx definitivo o un id ajeno descarta esa ruta. Se vacía al abrir la app y al volver la
conexión.
```

### Prompt 7 · Interfaz (commit `a869809`)

```text
En ActiveRouteView agrega «Finalizar ruta» (y la acción de VoiceOver) que pide confirmar con
«Llegué a mi destino» (completed) o «Terminar sin llegar» (cancelled). Al terminar muestra
FinishedRouteView con el resumen. Agrega UIBackgroundModes location en Info.plist y conecta
ArrivalMonitor y el sincronizador en AppDependencies y RootView.
```

### Prompt 8 · Pruebas y documentación (commits `d725aea`, `3809bc8`, `90bdef3`)

```text
Escribe RouteFinishTests (orden encolar → borrar, llegada con dos lecturas precisas, imprecisas no
cuentan, cambio de destino reinicia, cola: red caída, 4xx, 404 → history) y
RouteFinishIntegrationTests con árbitro, disco y backend falsos: al finalizar no suena ninguna
instrucción más, se oye el anuncio y la ruta llega al historial al volver la red. Documenta en
docs/ARCHITECTURE.md.
```

## Verificación final

- Backend: `pytest -rs` cubre cierre idempotente e historial offline sin duplicados.
- iOS: finalizar a mano o llegar al destino corta las indicaciones, vibra y dice que terminó; en
  modo avión la ruta aparece en el historial al volver la red.

## Commits cubiertos

| Commit | Repo | Mensaje |
|---|---|---|
| `4c6dbf7` | Lumio | Mark routes as finished and record routes finished offline |
| `49fc0aa` | Lumio | Add endpoints to finish a route and save an offline finished route |
| `6d844fd` | Lumio | Add unit tests for finishing routes |
| `fff82f4` | Lumio | Add Postgres integration tests for finishing routes |
| `b7feb8c` | Lumio | Document the finish route endpoints |
| `dca8b54` | LumioFrontend | Stop a route's instructions in the audio arbiter |
| `2d18ce4` | LumioFrontend | Finish the active route and keep it queued until it reaches the history |
| `a874c8e` | LumioFrontend | Detect arrival at the destination and finish the route |
| `6b467e2` | LumioFrontend | Send finished routes to the backend and retry when the connection returns |
| `a869809` | LumioFrontend | Add the finish route action, arrival tracking and the finished screen |
| `d725aea` | LumioFrontend | Add unit tests for finishing routes and arrival detection |
| `3809bc8` | LumioFrontend | Add integration tests for finishing routes with audio, disk and backend |
| `90bdef3` | LumioFrontend | Document finishing routes and arrival detection |
