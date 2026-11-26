# SCRUM-37 · HU: Manejo de Errores del Modelo

| | |
|---|---|
| Responsable (Jira) | Néstor López |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 5 (2026-11-20) |
| Herramienta | Los commits traen el enlace a la sesión de Claude Code (`Claude-Session`) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del
> chat. El historial original está en la sesión de Claude Code enlazada en cada commit.

## La HU

> Como usuario de Lumio, quiero que la aplicación gestione los errores del sistema de detección para
> que un fallo del modelo no interrumpa el funcionamiento general de la aplicación.

**Criterios de aceptación**
- Detecta errores al cargar o inferir con el modelo.
- Un error no cierra la app.
- Informa cuando la detección no está disponible.
- Intenta recuperar el procesamiento cuando sea posible.
- Navegación y otras funciones siguen funcionando.
- La red no afecta el procesamiento local de seguridad.

## Prompts

### Prompt 1 · Contexto y plan

```text
Vamos con SCRUM-37 sobre develop, que ya trae la detección rediseñada de SCRUM-33 (rastreo,
corredor, profundidad, poca luz, inclinación). Mi trabajo anterior estaba sobre f69930a; no lo
copies: re-impleméntalo dentro del pipeline nuevo sin cambiar sus reglas de detección y usando el
punto de extensión que develop dejó en AppDependencies y SafetyAudio. La detección sigue
arrancando y parando con la ruta y con la compuerta de cámara de SCRUM-315. Antes de tocar código
dime qué fallos distingues y qué política de reintentos propones.
```

### Prompt 2 · Cargar e inferir con recuperación local (commit `cc1e3a1`)

```text
Implementa RecoveringModel, un actor dedicado (fuera del hilo principal y de AppDependencies)
que carga Core ML e infiere:
- distingue modelo ausente, carga fallida, inferencia fallida y salida incompatible;
- una lista vacía válida es «sin objetos»; una excepción o un tipo de resultado incompatible
  nunca se convierte en lista vacía;
- carga e inferencia recuperables: hasta tres reconstrucciones a 1, 2 y 4 s con presupuesto
  compartido; reconstruir no reinicia el presupuesto, solo una inferencia válida lo reinicia;
- modelo ausente y salida incompatible no se reintentan;
- el frame fallido se descarta; la siguiente inferencia usa uno nuevo.
El modelo se prepara al iniciar la detección, antes de abrir la cámara. Cada inicio crea flujos
nuevos de frames y de estado, y el fin de la cámara se informa como captura no disponible. Agrega
SafetyStatus (detenido, preparando, activo, recuperando, no disponible). Sin HTTP, descargas ni
chequeos de red. Usa un reloj inyectado para poder probar las esperas.
```

### Prompt 3 · Publicar el estado y avisar (commit `7374430`)

```text
SafetyService siempre existe y publica su estado. Un episodio de fallo se anuncia una sola vez como
P1 (SafetyAudio.modelUnavailable); la recuperación confirmada, una vez como P2 que vence
(SafetyAudio.detectionRecovered). Durante la recuperación no hay avisos de obstáculos. El modo
completo/reducido se anuncia con la primera inferencia válida, no al cargar el modelo. retry()
abre una sesión nueva solo si hay ruta activa. Detener o perder la detección cancela solo el
contexto "safety" (cancel(contextIDs:)), sin resetSession, para no tocar navegación ni narración.
```

### Prompt 4 · Mostrar el estado y reintentar (commit `6091e4e`)

```text
Crea SafetyStatusView y muéstrala en la sección de la ruta activa en Debug y Release, con
«Reintentar detección» cuando el estado es no disponible. Accesible con VoiceOver.
```

### Prompt 5 · Pruebas y workflow (commit `7ef9dd6`)

```text
Escribe las pruebas con fábricas y frames falsos:
- ModelRecoveryTests: modelo ausente, carga transitoria, presupuesto de inferencia, salida
  incompatible, escena vacía válida, descarte del frame fallido, reinicio tras éxito, presupuesto
  compartido y cancelación durante la espera.
- SafetyAudioIsolationTests: retirar Safety conserva navegación y narración.
- DetectionPipelineRecoveryTests (iOS) y SafetyServiceStopTests (iOS): un solo aviso de pérdida y
  uno de recuperación, aviso de modo con la primera inferencia, reintento.
Agrega .github/workflows/safety-validation.yml con swift test en macOS y xcodebuild test en
simulador, con el mismo Xcode del pipeline de distribución.
```

### Prompt 6 · Documentación (commit `ff25568`)

```text
Escribe docs/SCRUM-37.md: base integrada, política de fallos y recuperación, estado y audio,
pruebas, pasos de validación en iPhone (modo avión, revocar cámara, reiniciar rutas, compilación
sin el modelo) y límites (no cubre terminaciones del proceso por el sistema; el umbral térmico es
SCRUM-321).
```

## Verificación final

- CI: safety-validation.yml corre swift test y xcodebuild test.
- En el iPhone: con un build sin el modelo, la app abre, anuncia el fallo al iniciar la ruta y la
  navegación sigue; «Reintentar detección» funciona.
- El doc indica que la compilación iOS y los resultados de CI quedaron pendientes en el momento
  del commit.

## Commits cubiertos

| Commit | Fecha | Mensaje |
|---|---|---|
| `cc1e3a1` | 2026-11-20 | Load and run the detection model with local recovery |
| `7374430` | 2026-11-20 | Publish detection status and announce outage and recovery |
| `6091e4e` | 2026-11-20 | Show detection status and retry during the route |
| `7ef9dd6` | 2026-11-20 | Add tests for model recovery and detection status |
| `ff25568` | 2026-11-20 | Document model error handling |
