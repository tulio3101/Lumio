# SCRUM-314 · HU: Preparar la Cámara y la Seguridad al Iniciar el Trayecto

| | |
|---|---|
| Responsable (Jira) | Juan Sebastián Puentes |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 1 (2026-11-25) |
| Depende de | SCRUM-37, SCRUM-315, SCRUM-42 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario con discapacidad visual, quiero saber cuándo la app está lista para protegerme
> para empezar a caminar con confianza.

**Criterios de aceptación**
- El modelo de detección se carga una sola vez, en segundo plano, sin bloquear el hilo principal.
- El sistema verifica el permiso de cámara y arranca la sesión de captura.
- La capa de seguridad está lista antes de anunciar que todo está listo.
- El aviso de "cámara lista" se emite por audio y háptica, nunca solo de forma visual.
- Los servicios del backend (narración, voces, perfil) cargan en paralelo y no retrasan el aviso.
- Si el modelo o la cámara no pueden iniciar, el sistema informa por audio que la detección no está disponible.
- El arranque no depende de ninguna llamada al backend.

**Dependencias.** AudioArbiter, Manejo de Errores del Modelo, Solicitar Permisos de Forma Accesible.

## Prompts

### Prompt 1 · Cargar el modelo una sola vez (commit `dce0c6f`)

```text
Crea ReusableModelLoader: el modelo de detección se carga una sola vez y se reutiliza en cada
ruta. AppDependencies lo precarga en segundo plano al abrir la app, sin esperar a la red; una
ruta que empieza antes espera esa misma carga. Al reconstruir tras un fallo, RecoveringModel y
DetectionPipeline descartan el modelo compartido para no reutilizar el que falló.
```

### Prompt 2 · Aviso de cámara lista (commit `dce0c6f`)

```text
Con la primera inferencia válida di «Cámara lista. La detección de obstáculos está activa.» y el
modo completo o reducido (P2, vence a los 15 s) y vibra HapticCue.safetyReady, que vibra siempre.
Pruebas en SafetyStartupTests (portables) y SafetyServiceStopTests (iOS); documenta en
ARCHITECTURE.md.
```

## Verificación final

- `swift test --filter SafetyStartupTests` pasa.
- Al iniciar una ruta en el iPhone se oye «Cámara lista» con vibración antes de caminar.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| LumioFrontend | `dce0c6f` | 2026-11-25 | SCRUM-314 HU: Preparar la cámara y la seguridad al iniciar el trayecto |
