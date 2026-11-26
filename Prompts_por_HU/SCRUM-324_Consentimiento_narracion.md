# SCRUM-324 · HU: Consentir el Envío de Imágenes para la Narración

| | |
|---|---|
| Responsable (Jira) | Juan Sebastián Puentes |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 2 (2026-11-25) |
| Depende de | spike SCRUM-308 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario con discapacidad visual, quiero saber y decidir si las imágenes de mi cámara se
> envían para narrar el entorno, para proteger mi privacidad y la de las personas a mi alrededor.

**Criterios de aceptación**
- Antes de activar la narración por primera vez, el sistema explica por audio que se envían imágenes a un servicio en la nube y pide consentimiento explícito.
- Sin consentimiento, la narración no se activa y el resto de la app sigue funcionando igual.
- El usuario puede revocar el consentimiento en cualquier momento.
- Las imágenes enviadas no se almacenan de forma persistente en el backend, según lo definido en el spike SCRUM-308.
- La decisión del usuario se conserva entre sesiones.
- El consentimiento y su revocación son accesibles con VoiceOver.

**Dependencias.** Spike del loop lento (SCRUM-308) y Narración del Entorno (SCRUM-38).

## Prompts

### Prompt 1 · Consentimiento en el teléfono (commit `9fc22b7`)

```text
Agrega NarrationConsent y NarrationConsentPolicy: la decisión {granted, version, decidedAt} con un
aviso versionado según ADR-308 (las fotos van a AWS, no se guardan, retención solo por abuso, no
se describen personas). NarrationConsentService lo explica por audio, acepta, rechaza y revoca, y
guarda la decisión en el teléfono (FileNarrationConsentStore). Sin consentimiento vigente
consentVersionForUpload es nil y no se envía nada; revocar corta la narración en curso y avisa a
onRevoked. NarrationConsentView en Preferencias > Narración del entorno, accesible con VoiceOver.
Pruebas en NarrationConsentTests y el contrato para SCRUM-38 y 39 en ARCHITECTURE.md.
```

### Prompt 2 · Exigirlo en el backend (commit `7882bb6`)

```text
FrameSubmission acepta consent_version. POST /vision/analyze responde 403 consent_required si
falta el consentimiento o su versión, antes de mirar el frame (ADR-308). Pruebas en
test_consent.py y el error documentado en OpenAPI.
```

## Verificación final

- `swift test --filter NarrationConsentTests` y `pytest tests/modules/vision_orchestration/test_consent.py` pasan.
- Sin aceptar el aviso, «Describir entorno» explica el consentimiento y no toma foto; revocarlo corta la narración.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| Lumio | `7882bb6` | 2026-11-25 | SCRUM-324 HU: Exigir consentimiento antes de analizar imágenes |
| LumioFrontend | `9fc22b7` | 2026-11-25 | SCRUM-324 HU: Consentir el envío de imágenes para la narración |
