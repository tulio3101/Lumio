# SCRUM-315 · HU: Solicitar Permisos de Forma Accesible

| | |
|---|---|
| Responsable (Jira) | Néstor López |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 3 (2026-10-29 → 2026-11-12) |
| Rama | `HU-Solicitar-Permisos-de-Forma-Accesible` |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario con discapacidad visual, quiero que la app me explique por audio qué permisos necesita y
> me guíe para concederlos, para poder usarla sin ayuda visual.

**Criterios de aceptación**
- Explica por audio para qué sirve cada permiso: cámara, ubicación, micrófono, reconocimiento de
  voz y notificaciones cuando aplique.
- Las solicitudes del sistema se pueden usar con VoiceOver.
- Si se deniega, informa qué queda limitado y cómo habilitarlo después.
- Informa qué permisos hacen falta para iniciar una ruta.
- No depende de la información visual.

## Prompts

### Prompt 1 · Dominio, proveedor de iOS y pantalla (commit `e5e1950`)

```text
Implementa SCRUM-315 en Features/Permissions. No pidas permisos al arrancar la app.
- Domain/Permission: los permisos (cámara, ubicación mientras se usa, micrófono, reconocimiento de
  voz, notificaciones), sus estados (sin solicitar, concedido, denegado, restringido, servicio
  desactivado) y los requisitos por función: .voiceDestination (micrófono y luego reconocimiento),
  .routeCalculation (ubicación), .obstacleAssistance (cámara). PermissionService.missing(for:).
  Las notificaciones no bloquean rutas.
- Data/IOSPermissionProvider: consulta siempre a iOS (sin guardar copias como fuente de verdad) y
  hace las solicitudes nativas.
- Presentation/PermissionsView + PermissionsViewModel en Trayecto > Preparar permisos y en
  Preferencias > Permisos y accesibilidad. Cada solicitud tiene explicación, «Continuar» (abre el
  diálogo nativo) y «Ahora no». Sin VoiceOver la explicación se reproduce por el AudioArbiter
  antes de habilitar «Continuar»; con VoiceOver se enfoca el texto y «Repetir explicación» la pide
  al árbitro. No uses otro sintetizador.
- Denegado: explica la limitación y ofrece Abrir Ajustes. Restringido: explica la restricción del
  dispositivo sin prometer que la app la quite. Ubicación desactivada: indica Privacidad y
  seguridad > Localización.
- Los mensajes de preparación son P2 no urgente: no interrumpen P1 ni narración. Agrega al árbitro
  la forma de cancelar la locución de la explicación al cerrarla sin vaciar la cola global.
- El botón de calcular ruta consulta la ubicación sin pedirla y dice por audio y texto si falta.
Agrega las descripciones de uso en project.yml. Pruebas en PermissionTests (estados, revocación,
requisitos, espera/cancelación e interrupción P1 de la explicación). Crea
.github/workflows/permissions-validation.yml (pruebas portables en macOS y en simulador iOS) y
agrega esta rama a los filtros de xcode-distribution.yml. Documenta en docs/SCRUM-315.md el
alcance, la política, decisiones pendientes y un recorrido manual en iPhone.
```

### Prompt 2 · «Configurar» no abre la explicación (commit `f10e9f3`)

```text
En el iPhone, al pulsar «Configurar micrófono» suena «Escuchar estado» y no se abre la explicación.
Sospecho del estilo automático de List, que activa varios botones de la misma fila. Aplica
.buttonStyle(.borderless) a los botones de la lista para aislar sus acciones y agrega a
docs/SCRUM-315.md la sección de regresión con los pasos para confirmarlo en el dispositivo.
```

### Prompt 3 · Pedir la cámara al iniciar la ruta (commit `995618d`, con SCRUM-33)

```text
La detección de obstáculos (SCRUM-33) necesita la cámara. Cuando se inicia una ruta y la cámara
está sin solicitar, ObstacleAssistanceGate debe pedirla con el flujo accesible de
PermissionsViewModel (explicación y luego diálogo nativo), no con el diálogo directo. Si se niega,
la ruta sigue sin detección y se avisa una sola vez. Agrega a Permission el requisito y a
DestinationViewModel la llamada antes de arrancar la detección.
```

## Verificación final

- `swift test` y el workflow permissions-validation pasan.
- En el iPhone con VoiceOver: configurar micrófono, denegar en iOS, oír la limitación y el camino a
  Ajustes; habilitarlo en Ajustes y volver actualiza el estado.
- El doc dice que la evidencia en dispositivo es requisito para cerrar la HU.

## Commits cubiertos

| Commit | Fecha | Autor | Mensaje |
|---|---|---|---|
| `e5e1950` | 2026-10-29 | Nestor | HU-solicitar-permisos |
| `f10e9f3` | 2026-10-29 | Nestor | Fixxing permission pop up |
| `995618d` | 2026-11-12 | Samuel Gil | feat(safety): pedir permiso de camara con el flujo accesible al iniciar la ruta (SCRUM-33/315) |
