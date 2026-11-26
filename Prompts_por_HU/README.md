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
| [SCRUM-42](SCRUM-42_Prioridad_de_audios.md) | Gestionar prioridad de audios | Juan Sebastián Puentes | Finalizado | iOS |
| [SCRUM-44](SCRUM-44_Interrumpir_narracion.md) | Interrumpir narración ante eventos prioritarios | Juan Sebastián Puentes | Finalizado | iOS |
| [SCRUM-1](SCRUM-1_Crear_Cuenta.md) | Crear cuenta | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-2](SCRUM-2_Iniciar_Sesion.md) | Iniciar sesión (incluye Google, SCRUM-62) | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-3](SCRUM-3_Recuperar_Contrasena.md) | Recuperar contraseña | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-5](SCRUM-5_Cerrar_Sesion.md) | Cerrar sesión (incluye bug SCRUM-360) | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-6](SCRUM-6_Personalizar_Cuenta.md) | Personalizar cuenta | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-7](SCRUM-7_Eliminar_Cuenta.md) | Eliminar cuenta | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-8](SCRUM-8_Crear_Ruta.md) | Crear ruta | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-9](SCRUM-9_Modificar_Ruta.md) | Modificar ruta | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-23](SCRUM-23_Consultar_Ruta_Actual.md) | Consultar ruta actual | Daniel Patiño | Finalizado | iOS |
| [SCRUM-24](SCRUM-24_Consultar_Rutas_Recientes.md) | Consultar rutas recientes | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-10](SCRUM-10_Finalizar_Ruta.md) | Finalizar ruta | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-26](SCRUM-26_Recalcular_Ruta.md) | Recalcular ruta | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-312](SCRUM-312_Guiar_giros.md) | Guiar giros durante el trayecto | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-33](SCRUM-33_Detectar_clasificar_obstaculos.md) | Detectar y clasificar obstáculos (incluye desniveles) | Samuel Gil | Finalizado | iOS |
| [SCRUM-320](SCRUM-320_Distancia_con_profundidad.md) | Estimar distancia con profundidad | Samuel Gil | Finalizado | iOS |
| [SCRUM-34](SCRUM-34_Alertar_proximidad.md) | Alertar proximidad de objetos | Tulio Riaño | Finalizado | iOS |
| [SCRUM-36](SCRUM-36_Baja_luminosidad.md) | Detección de baja luminosidad | Samuel Gil | Finalizado | iOS |
| [SCRUM-37](SCRUM-37_Manejo_errores_modelo.md) | Manejo de errores del modelo | Néstor López | Finalizado | iOS |
| [SCRUM-314](SCRUM-314_Camara_y_seguridad_lista.md) | Preparar la cámara y la seguridad al iniciar | Juan Sebastián Puentes | Finalizado | iOS |
| [SCRUM-321](SCRUM-321_Rendimiento_y_consumo.md) | Optimizar rendimiento y consumo de la detección | Samuel Gil | Finalizado | iOS |
| [SCRUM-315](SCRUM-315_Permisos_accesibles.md) | Solicitar permisos de forma accesible | Néstor López | Finalizado | iOS |
| [SCRUM-30](SCRUM-30_Interactuar_mediante_voz.md) | Interactuar mediante voz | Néstor López | Finalizado | iOS |
| [SCRUM-313](SCRUM-313_Destino_por_voz.md) | Indicar destino por voz | Juan Sebastián Puentes | Finalizado | iOS |
| [SCRUM-27](SCRUM-27_Preferencias_de_voz.md) | Preferencias de voz | Néstor López | Finalizado | Backend + iOS |
| [SCRUM-28](SCRUM-28_Retroalimentacion_haptica.md) | Retroalimentación háptica | Néstor López | Finalizado | Backend + iOS |
| [SCRUM-32](SCRUM-32_Preferencias_de_accesibilidad.md) | Preferencias de accesibilidad | Juan Sebastián Puentes | Finalizado | iOS |
| [SCRUM-31](SCRUM-31_Retroalimentacion_del_sistema.md) | Recibir retroalimentación del sistema | Samuel Gil | Finalizado | iOS |
| [SCRUM-356](SCRUM-356_Pantalla_principal_accesible.md) | Pantalla principal accesible | Néstor López | Finalizado | iOS |
| [SCRUM-29](SCRUM-29_Auditar_VoiceOver.md) | Auditar accesibilidad con VoiceOver | Juan Sebastián Puentes | Finalizado | iOS |
| [SCRUM-319](SCRUM-319_Contactos_de_confianza.md) | Contactos de confianza | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-35](SCRUM-35_Boton_de_emergencia.md) | Botón de emergencia | Daniel Patiño | Finalizado | Backend + iOS |
| [SCRUM-25](SCRUM-25_Compartir_Ubicacion.md) | Compartir ubicación | Juan Sebastián Puentes | Finalizado | Backend + iOS |
| [SCRUM-324](SCRUM-324_Consentimiento_narracion.md) | Consentir el envío de imágenes para la narración | Juan Sebastián Puentes | Finalizado | Backend + iOS |
| [SCRUM-38](SCRUM-38_Narracion_del_entorno.md) | Narración del entorno | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-39](SCRUM-39_Solicitar_narracion.md) | Solicitar narración del entorno | Juan Sebastián Puentes | Finalizado | iOS |
| [SCRUM-40](SCRUM-40_Actualizar_narracion.md) | Actualizar narración ante cambios de entorno | Tulio Riaño | Finalizado | Backend + iOS |
| [SCRUM-41](SCRUM-41_Disponibilidad_narracion.md) | Gestionar disponibilidad de la narración | Samuel Gil | Finalizado | Backend + iOS |

