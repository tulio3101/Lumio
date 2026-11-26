# SCRUM-9 · HU: Modificar Ruta

| | |
|---|---|
| Responsable (Jira) | Daniel Patiño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 14 (6 backend, 8 iOS; 2026-11-08) |
| Depende de | SCRUM-8, SCRUM-2 (JWT) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio quiero cambiar el destino de mi ruta activa para ir a otro lugar sin tener
> que reiniciar la navegación.

**Criterios de aceptación**
- El cambio de destino se pide por voz, con el mismo mecanismo y confirmación que Crear Ruta.
- Se calcula la nueva ruta desde la ubicación actual.
- Las nuevas instrucciones sustituyen a las anteriores.
- Se informa por audio que la ruta fue actualizada.
- Si no se puede, se mantiene la ruta anterior y se informa por audio.
- La ruta actualizada se persiste en el backend.

Fuera de alcance: el recálculo por desvío (SCRUM-26).

## Prompts · Backend

### Prompt 1 · Rutas con el JWT (commit `ba1014e`)

```text
El login (SCRUM-2) ya está en develop. Cambia la identificación provisional por el access token:
los endpoints de /places usan get_current_user y responden 401 invalid_session con el formato de
app/core/errors. Quita X-User-Id, ajusta seed_dev_user para que solo cree la cuenta y actualiza
las pruebas de integración y test_dependencies para que usen un Bearer real.
```

### Prompt 2 · Lógica para cambiar el destino (commit `70c0a0a`)

```text
Agrega en places la operación change_destination(route_id, cuerpo de crear ruta): misma ruta
(mismo id), nuevo destino, origen y pasos desde la ubicación actual, current_step a 0. Errores:
route_not_found (404, también si la ruta es de otro usuario) y route_not_open (409 si ya está
completada o cancelada). Usa el formato de errores común.
```

### Prompt 3 · Endpoint y pruebas (commits `4783a17`, `bf0d298`, `620906b`, `18cf870`)

```text
Expón PUT /places/routes/{route_id}/destination. Pruebas unitarias en test_service y test_router
con el repositorio falso, e integración en tests/integration/test_route_destination_api.py:
cambio correcto, ruta de otro usuario (404), ruta cerrada (409), sin token (401). Documenta en el
README que /places exige Bearer y la tabla de endpoints.
```

## Prompts · iOS

### Prompt 4 · Sesión con JWT en la app (commit `5672935`)

```text
Ahora que /places exige token, conecta el login real en la app: KeychainTokenStore,
RemoteAuthenticationService, AuthorizedHTTPClient (Bearer, un solo refresh ante 401 y borrar la
sesión si se rechaza) y SignOutService. RemoteActiveRouteService pasa a usar AuthorizedHTTPClient.
(El detalle de esta parte está en SCRUM-2.)
```

### Prompt 5 · Cambiar el destino sin perder la ruta (commit `57f342e`)

```text
Implementa Modificar Ruta en Navigation:
- Extrae de RouteCreationService un WalkingRoutePlanner común (ubicación nueva → geocodificar →
  calcular → instrucciones) que usen crear y modificar.
- RouteModificationService: misma ruta (mismo id), revisión +1, current_step 0, guarda la copia
  local, invalida el contexto de audio de la revisión anterior y anuncia «Ruta actualizada hacia
  X» + primera instrucción. Si falla antes de guardar, la ruta anterior queda intacta y se locuta
  «No se pudo cambiar el destino… Sigues con la ruta hacia X».
- Cada revisión usa su propio contextID: route-<id> y luego route-<id>-r<n>. El árbitro deja los
  contextos invalidados para siempre, así que reutilizarlo silenciaría las instrucciones nuevas.
- ActiveRouteSynchronizer: ruta nueva → PUT /places/routes/active; cambio de destino → PUT
  /places/routes/{remoteID}/destination (si el backend ya la cerró, 404/409, se sube como nueva).
  No sobrescribe una revisión local más nueva; hasPendingDestinationChange guarda lo pendiente.
- RoutePlannerView en modo .create o .changeDestination y el botón «Cambiar destino» en
  ActiveRouteView. En Preferencias, «Cerrar sesión».
Ajusta las pruebas de creación que dependían de la firma anterior.
```

### Prompt 6 · Pruebas (commits `9f43d2f`, `a3574bc`, `7cd4742`)

```text
Escribe RouteModificationServiceTests (éxito, cada fallo conserva la ruta anterior, revisión y
contexto nuevos) y AuthenticationTests (guardar tokens, refresh único, refresh rechazado borra la
sesión). Luego RouteModificationIntegrationTests con el árbitro real: tras cambiar el destino no
suena ninguna instrucción del recorrido anterior y sí «Ruta actualizada». Documenta el flujo y la
sesión JWT en docs/ARCHITECTURE.md.
```

### Prompt 7 · Repetir la indicación actual (commits `c348c7b`, `e3a9970`, `e2d0f6b`)

```text
Agrega RouteInstructionRepeater (InstructionRepeating): reenvía al árbitro el mismo mensaje del
paso actual con el contexto de la revisión vigente y la clave step-<n>; si aún espera o está
sonando no se duplica, y si ya terminó vuelve a sonar. En ActiveRouteView muestra la indicación
actual con «Repetir indicación», también con el Magic Tap de VoiceOver. Pruebas en
RouteInstructionRepeatTests y documentación.
```

## Verificación final

- Backend: `pytest -rs` cubre 200/401/404/409 del cambio de destino.
- iOS: con ruta activa, cambiar el destino suena «Ruta actualizada» y no vuelve ninguna
  instrucción vieja; un destino inexistente mantiene la ruta anterior y lo dice.
- **Pendiente:** pedir el cambio por voz con confirmación depende de SCRUM-313. SCRUM-30 ya permite
  «Llévame a…» con una ruta activa.

## Commits cubiertos

| Commit | Repo | Mensaje |
|---|---|---|
| `ba1014e` | Lumio | Identify route requests with the JWT access token |
| `70c0a0a` | Lumio | Add logic to change the destination of an open route |
| `4783a17` | Lumio | Implement endpoint to change the route destination |
| `bf0d298` | Lumio | Add unit tests for changing the route destination |
| `620906b` | Lumio | Add Postgres integration tests for changing the route destination |
| `18cf870` | Lumio | Document JWT on routes and the destination change endpoint |
| `5672935` | LumioFrontend | Sign in with email and keep session tokens in Keychain |
| `57f342e` | LumioFrontend | Change the active route destination keeping the previous route on failure |
| `9f43d2f` | LumioFrontend | Add unit tests for route modification and session handling |
| `a3574bc` | LumioFrontend | Add integration tests for destination change with audio arbiter |
| `7cd4742` | LumioFrontend | Document route modification flow and JWT session |
| `c348c7b` | LumioFrontend | Repeat the current route instruction on demand |
| `e3a9970` | LumioFrontend | Show the current instruction with a repeat action on the route screen |
| `e2d0f6b` | LumioFrontend | Document repeating the current instruction |
