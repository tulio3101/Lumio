# SCRUM-39 · HU: Solicitar Narración del Entorno

| | |
|---|---|
| Responsable (Jira) | Juan Sebastián Puentes |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 3 (2026-11-25 → 2026-11-26); `703a981` es el cherry-pick de `a60e756` a develop |
| Depende de | SCRUM-38 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero solicitar una descripción del entorno cuando la necesite para
> obtener información visual bajo demanda.

**Criterios de aceptación**
- El usuario puede solicitar una narración mediante un mecanismo accesible.
- El sistema captura el entorno al momento de la solicitud.
- El sistema procesa la solicitud mediante el servicio de narración.
- El usuario recibe la descripción resultante mediante audio.
- Una solicitud no interrumpe una alerta de seguridad activa.
- El sistema informa si no puede procesar la solicitud.
- Las solicitudes repetidas se gestionan sin generar procesamiento innecesario.

## Prompts

### Prompt 1 · Mecanismos de solicitud y repetidas (commit `f6c8116`)

```text
Además del botón de SCRUM-38, permite pedir la descripción con un comando de voz («describe el
entorno», «¿qué hay delante?», «¿qué ves?»…) en VoiceCommandInterpreter y con la acción de
VoiceOver «Describir entorno» sobre la indicación actual. La ayuda de voz lo menciona.
Agrega NarrationRepeatPolicy: una solicitud en curso se informa («Ya estoy describiendo el
entorno»); pedir otra vez en menos de 3 s repite la última descripción sin foto ni red; en menos
de 10 s con la misma escena (huella VNFeaturePrint) se repite sin enviar. Retirar el
consentimiento olvida la última descripción. Pruebas en NarrationRequestTests y
docs/HU-solicitar-narracion-del-entorno.md.
```

### Prompt 2 · Ajustar la prueba de disponibilidad (commits `a60e756` y `703a981`)

```text
requestsReportTheirResultToTheMonitor (SCRUM-41) pide dos descripciones en el mismo instante.
Con la ventana de repetición de SCRUM-39 la segunda repite la anterior sin red y no reporta la
falla. Haz que la prueba avance el reloj la ventana de repetición (3 s) entre las dos
solicitudes.
```

## Verificación final

- `swift test --filter NarrationRequestTests` y `--filter NarrationAvailabilityTests` pasan.
- En el iPhone: pedir dos veces seguidas repite la descripción sin esperar a la red.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| LumioFrontend | `f6c8116` | 2026-11-25 | SCRUM-39 HU: Solicitar narración del entorno |
| LumioFrontend | `a60e756` | 2026-11-26 | SCRUM-39 Fix: Prueba de disponibilidad con la ventana de repetición |
| LumioFrontend | `703a981` | 2026-11-26 | SCRUM-39 Fix: Prueba de disponibilidad con la ventana de repetición |