Son 44 HU. La tabla va por módulo, en el orden en que se construyó el producto: la base (pipeline,
backend, infraestructura y audio), cuenta, rutas, seguridad, voz, accesibilidad, emergencia y
narración. Los spikes (SCRUM-305 a 311) no tienen archivo propio: sus decisiones están en los ADR
y los prompts de cada HU los citan.

## Diferencias entre Jira y los repos

- Las 44 HU están en *Finalizado* en Jira, pero muchas de sus **subtareas** siguen en *Por hacer*
  o *En revisión*. Por ejemplo, la SCRUM-62 (inicio de sesión con Google) y la SCRUM-68 (registro
  con Google) están en *Por hacer*, aunque el código está en los commits `4bd4f1f`, `3d7b92b` y
  `87830ea`.
- El bug **SCRUM-360** (la cámara seguía activa tras cerrar sesión) ya no aparece en Jira; su
  arreglo está en `ce437bb` y se documenta en [SCRUM-5](SCRUM-5_Cerrar_Sesion.md).
- Algunos commits los hizo otra persona distinta del responsable en Jira: SCRUM-3 y SCRUM-312
  (Néstor López), SCRUM-38 (Daniel Patiño), SCRUM-41 (Néstor López) y SCRUM-31 (Samuel Gil y
  Daniel Patiño). Cada archivo lo indica.
- `971cbd5` (Samuel Gil) mezcla trabajo de SCRUM-320, 36, 360, 321, 31 y 41; aparece en cada una.
- Commits sin código de HU que se asignaron por contenido: `1665163` y `1b10ed3` → SCRUM-316;
  `cff9ce9` → SCRUM-1/2; `426b78c` → SCRUM-30; `e5e1950`, `f10e9f3` → SCRUM-315;
  `c1cbbee`, `54c614d` → SCRUM-27; `86619dc` → SCRUM-28; `da0bde3` → SCRUM-356;
  `5a7d643`, `046079c` → SCRUM-27 y SCRUM-28; `813eb8e`, `c06a9ee` → SCRUM-3; `dba7322` →
  SCRUM-33; `8722eae` → SCRUM-321; `8b74bdc` → SCRUM-5; `bac7fdc` → SCRUM-3.
- Fuera de las HU quedan los commits iniciales de cada repo y `b1f3587` (esta carpeta).
