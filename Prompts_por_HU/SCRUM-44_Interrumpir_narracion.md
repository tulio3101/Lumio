# SCRUM-44 · HU: Interrumpir Narración ante Eventos Prioritarios

| | |
|---|---|
| Responsable (Jira) | Juan Sebastián Puentes |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 1 (2026-11-25) |
| Depende de | SCRUM-42, spike SCRUM-309 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero que una narración pueda ser interrumpida cuando ocurra un evento
> de mayor prioridad para recibir de inmediato información relevante para mi seguridad o
> navegación.

**Criterios de aceptación**
- Una alerta de seguridad (prioridad 1) interrumpe siempre una narración activa.
- Una instrucción de navegación (prioridad 2) interrumpe una narración según las reglas del spike SCRUM-309.
- Las interrupciones respetan las prioridades del AudioArbiter.
- La narración interrumpida no bloquea la reproducción del mensaje prioritario.
- La narración interrumpida se descarta por quedar obsoleta, salvo que el spike SCRUM-309 defina otra regla.
- La interrupción genera una transición de audio clara para el usuario.

## Prompts

### Prompt 1 · Margen del giro (commit `0bc2503`)

```text
Crea Audio/Domain/TurnDeadline.swift con TurnDeadline y TurnGeometry: cuándo llega el usuario al
giro y su margen de reacción (1,5 s en giro cerrado, 2,5 s en giro amplio, spike SCRUM-309).
```

### Prompt 2 · Reglas de interrupción en el árbitro (commit `0bc2503`)

```text
En AudioPolicy: una indicación P2 con turnDeadline espera a que termine la narración si después
queda margen y la interrumpe si no; lo que falta de la narración lo estima
SpeechDurationEstimator. AudioArbiterService guarda cuándo empezó cada locución y programa una
revisión en el último momento útil del giro por si la narración dura más de lo estimado. La
narración interrumpida se descarta. Transición clara: AudioTransition.afterInterruption y
SpeechAudioPlayer deja 0,3 s de pausa antes de la indicación; P1 empieza siempre sin pausa.
Pruebas en NarrationInterruptionTests y el contrato para SCRUM-312 en ARCHITECTURE.md.
```

## Verificación final

- `swift test --filter NarrationInterruptionTests` pasa.
- Con una descripción sonando cerca de un giro, la indicación llega a tiempo tras una pausa breve.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| LumioFrontend | `0bc2503` | 2026-11-25 | SCRUM-44 HU: Interrumpir narración ante eventos prioritarios |
