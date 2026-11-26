# SCRUM-313 · HU: Indicar Destino por Voz

| | |
|---|---|
| Responsable (Jira) | Juan Sebastián Puentes |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 1 (2026-11-25) |
| Depende de | SCRUM-30, spike SCRUM-311 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario con discapacidad visual, quiero indicar mi destino hablando para iniciar una ruta
> sin escribir ni mirar la pantalla.

**Criterios de aceptación**
- El usuario puede activar el dictado mediante un gesto o comando accesible.
- El sistema transcribe en español la dirección o el nombre del lugar indicado.
- El sistema lee en voz alta lo entendido y pide confirmación antes de calcular la ruta.
- Si no entiende o el resultado es ambiguo, el sistema pide repetir o aclarar.
- El destino confirmado se geocodifica y queda disponible para Crear Ruta y Modificar Ruta.
- Si no hay permiso de micrófono o de reconocimiento de voz, el sistema informa por audio cómo habilitarlo.
- El flujo completo es usable con VoiceOver y sin mirar la pantalla.

**Dependencias.** Spike de dictado y geocodificación. Esta HU es la entrada que reutilizan Crear Ruta y Modificar Ruta.

## Prompts

### Prompt 1 · Buscar el destino dictado (commit `8abe1ad`)

```text
Agrega DestinationLookingUp con MapKitDestinationLookup: busca el destino dictado cerca del
usuario y devuelve hasta 3 lugares con calle y ciudad.
```

### Prompt 2 · Confirmar por voz (commit `8abe1ad`)

```text
En VoiceCommandService lee lo entendido y pide sí o no antes de calcular. Con varios lugares los
lee y acepta el número, el nombre o «ninguno». Si no lo encuentra o el usuario dice que no, pide
el destino otra vez (dos intentos). Sin red o sin ubicación confirma el texto y Crear Ruta informa
el fallo. VoiceActionPerforming.navigate(to:) entrega el destino confirmado a Crear Ruta o
Modificar Ruta ya geocodificado (DestinationRequest.place). Pruebas en
DestinationDictationTests y docs/HU-indicar-destino-por-voz.md.
```

## Verificación final

- `swift test --filter DestinationDictationTests` pasa.
- Con VoiceOver: dictar «la biblioteca», elegir entre las opciones leídas y confirmar crea la ruta.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| LumioFrontend | `8abe1ad` | 2026-11-25 | SCRUM-313 HU: Indicar destino por voz |
