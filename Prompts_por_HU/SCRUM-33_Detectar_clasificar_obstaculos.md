# SCRUM-33 · HU: Detectar y Clasificar Obstáculos

| | |
|---|---|
| Responsable (Jira) | Samuel Gil |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 21 (2026-10-27 → 2026-11-25), incluye subtareas SCRUM-215, 216, 217, 218, 221, 223 |
| Rama | `feature/SCRUM-33-deteccion` |
| Base | Spikes SCRUM-306 (YOLO26n en Core ML) y SCRUM-307 (LiDAR) / ADR-306, ADR-307 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario con discapacidad visual, quiero que Lumio detecte y clasifique obstáculos frente a mí
> para identificar posibles riesgos durante mi desplazamiento.

**Criterios de aceptación**
- Procesa imágenes de la cámara en el dispositivo.
- Identifica clases soportadas (subconjunto de COCO relevante para la movilidad).
- Cada detección tiene clase y ubicación en la imagen.
- Funciona sin Internet; un fallo de red no detiene la detección.
- Se ejecuta continuamente durante la navegación.

Alcance: la distancia es SCRUM-320 y el rendimiento SCRUM-321. Escalón, bordillo y puerta quedan para v2.

## Prompts

### Prompt 1 · Modelo Detection y clases (SCRUM-215, commit `5fc098c`)

```text
Empezamos el loop rápido de seguridad, 100 % en el iPhone (ADR-306). En Features/Safety/Domain
crea Detection (obstacleClass, confidence, boundingBox normalizado 0…1 con origen arriba a la
izquierda, distanceMeters opcional para SCRUM-320) y ObstacleClass, un enum con el subconjunto de
COCO útil para caminar (persona, bicicleta, carro, moto, bus, camión, semáforo, hidrante, pare,
parquímetro, banca, perro, silla, matera, mesa…) con su nombre en español. Agrega el target de
tests de Safety a Package.swift.
```

### Prompt 2 · Captura con ARKit (SCRUM-216, commits `151df9f`, `1fa1817`)

```text
Crea FrameSourceContracts (FrameSource que publica frames con pixel buffer, profundidad opcional
y timestamp) y ARKitFrameSource con ARWorldTrackingConfiguration y frameSemantics .sceneDepth si
el dispositivo tiene LiDAR. No retengas ARFrames: si el pipeline está ocupado, descarta el frame.
Luego: el gate actual con una Task no basta y ARKit avisa que se retienen frames. Cambia a un
gate sincrónico con OSAllocatedUnfairLock que se toma antes de entregar el frame y se libera al
terminar la inferencia.
```

### Prompt 3 · YOLO en Core ML con Vision (SCRUM-217, commits `003d4c3`, `43db19c`)

```text
Crea YOLORunner: carga yolo26n_640_int8 (el NMS ya va dentro del modelo, así que Vision devuelve
VNRecognizedObjectObservation), VNCoreMLRequest, VNImageRequestHandler con orientación .right,
umbral de confianza 0.45 y solo clases de ObstacleClass. BoundingBoxHelper convierte las cajas de
Vision (origen abajo) a nuestro sistema (origen arriba). Después agrega logs de diagnóstico de la
ruta del bundle del modelo y del tipo de observación que devuelve Vision, porque en el iPhone no
encuentra el modelo.
```

### Prompt 4 · Pipeline en tiempo real (SCRUM-218, commits `14995ed`, `07ba267`)

```text
Crea DetectionPipeline: recibe frames de ARKitFrameSource, corre YOLORunner fuera del hilo
principal, añade la distancia cuando hay profundidad y publica las detecciones. Luego: libera el
gate con defer para que un error no lo deje tomado, y limita los logs de detección a uno por
segundo.
```

### Prompt 5 · Servicio, dependencias y compilación iOS (commits `76dbabf`, `9a41c20`, `9a36f5f`)

