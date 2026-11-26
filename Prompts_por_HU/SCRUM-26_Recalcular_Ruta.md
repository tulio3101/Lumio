# SCRUM-26 · HU: Recalcular Ruta

| | |
|---|---|
| Responsable (Jira) | Daniel Patiño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 12 (5 backend, 7 iOS; 2026-11-17) |
| Depende de | SCRUM-8, SCRUM-9, SCRUM-10 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero que la aplicación recalcule automáticamente mi ruta cuando me desvíe
> del trayecto para continuar recibiendo instrucciones hacia mi destino.

**Criterios de aceptación**
- Se monitorea la posición durante la navegación e identifica el desvío.
- El recálculo se dispara con un umbral definido por el equipo (a validar en campo).
- Se calcula una nueva ruta hacia el mismo destino.
- Se actualizan instrucciones, copia local y backend.
- Se avisa por audio que la ruta fue actualizada.
- Sin red sigue guiando con la copia local, lo dice y recalcula al volver la conexión.
- Si no se puede recalcular, se informa.

## Prompts · Backend

### Prompt 1 · Reemplazar el recorrido y contar recálculos (commit `81e6af4`)

```text
Agrega a places la operación reroute: misma ruta y mismo destino; origen y pasos nuevos desde
donde se desvió el usuario; current_step a 0; la ruta queda activa. Guarda reroute_count y
last_rerouted_at (hora del dispositivo acotada entre el inicio y ahora) con la migración
0004_route_reroutes. Rechaza otro destino con 409 route_destination_mismatch (para eso está
/destination) y rutas cerradas con 409 route_not_open.
```

### Prompt 2 · Endpoint y pruebas (commits `4fc8bd8`, `d9e57dd`, `0365c96`, `1e54d58`)

```text
Expón PUT /places/routes/{route_id}/reroute con el cuerpo de crear ruta + rerouted_at. 404
route_not_found. Pruebas unitarias e integración en tests/integration/test_route_reroute_api.py
(conserva el id, suma reroute_count, acota la hora, rechaza otro destino y rutas cerradas).
Documenta en el README que ActiveRoute incluye reroute_count y last_rerouted_at.
```

## Prompts · iOS

### Prompt 3 · Política de desvío (commit `1acd990`)

```text
Crea Navigation/Domain/RouteDeviation.swift con DeviationPolicy (valores iniciales, a validar en
campo):
- una lectura con precisión <= 20 m está desviada si queda a más de 30 m del trayecto
  (agrega RouteProgressEstimator.distance sobre los tramos rectos origen → maniobras → destino);
- a <= 25 m del destino nunca está desviada (ahí decide la llegada);
- las imprecisas no cuentan ni reinician; una precisa en el trayecto reinicia;
- tres lecturas seguidas desviadas disparan el recálculo; 20 s entre recálculos automáticos;
  tras 3 fallos seguidos deja de intentar hasta volver al trayecto.
Agrega a NavigationInstructions los anuncios del recálculo.
```

### Prompt 4 · Sincronizar recálculos pendientes (commit `544e436`)

```text
En ActiveRouteSynchronizer envía los recálculos con PUT /places/routes/{remoteID}/reroute y
rerouted_at, y guárdalos como pendientes (hasPendingReroute, reroutedAt en ActiveRoute) hasta que
lleguen. 404 → se sube como ruta nueva; 409 → se reenvía como cambio de destino, que decide si
sigue abierta. Un cambio de destino pendiente gana sobre un recálculo pendiente.
FinishedRouteSynchronizer envía el recálculo pendiente antes de cerrar la ruta.
```

### Prompt 5 · Monitor y servicio de recálculo (commit `b47d771`)

```text
- SharedLocationTracker: reparte las lecturas de un solo CoreLocationRouteTracker entre
  ArrivalMonitor y RouteDeviationMonitor; sigue mientras alguno lo necesite.
- RouteDeviationMonitor: se activa y detiene junto con ArrivalMonitor; aplica DeviationPolicy;
  sin red (ConnectivityObserving con NWPathMonitor) espera y, al volver la conexión, recalcula
  con .reconnected si sigue desviado. Publica RerouteStatus (recalculando, recalculada, sin
  conexión, fallo).
- RouteRerouteService:
  1. sin red no llama a MapKit: «Sin conexión: no se puede recalcular…» y sigue la copia local;
  2. aviso según el disparador: «Te saliste de la ruta. Recalculando.», «Recalculando la ruta.»
     (a mano), «Volvió la conexión…»; los reintentos no repiten avisos (contexto route-reroute);
  3. WalkingRoutePlanner con .place(destino): mismo id y destino, revisión +1, current_step 0;
     si mientras calculaba la ruta cambió o terminó, se descarta (.superseded);
  4. invalida el contexto de la revisión anterior, «Ruta recalculada hacia X…» + primera
     instrucción y HapticCue.routeReady;
  5. si falla: la ruta anterior sigue, «No se pudo recalcular… Sigues con la ruta hacia X» y
     HapticCue.routeFailed.
```

### Prompt 6 · Interfaz (commit `b359053`)

```text
Muestra el RerouteStatus en «Tu ruta» y en el inicio, y agrega el botón «Recalcular ruta» con la
acción de VoiceOver del mismo nombre (sin esperas ni límite de intentos). Conéctalo en
AppDependencies y RootView.
```

### Prompt 7 · Pruebas y documentación (commits `4f15f00`, `7b2885d`, `512537e`)

```text
Escribe RouteRerouteTests (3 lecturas, imprecisas, cerca del destino, espera de 20 s, 3 fallos,
sin red, reconexión, .superseded) y RouteRerouteIntegrationTests con árbitro, disco y backend
falsos (las instrucciones viejas no vuelven a sonar, 404 y 409 del backend, finalizar con
recálculo pendiente). Documenta el flujo en docs/ARCHITECTURE.md.
```

## Verificación final

- Backend: `pytest -rs` cubre reroute con 404/409 y el contador.
- iOS: salirse más de 30 m del trayecto recalcula y lo anuncia; en modo avión dice que no puede y
  sigue guiando; al volver la red recalcula.
- **Pendiente:** validar los umbrales (30 m, 20 m, 3 lecturas, 20 s) en pruebas de campo.

## Commits cubiertos

| Commit | Repo | Mensaje |
|---|---|---|
| `81e6af4` | Lumio | Replace the path of an open route when the user deviates and count reroutes |
| `4fc8bd8` | Lumio | Implement endpoint to reroute an open route |
| `d9e57dd` | Lumio | Add unit tests for rerouting |
| `0365c96` | Lumio | Add Postgres integration tests for rerouting |
| `1e54d58` | Lumio | Document the reroute endpoint |
| `1acd990` | LumioFrontend | Detect deviation from the calculated route and define when to reroute |
| `544e436` | LumioFrontend | Send reroutes to the backend and keep them pending until they arrive |
| `b47d771` | LumioFrontend | Recalculate the route when the user deviates and announce it |
| `b359053` | LumioFrontend | Show the reroute status and add the recalculate route action |
| `4f15f00` | LumioFrontend | Add unit tests for deviation detection and rerouting |
| `7b2885d` | LumioFrontend | Add integration tests for rerouting with audio, disk and backend |
| `512537e` | LumioFrontend | Document rerouting |
