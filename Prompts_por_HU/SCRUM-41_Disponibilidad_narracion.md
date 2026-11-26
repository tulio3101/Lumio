# SCRUM-41 · HU: Gestionar Disponibilidad de la Narración

| | |
|---|---|
| Responsable (Jira) | Samuel Gil |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 3 (2026-11-25); el primero se comparte con SCRUM-31 |
| Depende de | SCRUM-38, SCRUM-40 |
| Autoría de los commits | Samuel Gil (monitor inicial) y Néstor López |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero que la aplicación gestione la disponibilidad del servicio de
> narración para saber cuándo puede proporcionar descripciones del entorno y continuar
> funcionando aunque este servicio no esté disponible.

**Criterios de aceptación**
- El sistema identifica cuando el servicio de narración está disponible.
- El sistema detecta pérdida de conectividad o indisponibilidad del servicio.
- El usuario recibe retroalimentación cuando la narración no está disponible, cuando corresponda.
- La indisponibilidad de la narración no afecta la detección de obstáculos ni las funciones de seguridad.
- El sistema puede reanudar la narración cuando el servicio vuelve a estar disponible.
- Las solicitudes realizadas durante una indisponibilidad se gestionan según la política definida.

## Prompts

### Prompt 1 · Monitor inicial (commit `971cbd5`)

```text
Crea NarrationAvailabilityMonitor y NarrationAvailability (checking, available,
unavailable(.offline | .serviceDown)) con un LumioAPIHealthChecker que consulta el backend y avisa
por FeedbackCatalog cuando la narración cae o vuelve.
```

### Prompt 2 · GET /vision/status (commit `e4fe9b4`)

```text
En el backend agrega GET /vision/status, sin sesión y sin llamar al VLM: available,
not_configured o degraded (3 fallas seguidas del VLM, durante 30 s desde la última) con
retry_after_seconds. POST /vision/analyze registra éxitos y fallas (503, 504 y respuesta vacía; el
429 no cuenta). haptic_disabled_events acepta narrationUnavailable y narrationAvailable. Pruebas
en test_availability.py, test_schemas.py y test_openapi.py; actualiza el README.
```

### Prompt 3 · Disponibilidad en la app (commit `329aadf`)

```text
Conecta NarrationAvailabilityMonitor en AppDependencies: durante la ruta vigila la red y GET
/vision/status (RemoteNarrationStatusService, reemplaza LumioAPIHealthChecker), cada 30 s si está
disponible y con espera creciente (2, 4, 8, 16 y 30 s o retry_after) si no. Avisa una vez al caer
y una al volver por el AudioArbiter (P2, contexto narration-status) con vibración
narrationUnavailable / narrationAvailable. Durante la caída las automáticas no toman foto y el
botón responde al instante y vuelve a comprobar, sin cola. Al volver,
AutoNarrationScheduler.resume() olvida la pausa. El botón muestra el estado y VoiceOver lo lee.
La detección no se toca. Pruebas en NarrationAvailabilityTests y
docs/HU-gestionar-disponibilidad-de-la-narracion.md.
```

## Verificación final

- `pytest tests/modules/vision_orchestration/test_availability.py` y `swift test --filter NarrationAvailabilityTests` pasan.
- En el iPhone: en modo avión se oye una sola vez que la narración no está disponible y al volver la red se oye que volvió.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| Lumio | `e4fe9b4` | 2026-11-25 | SCRUM-41 HU: Estado de disponibilidad de la narración (GET /vision/status) |
| LumioFrontend | `971cbd5` | 2026-11-25 | feat: integracion develop, desniveles y mesas, SCRUM-320/36/360/321/31 |
| LumioFrontend | `329aadf` | 2026-11-25 | SCRUM-41 HU: Gestionar disponibilidad de la narración |