```text
Crea SafetyService que arranca y detiene el pipeline y entrega los avisos al AudioArbiter. Arregla
los errores de compilación iOS en LowLightDetector, SafetyService y DepthSampler, y conecta
SafetyService en AppDependencies. Saca lumio.xcodeproj del repo y agrégalo al .gitignore: lo
genera XcodeGen.
```

### Prompt 6 · Sin Internet y textos en español (SCRUM-221, commit `793ff96`)

```text
Escribe pruebas de arquitectura que fallen si algo de Features/Safety importa HTTPClient, URLSession
o el módulo de red: el loop de seguridad no puede depender de Internet. Agrega pruebas del formato
de distancia en español con coma decimal («1,5 metros»).
```

### Prompt 7 · Avisos sin saturar (SCRUM-223, commit `0ec9991`)

```text
En SafetyService evita repetir avisos: como máximo uno cada 4 s por clase, nombres en español y
tres niveles de distancia: < 1 m inmediato (P1, interrumpe), 1–4 m normal (P3) y > 4 m «a más de
4 metros» (P3). Siempre en metros con un decimal y coma («0,3 metros»): nos apartamos de ADR-307,
que usaba centímetros bajo 1 m y silenciaba lo de más de 4 m; deja la nota en el código. Si hay
varias detecciones de la misma clase, anuncia la más cercana.
```

### Prompt 8 · Modelo empaquetado, ciclo de vida y overlay de depuración (commits `ad95763`, `2326584`, `f69930a`)

```text
- Agrega Resources/yolo26n_640_int8.mlpackage a Compile Sources en project.yml y para la app usa
  scenePhase: detener la detección al ir a segundo plano y retomarla al volver.
- Solo en builds DEBUG, crea DebugSafetyView con la vista de cámara, las cajas y los FPS, y un
  DebugSafetyContainer accesible desde DestinationView.
- Pinta las cajas en verde y deja 10 clases COCO de interiores para probar en el salón.
```

### Prompt 9 · Suavizado temporal y confianza por clase (commit `6cc4bb3`)

```text
Hay falsos positivos de un frame. Agrega TemporalSmoother (una detección se confirma si aparece en
varios frames seguidos) y ClassConfidencePolicy con umbral por clase: persona 0,55; bicicleta,
carro, moto, bus y camión 0,50; silla, banca y matera 0,45; resto 0,50. LowLightDetector y
ARKitFrameSource se adaptan al nuevo contrato del frame.
```

### Prompt 10 · Arrancar con la ruta y gate de cámara (commits `fad20b1`, `7752267`)

```text
La detección no debe estar siempre encendida. Haz que DestinationViewModel la arranque al empezar
una ruta y la detenga al terminarla. Crea ObstacleAssistanceGate (SCRUM-315): decide si la cámara
permite arrancar; nunca bloquea la navegación: sin permiso la ruta sigue y avisa una sola vez por
sesión que va sin detección. Separa ObstacleDetectionPipeline, ObstacleAnnouncer y SafetyAudio
(todo el audio de seguridad en el contexto "safety") y haz que las alertas caduquen en el árbitro
para no anunciar un obstáculo que ya pasó. Además, Info.plist se sobrescribía: deja una sola
fuente de verdad en project.yml.
```

### Prompt 11 · Exteriores, profundidad y desniveles (commit `944435d`)

```text
En exteriores avisa de todo lo que ve. Rediseña sobre DetectionFocusConfig (todo configurable):
- ObstacleTracker: asocia detecciones entre frames por IoU 0,3, descarta un track tras 5 frames
  sin verlo y lo confirma con 3 apariciones en 5 frames (PersistenceGate).
- WalkingCorridor: solo cuenta lo que está en el 40 % central y la mitad inferior de la imagen; el
  corredor se corre 0,01 por grado de giro.
- Inclinación: fuera de −35°…35° se recuerda cómo sostener el teléfono (PhonePitchReminder, cada 6 s).
- Relevancia por acercamiento: avisa si se acerca más de 0,15 m o está a menos de 1 m (peligro);
  4 s de espera por track.
- CorridorDepthSampler + DepthObstacleDetector + DepthObstacleFusion: obstáculos sin clase a partir
  de la profundidad del corredor (franja de piso 0,12 m, elevación entre 0,5 y 3 m) y desniveles:
  bajada o subida de 0,10 m, con al menos 3 muestras de piso y 2 huecos seguidos.
- MeshClassificationStore con la malla de ARKit para nombrar paredes, puertas o escalones
  (MeshObstacleName).
Pruebas para el tracker, el corredor, la fusión de profundidad, la persistencia y la relevancia.
```

