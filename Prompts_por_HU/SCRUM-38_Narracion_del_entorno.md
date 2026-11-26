# SCRUM-38 · HU: Narración del Entorno

| | |
|---|---|
| Responsable (Jira) | Tulio Riaño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 5 (2026-11-25) |
| Depende de | SCRUM-324 (consentimiento), SCRUM-42, SCRUM-44, ADR-308 |
| Autoría de los commits | Daniel Patiño |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario con discapacidad visual, quiero recibir una descripción del entorno que me rodea
> para obtener información contextual que no puedo percibir visualmente.

**Criterios de aceptación**
- El sistema puede capturar una imagen destinada a narración.
- La imagen puede enviarse al backend cuando existe conectividad.
- El backend procesa la imagen mediante el VLM configurado.
- El sistema recibe una descripción textual del entorno.
- La descripción se reproduce mediante el canal de audio definido.
- Una falla del backend no detiene el loop de seguridad.
- El sistema informa cuando la narración no está disponible.

## Prompts

### Prompt 1 · POST /vision/analyze con el VLM (commit `8bf41a1`)

```text
Implementa el loop lento del ADR-308 en el backend:
- POST /vision/analyze con Bearer y multipart/form-data: image JPEG (≤ 1 MB, ≤ 1024 px),
  captured_at, trigger (gesture|auto), language y consent_version. Sin consentimiento responde
  403 antes de leer la foto.
- app/modules/narration como servicio interno: prompt de sistema v1, cliente de Bedrock con la
  Converse API sobre el perfil us. (temperature 0,2, maxTokens 120, sin reintentos, timeout 4 s)
  y limpieza del texto a 2 oraciones como máximo.
- NARRATION_BACKEND disabled|fake|bedrock y NARRATION_MODEL_ID (por defecto
  us.anthropic.claude-haiku-5-5); fake solo en local.
- Límite por usuario: 1 cada 3 s y 1.500 al día (429).
- Errores 413 image_too_large, 422 invalid_image, 503 narration_unavailable y 504
  narration_timeout. Respuesta {text, model, latency_ms}, sin nivel de alerta.
- La foto solo vive en memoria; los logs registran metadatos. Quita el stub POST /narration.
Pruebas en tests/modules/narration y tests/modules/vision_orchestration.
```

### Prompt 2 · Permiso de Bedrock y despliegue (commit `37e4b81`)

```text
Para que la EC2 llame al modelo: en infra/lumio-dev.yaml da bedrock:InvokeModel e
InvokeModelWithResponseStream sobre el perfil us.<modelo> y el modelo base en us-east-1,
us-east-2 y us-west-2 (parámetro NarrationModelId). deploy.sh activa NARRATION_BACKEND=bedrock si
existe /lumio/<env>/NARRATION_MODEL_ID en SSM. En el Caddyfile limita /vision/* a 1100 KB para
que la foto nunca pase a disco. Documenta en el README el contrato, los errores, la privacidad y
lo pendiente fuera del código (habilitar el modelo en la consola de Bedrock).
```

### Prompt 3 · Del botón al audio en iOS (commit `3b585ed`)

```text
En la app:
- EnvironmentNarrationService: consentimiento y conexión antes de la foto, captura, POST
  /vision/analyze y descripción como P3 en el árbitro (NarrationAudio, captureSequence creciente).
  Una sola solicitud en vuelo, «Describiendo el entorno…» si tarda más de 1,5 s, descarta
  respuestas de más de 4 s y retirar el consentimiento la cancela.
- ARKitFrameSource.captureNarrationFrame toma la foto del ARSession de la seguridad, antes de la
  compuerta del detector y sin consumir sus frames; espera seguimiento normal hasta 1,5 s.
- NarrationFrameEncoder: 768 px de lado largo, vertical, JPEG 0,7, sin EXIF ni GPS, en memoria.
- RemoteEnvironmentNarrationService: multipart con sesión y timeout de 5 s.
- Cada falla (sin red, sin cámara, foto no clara, sesión, 429, 5xx, timeout) se dice por audio y
  no toca la detección. Botón «Describir entorno» en la ruta activa.
Pruebas en EnvironmentNarrationTests con dobles de captura, envío y audio.
```

### Prompt 4 · Documentación (commit `07c35a0`)

```text
Escribe docs/HU-narracion-del-entorno.md con el flujo, la tabla de fallas, las pruebas y la
validación en el iPhone, y agrega la sección en ARCHITECTURE.md y el README.
```

### Prompt 5 · Compilar fuera de iOS (commit `9565ca7`)

```text
environmentNarration se declara solo en iOS pero RootView lo pasa a DestinationView en todas las
plataformas, así que swift test en macOS no compila. Haz que la propiedad exista siempre y sea
nil fuera de iOS.
```

## Verificación final

- `pytest tests/modules/narration tests/modules/vision_orchestration` pasa.
- `swift test --filter EnvironmentNarrationTests` pasa y el build de Xcode compila.
- En el iPhone con consentimiento: «Describir entorno» da una descripción; en modo avión se oye el aviso y las alertas de obstáculos siguen.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| Lumio | `8bf41a1` | 2026-11-25 | SCRUM-38 HU: Describir el entorno con el VLM en POST /vision/analyze |
| Lumio | `37e4b81` | 2026-11-25 | SCRUM-38 HU: Permiso de Bedrock, despliegue y documentación de la narración |
| LumioFrontend | `3b585ed` | 2026-11-25 | SCRUM-38 HU: Narración del Entorno |
| LumioFrontend | `07c35a0` | 2026-11-25 | SCRUM-38 HU: Documentar la Narración del Entorno |
| LumioFrontend | `9565ca7` | 2026-11-25 | SCRUM-38 HU: Compilar RootView fuera de iOS |
