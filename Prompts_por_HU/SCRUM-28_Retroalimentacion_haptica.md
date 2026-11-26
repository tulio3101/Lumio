# SCRUM-28 · HU: Configurar Retroalimentación Háptica

| | |
|---|---|
| Responsable (Jira) | Néstor López |
| Estado Jira | Finalizado |
| Repositorios | `LumioFrontend` y `Lumio` (respaldo en el backend) |
| Commits | 4 (2026-11-24 → 2026-11-25); `5a7d643` y `046079c` se comparten con SCRUM-27 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero configurar la retroalimentación háptica para adaptar las alertas
> táctiles a mis preferencias.

**Criterios de aceptación**
- Activar o desactivar la vibración y configurar sus opciones.
- Cada evento configurado genera su patrón.
- Se leen del teléfono; la sincronización nunca bloquea las alertas.
- Se conservan al cerrar la app.
- Las alertas críticas no cambian con las preferencias.
- Accesible con VoiceOver.

## Prompts

### Prompt 1 · Patrones por evento y preferencias (commit `86619dc`)

```text
Implementa SCRUM-28. Hoy ruta lista y ruta terminada vibran igual y las alertas de seguridad no
vibran. Quiero un ritmo por evento:
| HapticCue | Patrón | Configurable |
| routeReady | dos toques cortos | sí |
| routeFailed | uno fuerte, pausa, uno suave | sí |
| routeFinished | tres toques que suben | sí |
| emergencyActivated | tres fuertes espaciados | no |
| emergencySent | dos rápidos, pausa, uno | no |
| emergencyFailed | dos pares fuertes | no |
| criticalAlert (P1 sonando) | cuatro fuertes y rápidos | no |
- Settings/Domain/HapticPreferences: activado, eventos apagados, intensidad suave/media/fuerte,
  HapticPattern.pattern(for:intensity:) (la intensidad multiplica la fuerza; las alertas de
  seguridad no se escalan ni se apagan).
- Data/FileHapticPreferencesStore: JSON en Application Support, leído una vez al abrir.
- Application/HapticPreferencesService: es el HapticFeedbackPlaying que reciben Crear, Modificar,
  Recalcular y Finalizar Ruta, que siguen llamando play(.routeReady) sin cambios. AppDependencies
  conecta AudioArbiterService.onMessageChanged: cuando un immediateRisk pasa a playing vibra
  criticalAlert sin mirar preferencias, así cualquier productor de P1 vibra sin tocar su código.
- Navigation/Data/UIKitHapticFeedback reproduce pulsos con UIImpactFeedbackGenerator.
- Presentation/HapticPreferencesView(Model) en Preferencias > Vibración: interruptor general, un
  interruptor por evento con su patrón descrito y «Probar vibración» en el rotor, selector de
  intensidad, y «Alertas de seguridad» siempre activas con «Probar alerta de seguridad». Al
  encender un evento se siente su patrón. Sin motor de vibración (iPad) se avisa.
- Si no se pudo guardar, se aplica igual y se avisa (P2) que al cerrar vuelve lo anterior.
- Eliminar Cuenta borra el archivo.
Pruebas en HapticPreferencesTests y documentación en docs/HU-preferencias-hapticas.md.
```

### Prompt 2 · Nombres de prueba duplicados (commit `e12d847`)

```text
Dos pruebas de HapticPreferencesTests tienen el mismo nombre que otras de VoicePreferencesTests y
el compilador se queja. Renómbralas para que describan su caso de háptica.
```

### Prompt 3 · Respaldo y sincronización (commits `5a7d643`, `046079c`)

```text
Usa el mismo respaldo que las preferencias de voz (ver SCRUM-27): GET/PUT /users/me/preferences y
PreferencesSynchronizer. Solo se envían los eventos configurables (routeReady, routeFailed,
routeFinished); las alertas de seguridad no se pueden apagar. Agrega a PreferencesSyncTests los
casos de háptica y actualiza docs/HU-preferencias-hapticas.md con la sección de respaldo.
```

## Verificación final

- `swift test` pasa HapticPreferencesTests y PreferencesSyncTests.
- En el iPhone sin mirar: crear ruta = dos toques; finalizarla = tres que suben. Con la vibración
  apagada, una alerta de obstáculo igual vibra.
- Compilación de Xcode y `swift test` en verde en el CI de develop.

## Commits cubiertos

| Commit | Repo | Fecha | Mensaje |
|---|---|---|---|
| `86619dc` | LumioFrontend | 2026-11-24 | HU: Configurar retroalimentacion haptica |
| `e12d847` | LumioFrontend | 2026-11-25 | test: rename haptic tests that collided with voice tests |
| `5a7d643` | Lumio | 2026-11-25 | Preferencias de voz y vibracion por cuenta |
| `046079c` | LumioFrontend | 2026-11-25 | Sincronizar preferencias de voz y vibracion con el backend |
