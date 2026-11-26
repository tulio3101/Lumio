# SCRUM-29 · HU: Auditar Accesibilidad con VoiceOver

| | |
|---|---|
| Responsable (Jira) | Juan Sebastián Puentes |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 1 (2026-11-25) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario con discapacidad visual, quiero utilizar la aplicación mediante VoiceOver para
> poder interactuar con sus funciones sin depender de la información visual.

**Criterios de aceptación**
- Los elementos interactivos tienen etiquetas accesibles.
- VoiceOver comunica correctamente la función de cada control.
- Los controles tienen un orden lógico de navegación.
- Los estados dinámicos se comunican correctamente.
- Los mensajes de error son accesibles.
- Los flujos principales (cuenta, destino por voz, ruta, emergencia) se completan solo con VoiceOver.
- La navegación no requiere identificar visualmente los controles.

**Cómo se aplica.** La accesibilidad con VoiceOver es un criterio de terminado de **cada** HU con interfaz: no se cierra una HU sin haberla probado con VoiceOver. Esta HU es la **auditoría y corrección final** de los flujos principales, para detectar lo que se haya escapado.

## Prompts

### Prompt 1 · Auditoría de las vistas (commit `1365830`)

```text
Audita con el código las vistas SwiftUI de los flujos principales (cuenta, destino por voz, ruta,
emergencia, preferencias y permisos) contra los criterios de la HU: etiqueta, función, orden de
navegación, estados dinámicos y errores. Escribe docs/AUDITORIA-VOICEOVER.md con una tabla por
pantalla (hallazgo, criterio, corrección) y la lista de pruebas que quedan para hacer con
VoiceOver en un iPhone.
```

### Prompt 2 · Correcciones (commit `1365830`)

```text
Corrige lo que encontró la auditoría:
- AccountFormView: el error del correo o de la contraseña va en la pista de VoiceOver del propio
  campo, no en un texto suelto.
- ActiveRouteView: el botón dice «Recalculando la ruta» y «Finalizando la ruta» mientras trabaja.
- SettingsView: «Cerrando sesión» mientras cierra.
- PermissionsView: nombre, estado y propósito de cada permiso en un solo elemento, y el último
  mensaje marcado como dinámico (updatesFrequently).
```

## Verificación final

- El build de Xcode y `swift test` pasan sin cambios en las pruebas.
- Recorrer con VoiceOver en el iPhone la lista de docs/AUDITORIA-VOICEOVER.md: cuenta, destino por voz, ruta y emergencia se completan sin mirar.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| LumioFrontend | `1365830` | 2026-11-25 | SCRUM-29 HU: Auditar accesibilidad con VoiceOver |
