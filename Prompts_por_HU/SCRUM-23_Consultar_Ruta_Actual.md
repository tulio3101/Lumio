# SCRUM-23 · HU: Consultar Ruta Actual

| | |
|---|---|
| Responsable (Jira) | Daniel Patiño |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` (no necesita backend) |
| Commits | 6 (2026-11-08) |
| Depende de | SCRUM-8, SCRUM-9 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero consultar información sobre mi ruta actual para conocer el estado de
> mi trayecto durante la navegación.

**Criterios de aceptación**
- La ruta activa se identifica a partir de su copia local.
- Se pide con un mecanismo accesible (voz o gesto) y se responde por audio.
- Informa destino, progreso y siguiente instrucción.
- Funciona aunque el backend no responda.
- Si no hay ruta activa, lo informa.

## Prompts

### Prompt 1 · Estimar el avance (commit `e946b3d`)

```text
Para Consultar Ruta Actual necesito saber cuánto lleva el usuario sin depender del backend.
Crea Navigation/Domain/RouteProgress.swift con RouteProgressEstimator:
- aproxima la ruta con tramos rectos: origen → coordenada de cada maniobra → destino;
- proyecta la posición sobre el tramo más cercano;
- devuelve la siguiente indicación, lo recorrido, lo que falta (resto del tramo + pasos
  siguientes), el porcentaje y el tiempo restante con la velocidad de la ruta;
- a menos de 25 m del destino marca «llegando».
Que sea puro (sin CoreLocation) para probarlo en Linux.
```

### Prompt 2 · Responder por audio desde la copia local (commit `3869dc9`)

```text
Crea RouteStatusService (RouteStatusQuerying) y RouteStatus:
1. ActiveRouteStoring.load(): solo la copia local. Sin ruta: «No tienes una ruta activa…»;
   copia ilegible: «No se pudo leer la ruta…».
2. Una lectura de GPS (no necesita internet). Si falla, calcula el avance con currentStep y dice
   que es aproximado.
3. RouteProgressEstimator.
4. RouteStatusAnnouncements arma el texto: destino, avance (metros y porcentaje, tiempo restante)
   y siguiente indicación; la pantalla muestra las mismas frases.
El mensaje es P2 en el contexto de la revisión, con clave route-status: no se duplica si se pide
dos veces y se descarta si cambia el destino. No guardes el paso estimado: avanzar currentStep es
de SCRUM-312.
```

### Prompt 3 · Magic Tap y «¿Cómo voy?» (commit `c59b7da`)

```text
Conecta la consulta en la interfaz: Magic Tap de VoiceOver en toda la pestaña Trayecto, botón
«¿Cómo voy?» en el inicio y en «Tu ruta», y la acción de VoiceOver «Consultar ruta». Todo llama
DestinationViewModel.queryRouteStatus. Guarda en el ViewModel la ruta usada para la respuesta
(guidanceRoute) para que «Repetir indicación» diga la misma indicación que se acaba de oír.
```

### Prompt 4 · Pruebas (commits `6fcfb1f`, `b98c66b`)

```text
Escribe RouteProgressTests (inicio, mitad de un tramo, fuera de la ruta, a menos de 25 m, ruta de
un solo paso) y RouteStatusServiceTests (sin ruta, copia dañada, sin GPS usa currentStep). Luego
RouteStatusIntegrationTests con el árbitro real y SIN backend: la respuesta suena completa,
pedirla dos veces no la duplica y un cambio de destino descarta la pendiente.
```

### Prompt 5 · Documentación (commit `54a7068`)

```text
Documenta en docs/ARCHITECTURE.md y en el README el flujo de Consultar Ruta Actual: entradas,
pasos, textos y que no usa backend.
```

## Verificación final

- `swift test` pasa las pruebas de avance y estado.
- En el iPhone con VoiceOver: Magic Tap en Trayecto dice destino, avance y siguiente indicación,
  también en modo avión. Sin ruta dice que no hay ruta activa.

## Commits cubiertos

| Commit | Mensaje |
|---|---|
| `e946b3d` | Estimate route progress from the current location |
| `3869dc9` | Answer the active route status by audio from the local copy |
| `c59b7da` | Query the route status with Magic Tap or the How am I doing button |
| `6fcfb1f` | Add unit tests for route progress and status query |
| `b98c66b` | Add integration tests for the route status query without backend |
| `54a7068` | Document the route status query |
