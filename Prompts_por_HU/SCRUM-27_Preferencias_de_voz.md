# SCRUM-27 · HU: Configurar Preferencias de Voz Descriptiva

| | |
|---|---|
| Responsable (Jira) | Néstor López |
| Estado Jira | En revisión |
| Repositorios | `LumioFrontend` y `Lumio` (respaldo en el backend) |
| Commits | 4 (2026-11-24 → 2026-11-25); los dos últimos se comparten con SCRUM-28 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero configurar las preferencias de la voz para adaptar las locuciones de
> la app a mis necesidades.

**Criterios de aceptación**
- Consultar las preferencias actuales.
- Elegir idioma, voz y velocidad disponibles.
- Se aplican a todas las locuciones del AudioArbiter (seguridad, navegación y narración).
- Se leen siempre del teléfono; la sincronización con el backend nunca bloquea alertas.
- Se conservan al cerrar y abrir la app.
- Se informa cuando una configuración no se puede aplicar.
- Accesible con VoiceOver.

## Prompts

### Prompt 1 · Preferencias locales aplicadas al reproductor (commit `c1cbbee`)

```text
Implementa SCRUM-27 en Features/Settings:
- Domain/VoicePreferences: idioma (solo variantes de español, porque todos los textos están en
  español), voz (o predeterminada) y velocidad de 0,5 a 2 en pasos de 0,25, que multiplica
  AVSpeechUtteranceDefaultSpeechRate sin salirse de sus límites. Validación y textos («1,25 veces»).
- Data/FileVoicePreferencesStore: JSON en Application Support, junto a la ruta activa.
- Data/SystemVoiceCatalog: voces en español instaladas (AVSpeechSynthesisVoice); las mejoradas
  con «(mejorada)».
- Application/VoicePreferencesService: lee al iniciar y aplica al reproductor en su init, para que
  la primera locución ya salga con ellas. Cada cambio se aplica, se guarda y se confirma con la
  voz nueva como P2 (contexto voice-preferences, vence a los 30 s); cada mensaje cancela el
  anterior del mismo contexto. «Probar la voz».
- Audio/Data/SpeechAudioPlayer guarda las preferencias en memoria y las aplica a cada utterance:
  reproducir nunca lee disco ni red, así una P1 no se retrasa. La locución que suena termina como
  empezó.
- Errores locutados y en un aviso: velocidad fuera de rango, idioma no disponible o voz no
  instalada no cambian nada (para la voz, decir dónde descargarla); si no se pudo guardar, se
  aplica y se avisa que al cerrar vuelve lo anterior. Al abrir, lo guardado que ya no sirve se
  reemplaza por lo predeterminado sin perder lo demás y se explica en la pantalla; el archivo no
  se reescribe.
- Presentation/VoicePreferencesView(Model): resumen que VoiceOver lee como un solo elemento,
  selectores y control ajustable de velocidad con «Volver a la velocidad normal». Los avisos no
  mueven el foco.
- AppDependencies crea el servicio justo después del reproductor y del árbitro, antes que
  cualquier productor de audio. Eliminar Cuenta (AccountDeletionService) borra el archivo y vuelve
  a la voz predeterminada; cerrar sesión no.
Pruebas en VoicePreferencesTests y documentación en docs/HU-preferencias-de-voz.md.
```

### Prompt 2 · Ruta del archivo sin MainActor (commit `54c614d`)

```text
La compilación falla porque FileVoicePreferencesStore usa FileActiveRouteStore.defaultFileURL,
que es @MainActor (por ActiveRouteStoring), y este almacenamiento no lo es. Construye la ruta
directamente (Application Support/Lumio, con el directorio temporal como respaldo) para que siga
en la misma carpeta que la ruta activa, y deja un comentario con el motivo.
```

### Prompt 3 · Respaldo en el backend (commit `5a7d643`, compartido con SCRUM-28)

```text
Agrega al backend la copia de respaldo de las preferencias de voz y vibración:
- tabla user_preferences (FK a users con CASCADE, migración 0008) con voice_language,
  voice_identifier, speech_rate, haptics_enabled, haptic_intensity, haptic_disabled_events y
  updated_at;
- GET /users/me/preferences: lo guardado o, si no hay nada, las predeterminadas con
  updated_at: null;
- PUT /users/me/preferences reemplaza todas: voice_language (es-MX, es-ES, es-419…),
  voice_identifier o null, speech_rate 0,5–2, haptics_enabled, haptic_intensity
  (soft | medium | strong) y haptic_disabled_events (solo routeReady, routeFailed,
  routeFinished). 200 con updated_at; 422, 500 preferences_update_failed, 503.
Mismas reglas que en el teléfono. Pruebas en tests/integration/test_preferences_api.py,
test_schemas y test_openapi; actualiza el README.
```

### Prompt 4 · Sincronizar en segundo plano (commit `046079c`, compartido con SCRUM-28)

```text
Crea PreferencesSynchronizer con RemotePreferencesService y FilePreferencesSyncStateStore
(preferences-sync.json), siempre después de aplicar y guardar en el teléfono:
- cada cambio del usuario queda pendiente y se sube en segundo plano; sin red, sin sesión o con
  error del servidor sigue pendiente y se reintenta al volver la conexión, al abrir la app o al
  iniciar sesión; un 422 no se reintenta;
- sin pendientes, al abrir con sesión o al iniciar sesión baja las del backend y solo las aplica
  si su updated_at es más reciente; lo bajado no se vuelve a subir ni se locuta; una voz que no
  está en este teléfono se cambia por la predeterminada y se avisa en la pantalla;
- al cerrar sesión o eliminar la cuenta se olvida el estado.
Conecta VoicePreferencesService y HapticPreferencesService. Pruebas en PreferencesSyncTests y
actualiza los dos docs de HU.
```

## Verificación final

- `swift test` pasa VoicePreferencesTests y PreferencesSyncTests; `pytest -rs` pasa las de preferencias.
- En el iPhone: subir la velocidad a 1,5 cambia también las indicaciones y alertas; cerrar y abrir
  conserva la configuración.
- El doc indica compilación y pruebas pendientes de CI al momento del commit; la HU sigue En revisión.

## Commits cubiertos

| Commit | Repo | Fecha | Mensaje |
|---|---|---|---|
| `c1cbbee` | LumioFrontend | 2026-11-24 | Add : adding preferencias de voz |
| `54c614d` | LumioFrontend | 2026-11-24 | Fix: build voice preferences path without main actor |
| `5a7d643` | Lumio | 2026-11-25 | Preferencias de voz y vibracion por cuenta |
| `046079c` | LumioFrontend | 2026-11-25 | Sincronizar preferencias de voz y vibracion con el backend |
