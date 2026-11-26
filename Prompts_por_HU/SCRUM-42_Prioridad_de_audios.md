# SCRUM-42 · HU: Gestionar Prioridad de Audios

| | |
|---|---|
| Responsable (Jira) | Juan Sebastián Puentes |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 1 (2026-11-25) |
| Depende de | SCRUM-43, spike SCRUM-309 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero que los mensajes de audio sean reproducidos según su nivel de
> prioridad para recibir primero la información más importante para mi seguridad.

**Criterios de aceptación**
- El sistema clasifica los mensajes según su prioridad.
- Las alertas de seguridad tienen la máxima prioridad.
- Las instrucciones de navegación tienen prioridad sobre la narración.
- La narración se reproduce únicamente cuando el canal está disponible.
- Un mensaje de mayor prioridad puede interrumpir uno de menor prioridad.
- Ningún módulo reproduce audio directamente fuera del AudioArbiter.

## Prompts

### Prompt 1 · Narración como P3 (commit `7e2c607`)

```text
Crea Narration/Domain/NarrationAudio.swift: la narración entra al árbitro siempre como P3
(.environmentInformation), en el contexto narration, vence 10 s después de la captura y usa
captureSequence, aunque el backend la marque como urgente.
```

### Prompt 2 · Pruebas de prioridad y guardia (commit `7e2c607`)

```text
Escribe AudioPriorityTests: la clasificación P1/P2/P3 de cada productor y los escenarios del spike
SCRUM-309 (P1 gana a P2 y P3, P2 antes que P3, P3 solo con el canal libre, narración interrumpida
descartada, narración vieja descartada). Agrega una guarda que recorre Sources: solo
SpeechAudioPlayer usa APIs de reproducción y solo AppDependencies lo crea. Documenta las reglas en
ARCHITECTURE.md.
```

## Verificación final

- `swift test --filter AudioPriorityTests` pasa.
- Con una narración sonando, una alerta de obstáculo la interrumpe de inmediato.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| LumioFrontend | `7e2c607` | 2026-11-25 | SCRUM-42 HU: Gestionar prioridad de audios |