### Prompt 12 · Compilación portable en CI (commits `167888c`, `831b085`)

```text
La CI de SwiftPM en Linux falla: accessibilityAction(.magicTap) y el @main no existen fuera de
iOS, y un test usa APIs de iOS. Protégelos con #if os(iOS) / canImport sin cambiar el
comportamiento en el iPhone. En ObstacleAnnouncerTests cambia a let el anunciador que no se muta.
```

## Verificación final

- `swift test` pasa las pruebas de Safety en Linux y macOS; el loop no importa red.
- En el iPhone: con una ruta activa y en modo avión, una persona o silla en el corredor se anuncia
  con su distancia; las que están a un lado no; < 1 m interrumpe la navegación.
- Rendimiento medido en el spike: ~30 fps y 8,8 ms por frame (SCRUM-306).

## Commits cubiertos

| Commit | Fecha | Mensaje |
|---|---|---|
| `5fc098c` | 2026-10-27 | SCRUM-215: Add Detection model and ObstacleClass enum |
| `151df9f` | 2026-10-27 | SCRUM-216: Captura de frames con ARKit |
| `003d4c3` | 2026-10-27 | SCRUM-217: Integrar modelo YOLO para detectar obstáculos |
| `14995ed` | 2026-10-27 | SCRUM-218: Pipeline de detección en tiempo real con distancia |
| `76dbabf` | 2026-10-27 | Fix errores de compilación iOS en el pipeline de seguridad |
| `9a41c20` | 2026-10-27 | Conectar SafetyService en AppDependencies |
| `9a36f5f` | 2026-10-28 | chore: excluir lumio.xcodeproj del repo (generado por XcodeGen) |
| `1fa1817` | 2026-10-28 | SCRUM-216: gate sincrónico con OSAllocatedUnfairLock |
| `43db19c` | 2026-10-28 | SCRUM-217: logs de diagnóstico para bundle path y tipo de observación Vision |
| `07ba267` | 2026-10-28 | SCRUM-218: defer para liberar gate en el pipeline y throttle de logs |
| `793ff96` | 2026-10-28 | SCRUM-221: tests de arquitectura offline y formato de distancia en español |
| `0ec9991` | 2026-10-28 | SCRUM-223: throttle de anuncios por clase, tiers de distancia y nombres en español |
| `ad95763` | 2026-10-28 | feat: modelo YOLO en Compile Sources, project.yml y lifecycle con scenePhase |
| `2326584` | 2026-10-28 | feat: overlay de debug con preview de cámara y bounding boxes (solo DEBUG) |
| `f69930a` | 2026-10-28 | feat: cajas de detección en verde y 10 clases COCO interiores |
| `6cc4bb3` | 2026-11-12 | SCRUM-33: suavizado temporal y politica de confianza por clase (wip) |
| `fad20b1` | 2026-11-12 | feat(safety): arrancar deteccion con la ruta, gate de camara y obsolescencia de alertas |
| `7752267` | 2026-11-12 | fix(build): Info.plist con una sola fuente de verdad |
| `944435d` | 2026-11-19 | SCRUM-33: wip exteriores, profundidad y desniveles |
| `167888c` | 2026-11-19 | fix(ci): compilacion portable (magicTap, guard de tests y @main en SwiftPM) |
| `831b085` | 2026-11-25 | test: use let for unmutated announcer |

El permiso de cámara con el flujo accesible (`995618d`) está en [SCRUM-315](SCRUM-315_Permisos_accesibles.md).
