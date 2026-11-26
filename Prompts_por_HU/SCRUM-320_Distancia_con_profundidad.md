# SCRUM-320 · HU: Estimar Distancia de Obstáculos con Profundidad

| | |
|---|---|
| Responsable (Jira) | Samuel Gil |
| Estado Jira | Por hacer (sus subtareas SCRUM-219 y SCRUM-349 están Finalizadas) |
| Repositorio | `LumioFrontend` |
| Commits | 4 (2026-10-27 → 2026-10-28) |
| Base | Spike SCRUM-307 / ADR-307 (LiDAR y modo reducido sin LiDAR) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

Estimar la distancia a cada obstáculo detectado con la profundidad del iPhone y avisar por audio si
la app trabaja en modo completo (con LiDAR) o reducido (sin LiDAR).

**Subtareas con commits**
- SCRUM-219: Implementar estimación de profundidad cuando el hardware lo permita.
- SCRUM-349: Informar por audio si la app opera en modo completo o reducido.

## Prompts

### Prompt 1 · Distancia con LiDAR (SCRUM-219, commit `cb654f1`)

```text
Según ADR-307, la distancia a un obstáculo se estima con sceneDepth de ARKit. Crea
Features/Safety/Data/DepthSampler.swift con sampleDepth(depthData, boundingBox): toma la mediana
de la profundidad del 30 % central de la caja, usando solo píxeles de confianza alta del
confidenceMap, y escala la caja de la imagen a la resolución del mapa de profundidad. Bloquea y
libera los pixel buffers correctamente. Devuelve nil si no hay píxeles válidos o si pasa de 4 m
(maxAlertDistanceMeters). Úsalo en DetectionPipeline para llenar Detection.distanceMeters.
```

### Prompt 2 · Devolver la profundidad real (SCRUM-219, commit `04dadf1`)

```text
Cambio de decisión: no queremos perder los obstáculos de más de 4 m, el anunciador los dice como
«a más de 4 metros». Haz que DepthSampler devuelva la profundidad real sin el tope de 4 m y deja un
comentario que explique el desvío respecto a ADR-307 y quién decide el umbral (el anunciador).
```

### Prompt 3 · Avisar el modo de operación (SCRUM-349, commit `e622768`)

```text
Al arrancar la detección (SafetyService.start, después de pipeline.start), SafetyService debe
decir por audio en qué modo trabaja: completo si el dispositivo tiene LiDAR o reducido si no,
explicando que en modo reducido no habrá distancias. El mensaje va por el AudioArbiter, nunca
directo al TTS, y se dice una vez por arranque.
```

### Prompt 4 · Coma decimal en la voz (SCRUM-349, commit `ed001c4`)

```text
La voz lee «1.5 metros» como «uno punto cinco». En SpeechAudioPlayer fija la voz en es-MX para
que AVSpeechSynthesizer lea la coma decimal en español («uno coma cinco metros»).
```

## Verificación final

- En un iPhone con LiDAR: una silla a ~1,5 m se anuncia «a 1,5 metros» y al arrancar se oye
  «modo completo».
- En un iPhone sin LiDAR: se oye «modo reducido» y las detecciones salen sin distancia.
- **Pendiente:** cerrar la HU en Jira (sigue en Por hacer). La fusión de profundidad del corredor y
  los desniveles se hicieron después, dentro de SCRUM-33 (`944435d`).

## Commits cubiertos

| Commit | Fecha | Mensaje |
|---|---|---|
| `cb654f1` | 2026-10-27 | SCRUM-219: Estimar distancia a obstáculos con LiDAR |
| `04dadf1` | 2026-10-28 | SCRUM-219: retornar profundidad real sin límite de 4 m (desvío ADR-307) |
| `e622768` | 2026-10-27 | SCRUM-349: Avisar por audio el modo de operación al arrancar |
| `ed001c4` | 2026-10-28 | SCRUM-349: locale es-MX en AVSpeechSynthesizer para leer coma decimal en español |
