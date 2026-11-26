# SCRUM-32 · HU: Configurar Preferencias de Accesibilidad

| | |
|---|---|
| Responsable (Jira) | Juan Sebastián Puentes |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 1 (2026-11-25) |
| Depende de | SCRUM-27, SCRUM-28 (mismo modelo de preferencias) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero configurar mis preferencias de accesibilidad para adaptar la
> interacción con la aplicación a mis necesidades.

**Criterios de aceptación**
- El usuario puede consultar sus preferencias.
- El usuario puede modificar las preferencias disponibles.
- Los cambios se validan antes de almacenarse.
- Las preferencias se leen siempre desde almacenamiento local en el dispositivo; la sincronización con el backend nunca bloquea las alertas de seguridad.
- Las preferencias se conservan después de cerrar la aplicación.
- Las preferencias se aplican a los módulos correspondientes.
- La configuración es accesible mediante VoiceOver.

**Alcance.** Usa el mismo modelo de preferencias que Voz (SCRUM-27) y Háptica (SCRUM-28): un solo `UserPreferences`, no un modelo por HU.

## Prompts

### Prompt 1 · Modelo y servicio de preferencias (commit `3c74d1c`)

```text
Agrega Settings/Domain/AccessibilityPreferences.swift con tres opciones: narración automática
(activada por defecto, ADR-308), decir el estado al abrir la app y avisos breves o detallados.
Al leer, un campo ausente o desconocido toma su predeterminado. AccessibilityPreferencesService
con FileAccessibilityPreferencesStore: se leen del teléfono, se aplican en memoria, se guardan al
cambiar y, si no se pudo guardar, lo dicen por audio y siguen aplicadas mientras la app esté
abierta. Nunca esperan a la red. Eliminar cuenta las reinicia.
```

### Prompt 2 · Aplicarlas y la pantalla (commit `3c74d1c`)

```text
Aplica las preferencias: AutoNarrationScheduler no toma fotos si la narración automática está
apagada, y HomeStatusService no habla al abrir y usa avisos sin pistas cuando se eligen breves.
Crea AccessibilityPreferencesView en Preferencias, accesible con VoiceOver, y conéctala en
AppDependencies y RootView. Pruebas en AccessibilityPreferencesTests y
docs/HU-preferencias-de-accesibilidad.md.
```

## Verificación final

- `swift test --filter AccessibilityPreferencesTests` pasa.
- Cambiar una opción, cerrar y abrir la app: la opción se conserva y se aplica.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| LumioFrontend | `3c74d1c` | 2026-11-25 | SCRUM-32 HU: Configurar preferencias de accesibilidad |
