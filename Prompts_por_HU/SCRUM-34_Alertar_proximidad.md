# SCRUM-34 · HU: Alertar Proximidad de Objetos

| | |
|---|---|
| Responsable (Jira) | Tulio Riaño |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 3 (2026-11-25) |
| Depende de | SCRUM-320, SCRUM-42, spike SCRUM-309 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero recibir una alerta cuando un objeto se encuentre a una distancia
> potencialmente peligrosa para reaccionar oportunamente.

**Criterios de aceptación**
- El sistema recibe la distancia estimada de cada obstáculo detectado (HU Estimar Distancia, SCRUM-320).
- El sistema clasifica la proximidad según la tabla de umbrales definida en el spike SCRUM-309.
- Los objetos dentro de la zona de riesgo generan una alerta de seguridad (prioridad 1 del AudioArbiter).
- La alerta se comunica por audio y por háptica.
- En modo reducido (iPhone sin LiDAR) las alertas usan la proximidad aproximada definida en el spike SCRUM-307.
- Las alertas funcionan sin conexión a Internet.
- El sistema evita generar alertas repetitivas sobre el mismo obstáculo.

**Dependencias.** SCRUM-320 (distancia), SCRUM-42 (AudioArbiter) y spike SCRUM-309 (umbrales).

## Prompts

### Prompt 1 · Política de proximidad del spike (commit `e5ad9e4`)

```text
Reemplaza el umbral único de 1 m por Safety/Domain/ProximityPolicy.swift con la tabla del spike
SCRUM-309 y ADR-307:
- LiDAR: zona de riesgo ≤ 2,5 m (≤ 3,0 m si el objeto se acerca, TrackedDetection.isApproaching)
  como P1 con metros; hasta 3 m fuera de la zona, P3 con metros; 3–4 m, P3 «cerca» sin metros.
- Sin LiDAR: < 1,5 m «muy cerca» P1; 1,5–2,5 m «cerca» P3; más lejos, sin aviso de distancia.
- Nunca se dicen metros en el modo reducido.
Los umbrales van en DetectionFocusConfig.proximity. ObstacleAnnouncer usa la política y guarda
por objeto el nivel más alto ya anunciado: solo vuelve a sonar si sube de nivel o si se sigue
acercando y pasó el cooldown de 4 s. SafetyService pasa DepthMode.reduced cuando no hay
profundidad y vibra .warning en la zona de riesgo.
```

### Prompt 2 · Pruebas (commit `e5a1b63`)

```text
Agrega Tests/SafetyTests/ProximityPolicyTests.swift con cada fila de la tabla y los bordes
(2,5 m, 3,0 m, 1,5 m), y amplía ObstacleAnnouncerTests: P1 en la zona de riesgo, sin metros en
modo reducido, sin repetir cuando la distancia oscila en un umbral, y repetición al subir de
nivel.
```

### Prompt 3 · Documentación (commit `096e80d`)

```text
Escribe docs/HU-alertar-proximidad-de-objetos.md: qué había y qué cambia, la tabla de umbrales,
cada criterio con el código que lo cumple y las decisiones que el equipo debe revisar en campo
(más alertas P1 al pasar de 1 m a 2,5–3 m). Actualiza la línea de ARCHITECTURE.md.
```

## Verificación final

- `swift test --filter ProximityPolicyTests` y `--filter ObstacleAnnouncerTests` pasan.
- En la calle con LiDAR: una persona a menos de 2,5 m da una alerta P1 con metros y vibración, sin repetirse mientras se mantiene a esa distancia.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| LumioFrontend | `e5ad9e4` | 2026-11-25 | SCRUM-34 HU: Clasificar la proximidad con los umbrales del spike |
| LumioFrontend | `e5a1b63` | 2026-11-25 | SCRUM-34 HU: Probar las alertas de proximidad |
| LumioFrontend | `096e80d` | 2026-11-25 | SCRUM-34 HU: Documentar las alertas de proximidad |
