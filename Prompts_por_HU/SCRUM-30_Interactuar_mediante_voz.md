# SCRUM-30 · HU: Interactuar con la Aplicación Mediante Voz

| | |
|---|---|
| Responsable (Jira) | Néstor López |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 3 (2026-11-20 → 2026-11-23) |
| Depende de | SCRUM-315 (permisos), SCRUM-8/9/10/23 (casos de uso que la voz invoca) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero interactuar con la aplicación mediante comandos de voz para ejecutar
> acciones sin depender de controles visuales.

**Criterios de aceptación**
- Se puede activar la entrada por voz.
- Reconoce los comandos soportados y ejecuta la acción asociada.
- Pide aclaración si el comando es ambiguo e informa si no lo reconoce.
- Confirma las acciones cuando corresponde.
- Los comandos se usan durante la navegación sin interferir con alertas críticas.

## Prompts

### Prompt 1 · Diseño del catálogo

```text
Vamos con SCRUM-30. El reconocimiento y la interpretación tienen que ser locales: SFSpeechRecognizer
en español (en el iPhone si lo permite), sin backend. Los comandos solo llaman a los casos de uso
que ya existen; la voz no duplica lógica de navegación. Propón el catálogo de frases y la acción de
cada una antes de implementar. Mi lista: llévame a / quiero ir a / ruta a…, nueva ruta, cambiar
destino, repetir instrucción, ¿cómo voy?, llegué, terminar la ruta, ayuda, nada / olvídalo.
```

### Prompt 2 · Implementación (commit `426b78c`)

```text
Implementa Features/Voice:
- Domain/VoiceCommand y VoiceCommandInterpreter: compara palabras sin tildes, mayúsculas ni
  puntuación y gana la frase más larga. El destino conserva lo dicho («la Biblioteca Luis Ángel
  Arango»). Palabras sueltas ambiguas («ruta», o «cancelar» con ruta activa) generan «¿Quieres …
  o …?» y se acepta la opción dicha o «la primera», «la segunda». Sin ruta activa no se ofrecen
  acciones que la necesitan. Sí/no para confirmar.
- Domain/VoiceContracts, Data/DeviceSpeechListener (una sola frase, AVAudioSession .playAndRecord
  con mezcla para no cortar lo que suena), Data/ArbiterVoiceAudio y Data/PermissionsVoiceGate.
- Application/VoiceCommandService:
  · todo lo que dice va por el AudioArbiter como P2 (contexto voice-command, vence a los 30 s);
  · no abre el micrófono si suena una P1 y avisa que se intente al terminar; si empieza una P1
    mientras escucha, corta la escucha, no ejecuta nada y después dice «Comando de voz
    interrumpido por una alerta»;
  · «llegué» y «terminar» piden sí o no; una respuesta dudosa conserva la ruta;
  · al pedir un destino confirma lo entendido («Buscando una ruta a …») y no repite lo que el caso
    de uso ya anuncia;
  · no reconocido: «No reconocí el comando. Di ayuda…»; silencio también se informa.
- Presentation/VoiceCommandControl: botón flotante «Comando de voz» en Trayecto y en Tu ruta;
  mientras escucha muestra «Escuchando…» y pasa a «Cerrar comando de voz».
- DestinationViewModel+Voice implementa VoiceActionPerforming con los mismos métodos que los botones.
- La primera vez pide micrófono y reconocimiento con PermissionsViewModel.requestForVoiceCommands()
  (SCRUM-315); sin permisos explica cómo darlos y no abre el micrófono. Agrega
  NSSpeechRecognitionUsageDescription al Info.plist.
Pruebas: VoiceCommandInterpreterTests y VoiceCommandServiceTests con escucha y audio falsos.
Documenta en docs/HU-interactuar-mediante-voz.md con la tabla de comandos y la validación en iPhone.
```

### Prompt 3 · Arreglar la prueba y limpiar (commits `1d23c41`, `ed32c23`)

```text
VoiceCommandServiceTests no compila: la función auxiliar run(...) crea FakeActions,
FakePermissions y RecordingAudio como valores por defecto de sus parámetros, y esos valores se
evalúan fuera del MainActor. Haz los parámetros opcionales y crea los dobles dentro de la función,
sin cambiar las pruebas ni el servicio. Además se coló al repo un archivo llamado
«tash show --stat --include-untracked stash@{0}» (salida de git por error): bórralo.
```

## Verificación final

- `swift test` pasa las pruebas del intérprete y del servicio.
- En el iPhone: «Llévame a [lugar]» crea la ruta; «Ruta» pregunta y «la primera» responde;
  «Terminar la ruta» + «no» conserva la ruta; una alerta de obstáculo durante la escucha suena
  completa y luego se avisa la interrupción.
- Fuera de alcance según el doc: «estado de detección» y «reintentar detección» (dependían de
  SCRUM-37) y el dictado con geocodificación completa (SCRUM-313).

## Commits cubiertos

| Commit | Fecha | Mensaje |
|---|---|---|
| `426b78c` | 2026-11-20 | Add: adding hu |
| `1d23c41` | 2026-11-23 | Fix: fixxing test |
| `ed32c23` | 2026-11-23 | Remove stray git output file |
