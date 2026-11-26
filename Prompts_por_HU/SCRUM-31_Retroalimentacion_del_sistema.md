# SCRUM-31 · HU: Recibir Retroalimentación del Sistema

| | |
|---|---|
| Responsable (Jira) | Samuel Gil |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 3 (2026-11-25 → 2026-11-26); el primero se comparte con SCRUM-320, 36, 360 y 321 |
| Depende de | SCRUM-42 (AudioArbiter), SCRUM-28 (motor háptico) |
| Autoría de los commits | Samuel Gil (catálogo inicial) y Daniel Patiño (matriz, flujos y pruebas) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero recibir retroalimentación sobre las acciones y estados de la
> aplicación para saber qué está ocurriendo sin depender de información visual.

**Criterios de aceptación**
- Las acciones relevantes generan retroalimentación.
- Los errores generan retroalimentación.
- Los eventos críticos generan una alerta prioritaria.
- La retroalimentación usa audio y háptica.
- Todo el audio se emite exclusivamente a través del AudioArbiter (SCRUM-42) y toda la háptica a través del motor háptico; no existe un gestor de audio paralelo.
- Los mensajes respetan las prioridades del AudioArbiter (1 seguridad, 2 navegación, 3 narración).
- La retroalimentación no bloquea el funcionamiento de otros módulos críticos.

**Alcance.** Esta HU define la matriz de eventos y su integración. La cola, la prioridad y la reproducción son responsabilidad del AudioArbiter.

## Prompts

### Prompt 1 · Catálogo de avisos (commit `971cbd5`)

```text
Crea Features/Audio/Domain/FeedbackCatalog.swift: un FeedbackEvent por aviso del sistema (ruta
creada, modificada, recalculada y finalizada, llegada, permisos, modelo no disponible, poca luz,
modo completo o reducido, sin conexión, error del backend, sesión cerrada o vencida) y un
FeedbackItem con el AudioMessage y el HapticCue opcional. Reutiliza los textos que ya existen
(NavigationInstructionBuilder, SafetyAudio, SessionAudio). FeedbackCatalog.emit envía el
mensaje al AudioArbiter y el patrón al motor háptico. Nada de TTS ni generadores de vibración
fuera de esos dos.
```

### Prompt 2 · Matriz completa y flujos principales (commit `0743cc9`)

```text
Completa la matriz evento → prioridad → patrón: fallas al crear, modificar y recalcular la ruta,
pausa y reanudación por calor, vuelta de la detección y cada paso de la emergencia (todo P1 en el
contexto emergency). Prioridades: 1 seguridad, 2 navegación, 3 narración.
Haz que RouteCreationService, RouteModificationService, RouteRerouteService, RouteFinishService,
EmergencyService (cancela su aviso anterior antes de emitir), SafetyService, SessionTeardown y
SessionExpiryCoordinator emitan por el catálogo sin cambiar texto, prioridad, contexto ni clave.
LowLightDetector deja su UINotificationFeedbackGenerator: recibe el motor háptico, emite lowLight
(P1, warning) y lowLightRecovered (P3, sin vibrar) y ya no depende de UIKit.
```

### Prompt 3 · Pruebas y documentación (commit `808de3c`)

```text
Escribe Tests/LumioFrontendTests/FeedbackMatrixTests.swift:
- cada evento tiene la prioridad y el patrón de la matriz;
- las alertas P1 nunca usan un patrón que el usuario pueda apagar;
- todo error de ruta y de emergencia se locuta y vibra; los de emergencia recuerdan el 123;
- emit funciona sin árbitro o sin motor háptico;
- conflictos en el AudioArbiterService real: P1 interrumpe P2, P2 espera detrás de P1, P3 no
  interrumpe y un aviso repetido no se encola dos veces;
- una guarda que recorre Sources y falla si hay un generador de vibración fuera de
  UIKitHapticFeedback.
Documenta la matriz, los anuncios de VoiceOver permitidos y la validación en el iPhone en
docs/HU-recibir-retroalimentacion-del-sistema.md y una sección en ARCHITECTURE.md.
```

## Verificación final

- `swift test --filter FeedbackMatrixTests` pasa, junto con las pruebas existentes de rutas, emergencia y preferencias hápticas.
- En el iPhone: tapar la cámara da «Poca luz» con vibración aunque la vibración esté apagada; una alerta de obstáculo corta una indicación y la indicación vuelve.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| LumioFrontend | `971cbd5` | 2026-11-25 | feat: integracion develop, desniveles y mesas, SCRUM-320/36/360/321/31 |
| LumioFrontend | `0743cc9` | 2026-11-26 | SCRUM-31: retroalimentación del sistema por FeedbackCatalog |
| LumioFrontend | `808de3c` | 2026-11-26 | SCRUM-31: pruebas de la matriz, conflictos de prioridad y documentación |
