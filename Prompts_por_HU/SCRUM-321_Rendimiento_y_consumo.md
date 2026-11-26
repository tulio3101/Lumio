# SCRUM-321 · HU: Optimizar Rendimiento y Consumo de la Detección

| | |
|---|---|
| Responsable (Jira) | Samuel Gil |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 2 (2026-11-25); el primero se comparte con SCRUM-320, 36, 360 y 31 |
| Depende de | SCRUM-33, spike SCRUM-306 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario con discapacidad visual, quiero que la detección se mantenga fluida y no agote mi
> batería para poder usar la app durante todo un trayecto.

**Criterios de aceptación**
- La detección se sostiene en el rango de fps objetivo del loop de seguridad (\~10–15 fps) durante la navegación.
- El procesamiento no bloquea el hilo principal.
- El consumo de batería y la temperatura se miden en sesiones largas y se comparan contra los límites definidos en el spike (SCRUM-306).
- Bajo presión térmica el sistema reduce su carga de forma controlada en lugar de fallar.
- El rendimiento se verifica en un iPhone con LiDAR y en uno sin LiDAR.

**Dependencias.** Spike de YOLO26n en Core ML (SCRUM-306) y Detectar y Clasificar Obstáculos (SCRUM-33).

## Prompts

### Prompt 1 · Política térmica (commit `971cbd5`)

```text
Crea Safety/Domain/ThermalPolicy.swift, un núcleo puro sin ARKit ni UIKit: estado térmico y Modo
de Bajo Consumo → DetectionLoad (fps objetivo, pausa, Hz de la malla). Nominal 15 fps, fair 10,
serious 5 y critical en pausa; Bajo Consumo baja un escalón. La malla LiDAR va a 2,5 Hz y se
apaga en serious, critical o con Bajo Consumo. En DetectionPipeline lee ProcessInfo en cada frame,
limita los fps y emite una sola transición de pausa térmica por episodio; SafetyService avisa la
pausa (P1) y la reanudación (P2). El delegado de ARSession corre en una cola propia, fuera del hilo
principal. Pruebas en ThermalPolicyTests.
```

### Prompt 2 · Telemetría de rendimiento (commits `971cbd5` y `8722eae`)

```text
Agrega DetectionTelemetry (solo Debug): fps procesados, latencia de inferencia y frames
descartados, con un resumen en el Logger cada 30 s. logSummaryIfDue es mutating y el Logger evalúa
cada valor en un autoclosure, así que copia dropped a una constante antes de registrarlo; sin eso
el build de Debug (swift test) no compila.
```

## Verificación final

- `swift test --filter ThermalPolicyTests` pasa y el build de Debug compila.
- En una sesión larga en el iPhone, el resumen de telemetría muestra fps dentro de 10–15 y la detección baja de carga al calentarse.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| LumioFrontend | `971cbd5` | 2026-11-25 | feat: integracion develop, desniveles y mesas, SCRUM-320/36/360/321/31 |
| LumioFrontend | `8722eae` | 2026-11-25 | Corregir la compilación en Debug de la telemetría de detección |
