# SCRUM-36 · HU: Detección de Baja Luminosidad

| | |
|---|---|
| Responsable (Jira) | Samuel Gil |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 3 (2026-10-27 → 2026-11-26); ajustes intermedios dentro de SCRUM-33 (`6cc4bb3`, `944435d`) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero que la aplicación detecte condiciones de baja luminosidad para recibir
> información cuando las condiciones de captura puedan afectar la asistencia visual.

**Criterios de aceptación**
- Identifica condiciones de baja luminosidad durante el uso de la cámara.
- Usa el umbral de luminosidad definido.
- Alerta cuando se alcanza la condición y deja de alertar cuando vuelven a ser adecuadas.
- Funciona sin conexión.

## Prompts

### Prompt 1 · Detector de poca luz (commit `694ded1`)

```text
Crea Features/Safety/Application/LowLightDetector.swift. Los frames de ARKit vienen en
420YpCbCr8BiPlanarFullRange: el plano 0 es la luminancia (Y) de 8 bits. Calcula la luminancia
media normalizada 0…1 muestreando uno de cada 8 píxeles en cada eje del plano Y, para que el costo
de CPU sea mínimo, y bloquea y libera el buffer. Si el buffer no tiene planos, trata la escena como
iluminada (1.0). Umbral configurable alertThreshold = 0.15 con histéresis hysteresisMargin = 0.05:
alerta cuando la media baja de 0.15 y solo se recupera cuando llega a 0.20. Avisa una vez al
entrar en poca luz (audio por el AudioArbiter + háptica con UINotificationFeedbackGenerator) y otra
al recuperarse. Todo local, sin red.
Pruebas en Tests/SafetyTests/LowLightDetectorTests.swift con buffers sintéticos: oscuro, claro,
justo en el umbral, histéresis (no alterna entre 0.15 y 0.20) y buffer sin planos.
```

### Prompt 2 · Integrarlo al pipeline (dentro de SCRUM-33)

```text
Conecta LowLightDetector al DetectionPipeline para que evalúe cada frame mientras la detección está
activa, y adáptalo al contrato nuevo del frame. Su aviso va en el contexto de audio "safety" y se
cancela al detener la detección.
```

### Prompt 3 · Luz de ARKit en lugar del plano Y (commit `971cbd5`)

```text
Muestrear el plano Y retiene el IOSurface del frame y contribuye a «ARSession is retaining N
ARFrames». Cambia la API a analyze(ambientIntensity:) con ARFrame.lightEstimate.ambientIntensity
leído como Float dentro del delegado, antes de la compuerta del detector. Umbral en lux:
alertThreshold = 100 y hysteresisMargin = 40 (se recupera a 140). La recuperación se confirma
por audio como P3. Actualiza LowLightDetectorTests.
```

### Prompt 4 · Pasar por el catálogo y el motor háptico (commit `0743cc9`, SCRUM-31)

```text
LowLightDetector todavía usa su propio UINotificationFeedbackGenerator. Haz que reciba el motor
háptico y emita por FeedbackCatalog: lowLight (P1, patrón warning, que vibra siempre) y
lowLightRecovered (P3, sin vibrar). Así respeta las preferencias hápticas y deja de depender de
UIKit. Pruébalo en FeedbackMatrixTests.
```

## Verificación final

- `swift test` pasa LowLightDetectorTests.
- En el iPhone: tapar la cámara durante una ruta produce un aviso; destaparla produce un aviso de
  recuperación, sin repetirse.
- `swift test --filter FeedbackMatrixTests` cubre la alerta, la histéresis y la vibración por el motor háptico.

## Commits cubiertos

| Commit | Fecha | Mensaje |
|---|---|---|
| `694ded1` | 2026-10-27 | SCRUM-36: Detectar poca luz y avisar al usuario |
| `971cbd5` | 2026-11-25 | feat: integracion develop, desniveles y mesas, SCRUM-320/36/360/321/31 |
| `0743cc9` | 2026-11-26 | SCRUM-31: retroalimentación del sistema por FeedbackCatalog |
