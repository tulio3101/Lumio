# SCRUM-40 · HU: Actualizar Narración ante Cambios de Entorno

| | |
|---|---|
| Responsable (Jira) | Tulio Riaño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 5 (2026-11-25) |
| Depende de | SCRUM-38, SCRUM-42 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero recibir nuevas descripciones cuando el entorno cambie
> significativamente para evitar información repetitiva o desactualizada.

**Criterios de aceptación**
- El sistema controla la frecuencia de las solicitudes de narración.
- El sistema evita enviar solicitudes innecesarias en un entorno sin cambios relevantes.
- Un cambio significativo del entorno puede generar una nueva solicitud.
- El sistema evita reproducir narraciones obsoletas.
- Las narraciones respetan la prioridad definida por el AudioArbiter.
- La pérdida de conexión no afecta el loop de seguridad.
- El sistema controla el consumo de datos y recursos asociado a la narración.

## Prompts

### Prompt 1 · Narración automática por cambio de escena (commit `901c442`)

```text
Agrega AutoNarrationScheduler: durante la ruta activa calcula la huella de la escena
(VisionSceneSignatureProvider con VNFeaturePrint, SceneChange) y pide una descripción automática
solo si la escena cambió lo suficiente, pasaron al menos 10 s desde la anterior y el canal de
audio está libre. Respeta un tope de solicitudes, se pausa tras fallas seguidas y nunca toca el
loop de seguridad. EnvironmentNarrationService acepta trigger auto y AudioArbiterService expone
si el canal está libre. Conéctalo en AppDependencies y ActiveRouteView.
```

### Prompt 2 · Pruebas (commit `b19ec33`)

```text
Escribe AutoNarrationTests: sin cambio no se envía, un cambio grande sí, el intervalo mínimo, el
canal ocupado, la pausa por fallas, sin red no toma foto y una narración vieja no suena.
```

### Prompt 3 · Documentación (commit `78c3967`)

```text
Escribe docs/HU-actualizar-narracion-ante-cambios-de-entorno.md con la estrategia, los umbrales y
las pruebas, y actualiza ARCHITECTURE.md y HU-narracion-del-entorno.md.
```

### Prompt 4 · Límite propio para las automáticas en el backend (commit `7cafba2`)

```text
En app/modules/narration/rate_limit.py separa el límite de las solicitudes automáticas
(trigger=auto) del de las del botón: las automáticas van a 1 cada 10 s y 1.200 al día, para
controlar costo y datos sin quitarle cupo al usuario. Una automática rechazada responde 429 sin
llamar al VLM. Agrega los valores en config y pruebas en test_narration.py y test_narration_api.py.
```

### Prompt 5 · Documentar los límites (commit `749aad5`)

```text
Documenta en el README los límites de narración automática y del botón.
```

## Verificación final

- `swift test --filter AutoNarrationTests` y `pytest tests/modules/narration` pasan.
- Caminando: la descripción se actualiza al cambiar de lugar y no se repite en un pasillo igual.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| Lumio | `7cafba2` | 2026-11-25 | SCRUM-40 HU: Limit automatic narration requests separately from the button |
| Lumio | `749aad5` | 2026-11-25 | SCRUM-40 HU: Document the automatic narration limits |
| LumioFrontend | `901c442` | 2026-11-25 | SCRUM-40 HU: Actualizar la narración ante cambios de entorno |
| LumioFrontend | `b19ec33` | 2026-11-25 | SCRUM-40 HU: Probar la actualización de la narración |
| LumioFrontend | `78c3967` | 2026-11-25 | SCRUM-40 HU: Documentar la actualización de la narración |
