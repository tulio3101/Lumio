# SCRUM-36 · HU: Detección de Baja Luminosidad

| | |
|---|---|
| Responsable (Jira) | Samuel Gil |
| Estado Jira | Por hacer (hay commit con la implementación) |
| Repositorio | `LumioFrontend` |
| Commits | 1 (2026-10-27); ajustes posteriores dentro de SCRUM-33 (`6cc4bb3`, `944435d`) |

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

## Verificación final

- `swift test` pasa LowLightDetectorTests.
- En el iPhone: tapar la cámara durante una ruta produce un aviso; destaparla produce un aviso de
  recuperación, sin repetirse.
- **Pendiente:** mover la HU en Jira (sigue en Por hacer) y validar el umbral 0,15 en campo.

## Commits cubiertos

| Commit | Fecha | Mensaje |
|---|---|---|
| `694ded1` | 2026-10-27 | SCRUM-36: Detectar poca luz y avisar al usuario |
