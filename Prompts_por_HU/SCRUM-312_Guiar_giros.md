# SCRUM-312 · HU: Guiar Giros durante el Trayecto

| | |
|---|---|
| Responsable (Jira) | Daniel Patiño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 2 (2026-11-25) |
| Depende de | SCRUM-8, SCRUM-42, SCRUM-44, spike SCRUM-309 |
| Autoría de los commits | Néstor López |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario con discapacidad visual, quiero recibir cada giro de mi ruta en el momento
> correcto por audio y vibración para seguir el camino sin mirar la pantalla.

**Criterios de aceptación**
- El sistema sigue la posición del usuario durante la ruta activa mediante GPS.
- La guía usa la copia local de la ruta activa y no depende de que el backend responda.
- El sistema anuncia cada giro con la anticipación suficiente, indicando la dirección y la distancia.
- El anuncio se entrega como mensaje de navegación (prioridad 2) a través del AudioArbiter.
- Cada giro se acompaña de un patrón háptico distinto para izquierda y derecha.
- Si hay una locución en curso, el anuncio espera salvo urgencia, según las reglas del spike SCRUM-309.
- El sistema anuncia la llegada al destino.
- Si se pierde la red o se degrada la señal GPS, el sistema informa por audio y la detección de obstáculos no se ve afectada.

**Dependencias.** AudioArbiter (SCRUM-42), Crear Ruta (SCRUM-8) y spike de reglas de audio (SCRUM-309).

## Prompts

### Prompt 1 · Monitor de giros (commit `ed3d8cb`)

```text
Crea TurnGuidanceMonitor: durante la ruta activa observa la fuente de GPS compartida
(SharedLocationTracker, LocationFix con la velocidad), usa solo la copia local de la ruta y
avanza currentStep con RouteProgressEstimator. Cada giro se anuncia por el AudioArbiter como P2
con TurnDeadline: aviso previo («En 40 metros, gira…») y «Ahora, gira…», según distancia y
velocidad (Navigation/Domain/TurnGuidance.swift). Vibra turnLeft o turnRight según el lado,
configurable en las preferencias hápticas. Avisa antes de llegar y cuando el GPS se degrada o la
red se pierde o vuelve, sin afectar la detección. Pruebas en TurnGuidanceTests y
docs/HU-guiar-giros.md.
```

### Prompt 2 · Preferencias hápticas en el backend (commit `4610359`)

```text
Acepta turnLeft y turnRight en haptic_disabled_events de las preferencias, para que el usuario
los pueda apagar como los demás eventos de ruta. Prueba en test_schemas.py y README.
```

## Verificación final

- `swift test --filter TurnGuidanceTests` y `pytest tests/test_schemas.py` pasan.
- Caminando una ruta real: cada giro se oye con anticipación y vibra distinto a cada lado.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| Lumio | `4610359` | 2026-11-25 | SCRUM-312 HU: Guiar giros durante el trayecto |
| LumioFrontend | `ed3d8cb` | 2026-11-25 | SCRUM-312 HU: Guiar giros durante el trayecto |
