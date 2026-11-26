# SCRUM-43 · HU: Gestionar Cola de Mensajes

| | |
|---|---|
| Responsable (Jira) | Daniel Patiño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` (prototipo de reglas) y `LumioFrontend` (implementación) |
| Commits | 2 (2026-10-25) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero que los mensajes de audio se gestionen mediante una cola para evitar
> perder información importante y evitar la reproducción simultánea de mensajes.

**Criterios de aceptación**
- Los mensajes se almacenan según las reglas de prioridad.
- Se reproduce un único mensaje a la vez.
- Los mensajes se procesan respetando su prioridad.
- Los mensajes que ya no son relevantes pueden descartarse.
- La cola recibe mensajes mientras otro suena.
- La cola no bloquea los eventos críticos de seguridad.

## Prompts

### Prompt 1 · Prototipo de reglas en el backend (commit `3715778`)

```text
Antes de escribirlo en Swift quiero validar las reglas del árbitro de audio con pruebas rápidas
en Python. Crea app/modules/audio_orchestration con models, schemas, repository, service y router.
Reglas:
- Prioridades: P1 riesgo inmediato (seguridad), P2 navegación, P3 narración del entorno.
- Un solo mensaje sonando. P1 interrumpe P2 y P3. Misma prioridad: FIFO por orden de recepción,
  no por createdAt.
- P2 solo interrumpe P3 si el giro es urgente.
- P3 interrumpido se descarta; P2 interrumpido se reevalúa y, si sigue vigente, vuelve a sonar
  desde el principio.
- Un mensaje vencido o de un contexto invalidado se descarta antes de sonar.
Escribe tests/modules/audio_orchestration/test_service.py con un escenario por regla. Este
prototipo es la especificación: la app no va a llamar esta cola por HTTP.
```

### Prompt 2 · Cola y árbitro en la app (commit `f32bd44`)

```text
Lleva esas reglas a la app iOS sin llamar al backend. En Features/Audio:
- Domain/AudioMessage y AudioContracts: AudioPriority (immediateRisk, navigation,
  environmentInformation), id UUID, texto, contextID, expiresAt; protocolo AudioPlaying
  (play/stop con un PlaybackToken por intento) y AudioArbitrating (receive, updateContext,
  processNext, cancel).
- Domain/AudioMessageQueue: cola ordenada por prioridad y orden de llegada.
- Domain/AudioPolicy: decide si un mensaje nuevo interrumpe al actual y si un pendiente sigue
  siendo relevante (vencimiento + AudioDecisionContext con urgentNavigationMessageIDs e
  invalidatedContextIDs). No inventes umbrales: el spike todavía no los fijó.
- Application/AudioArbiterService (@MainActor): único dueño de la cola; reproduce uno a la vez;
  ignora callbacks de tokens viejos; si play falla, descarta el mensaje, lo informa por
  onPlaybackError y sigue con el siguiente; publica currentMessage, pendingMessages y
  onMessageChanged.
- Data/SpeechAudioPlayer: AVSpeechSynthesizer con un solo sintetizador, mapeando cada utterance
  a su token y entregando los callbacks en MainActor. play no espera a que termine la locución.
Conecta una instancia en AppDependencies. Ningún ViewModel ni detector debe llamar al TTS
directamente.
Pruebas en Tests/LumioFrontendTests/AudioArbiterTests.swift con un reproductor falso: prioridad,
FIFO, interrupciones, tokens antiguos, expiración y fallos de inicio. Documenta en
docs/ARCHITECTURE.md (sección Audio y seguridad + Integración de la cola) y en el README.
```

## Verificación final

- `pytest` del prototipo y `swift test` pasan (13 pruebas del árbitro al cierre de esta HU).
- Pendiente en iPhone: stop/reinicio, ducking e interrupciones externas (llamadas, Siri).

## Commits cubiertos

| Commit | Repo | Fecha | Mensaje |
|---|---|---|---|
| `3715778` | Lumio | 2026-10-25 | audio orchestration models and audio arbitrer service implemented |
| `f32bd44` | LumioFrontend | 2026-10-25 | Message queue management implemented |
