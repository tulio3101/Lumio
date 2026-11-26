# Prompts por HU · Lumio

Un archivo por historia de usuario con commits en `Lumio` (backend FastAPI) o `LumioFrontend` (iOS).
Cada archivo trae la HU y sus criterios tal como están en Jira, la secuencia de prompts para
llevarla de cero a terminada, la verificación final y la lista de commits que cubre.

**Cómo se hicieron.** Los prompts se reconstruyeron a partir de los commits (mensaje, archivos
tocados y documentación que dejaron en el repo) y de la HU en Jira. No son el historial literal
de chat de cada integrante: son los prompts que reproducen ese trabajo en el mismo orden. Cada
prompt indica el commit que le corresponde. Los valores (umbrales, endpoints, códigos de error)
salen del código y de `README.md` / `docs/` de cada repo.

## Índice

| HU | Título | Responsable (Jira) | Estado Jira | Repos |
|---|---|---|---|---|
| [SCRUM-316](SCRUM-316_Pipeline_compilacion_distribucion.md) | Pipeline de compilación y distribución gratuita | Daniel Patiño | Finalizado | iOS |
| [SCRUM-317](SCRUM-317_Esqueleto_backend_contratos.md) | Esqueleto del backend FastAPI y contratos | Tulio Riaño | Finalizado | Backend |
| [SCRUM-318](SCRUM-318_Infraestructura_AWS_CICD.md) | Infraestructura base en AWS y CI/CD | Juan Sebastián Puentes | Finalizado | Backend |
| [SCRUM-43](SCRUM-43_Gestionar_cola_de_mensajes.md) | Gestionar cola de mensajes | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-45](SCRUM-45_Mensajes_duplicados_obsoletos.md) | Mensajes duplicados u obsoletos | Daniel Patiño | Finalizado | iOS |
| [SCRUM-1](SCRUM-1_Crear_Cuenta.md) | Crear cuenta | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-2](SCRUM-2_Iniciar_Sesion.md) | Iniciar sesión | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-5](SCRUM-5_Cerrar_Sesion.md) | Cerrar sesión (incluye bug SCRUM-360) | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-6](SCRUM-6_Personalizar_Cuenta.md) | Personalizar cuenta | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-7](SCRUM-7_Eliminar_Cuenta.md) | Eliminar cuenta | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-8](SCRUM-8_Crear_Ruta.md) | Crear ruta | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-9](SCRUM-9_Modificar_Ruta.md) | Modificar ruta | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-23](SCRUM-23_Consultar_Ruta_Actual.md) | Consultar ruta actual | Daniel Patiño | Finalizado | iOS |
| [SCRUM-24](SCRUM-24_Consultar_Rutas_Recientes.md) | Consultar rutas recientes | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-10](SCRUM-10_Finalizar_Ruta.md) | Finalizar ruta | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-26](SCRUM-26_Recalcular_Ruta.md) | Recalcular ruta | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-33](SCRUM-33_Detectar_clasificar_obstaculos.md) | Detectar y clasificar obstáculos | Samuel Gil | Finalizado | iOS |
| [SCRUM-320](SCRUM-320_Distancia_con_profundidad.md) | Estimar distancia con profundidad | Samuel Gil | Por hacer (subtareas hechas) | iOS |
| [SCRUM-36](SCRUM-36_Baja_luminosidad.md) | Detección de baja luminosidad | Samuel Gil | Por hacer (hay commit) | iOS |
| [SCRUM-37](SCRUM-37_Manejo_errores_modelo.md) | Manejo de errores del modelo | Néstor López | Finalizado | iOS |
| [SCRUM-315](SCRUM-315_Permisos_accesibles.md) | Solicitar permisos de forma accesible | Néstor López | Finalizado | iOS |
| [SCRUM-30](SCRUM-30_Interactuar_mediante_voz.md) | Interactuar mediante voz | Néstor López | Finalizado | iOS |
| [SCRUM-27](SCRUM-27_Preferencias_de_voz.md) | Preferencias de voz | Néstor López | En revisión | Backend + iOS |
| [SCRUM-28](SCRUM-28_Retroalimentacion_haptica.md) | Retroalimentación háptica | Néstor López | En revisión | Backend + iOS |
| [SCRUM-356](SCRUM-356_Pantalla_principal_accesible.md) | Pantalla principal accesible | Néstor López | En revisión | iOS |
| [SCRUM-319](SCRUM-319_Contactos_de_confianza.md) | Contactos de confianza | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-35](SCRUM-35_Boton_de_emergencia.md) | Botón de emergencia | Daniel Patiño | Finalizado | Backend + iOS |

El orden de la tabla es el orden en que se construyó el producto: primero la base (pipeline,
backend, infraestructura, árbitro de audio), luego cuenta, rutas, seguridad, accesibilidad y
emergencia.

## Diferencias entre Jira y los repos

- **SCRUM-36** sigue en *Por hacer* en Jira, pero `LowLightDetector` está en el commit `694ded1`.
- **SCRUM-320** está en *Por hacer*, pero sus subtareas SCRUM-219 y SCRUM-349 están finalizadas
  y tienen commits.
- **SCRUM-1 y SCRUM-2** piden también registro e inicio de sesión con Google. No hay commits de
  Google en el backend; la pantalla iOS ya muestra el botón. Está marcado en cada archivo.
- **SCRUM-5**: el bug SCRUM-360 (la cámara seguía activa tras cerrar sesión) tiene su arreglo en
  `ce437bb` y Jira lo sigue mostrando en *Por hacer*.
- **SCRUM-27, 28 y 356** están en *En revisión*. Sus docs dicen que la compilación y las pruebas
  quedaron pendientes de CI.
- Commits sin código de HU que se asignaron por contenido: `1665163` y `1b10ed3` → SCRUM-316;
  `cff9ce9` → SCRUM-1/2; `426b78c` → SCRUM-30; `e5e1950`, `f10e9f3` → SCRUM-315;
  `c1cbbee`, `54c614d` → SCRUM-27; `86619dc` → SCRUM-28; `da0bde3` → SCRUM-356;
  `5a7d643`, `046079c` → SCRUM-27 y SCRUM-28.
