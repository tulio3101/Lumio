# SCRUM-356 · HU: Pantalla Principal Accesible

| | |
|---|---|
| Responsable (Jira) | Néstor López |
| Estado Jira | En revisión |
| Repositorio | `LumioFrontend` (sin cambios de backend) |
| Commits | 1 (2026-11-25) |
| Integra | SCRUM-313 (punto de entrada), SCRUM-35, SCRUM-23, SCRUM-30 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario con discapacidad visual, quiero una pantalla principal que pueda usar solo con VoiceOver
> y gestos, para iniciar una ruta, activar la emergencia y abrir los ajustes sin depender de la vista.

**Criterios de aceptación**
- La app abre en una pantalla principal usable solo con VoiceOver y gestos.
- Desde ella se dicta un destino, se activa la emergencia, se consulta la ruta y se abren los ajustes.
- Controles grandes, etiquetas claras y orden lógico.
- Al abrir informa por audio: sesión, permisos y seguridad lista.
- No requiere información visual.
- Dictar destino y emergencia tienen gesto o acción rápida.

## Prompts

### Prompt 1 · Estado al abrir (commit `da0bde3`, parte 1)

```text
Implementa SCRUM-356. La pestaña Trayecto (DestinationView) es la pantalla principal. Primero el
estado al abrir: crea Features/Home/Domain/HomeStatus y Application/HomeStatusService. Arma el
mensaje con datos locales (HomeAnnouncements.welcome) y locútalo una vez por apertura como P2
(contexto home-status), para que una alerta crítica lo interrumpa:
- sesión: «Sesión iniciada.» o, en el modo de desarrollo sin sesión, que las rutas no se guardan;
- permisos esenciales (ubicación, micrófono, reconocimiento de voz): nombra solo los negados,
  restringidos o desactivados y dónde concederlos; abrir la app no pide nada;
- seguridad: «Detección de obstáculos lista: se activa al iniciar una ruta.» si el modelo está en
  la app y la cámara no está negada; si no, por qué no está disponible;
- ruta activa guardada, si hay, y cómo usar las acciones rápidas.
```

### Prompt 2 · Orden, controles y gestos (commit `da0bde3`, parte 2)

```text
Reorganiza DestinationView para VoiceOver, de arriba abajo: encabezado «Lumio, trayecto»; «Estado
de Lumio. …» (el mismo texto que se locuta; doble toque lo repite); «Indicar destino por voz»
(con ruta activa «Cambiar destino por voz») como botón principal; «¿Cómo voy?»; «Ajustes» (cambia
a Preferencias); la ruta activa o el estado sin ruta y «Rutas recientes»; el botón de Emergencia
fijo abajo; el botón «Comando de voz». Quita la tarjeta «Próximamente».
Gestos: el Magic Tap dicta un destino (y cierra la escucha si está abierta); en ActiveRouteView el
Magic Tap sigue repitiendo la indicación. Acciones del rotor en los elementos 2 a 5: «Indicar
destino por voz» y «Emergencia». No pongas la emergencia en el Magic Tap: es fácil hacerlo sin
querer.
Agrega VoiceCommandService.startDestinationDictation(): pregunta «¿A dónde quieres ir?» sin el «Te
escucho» y sigue el flujo de «nueva ruta»; sin servicio de voz abre la búsqueda escrita. Ahí se
conectará el dictado de SCRUM-313.
Pruebas: HomeStatusTests (una vez por apertura y P2, repetir a pedido, permisos negados nombrados,
seguridad sin cámara o sin modelo, ruta activa, modo sin sesión) y un caso nuevo en
VoiceCommandServiceTests. Documenta en docs/HU-pantalla-principal-accesible.md con la validación
con la cortina de pantalla.
```

## Verificación final

- `swift test` pasa HomeStatusTests y VoiceCommandServiceTests.
- En el iPhone con VoiceOver y la cortina de pantalla: al abrir se oye el estado una vez; deslizar
  recorre el orden indicado; el Magic Tap pregunta el destino y crea la ruta; desde el rotor se
  activa «Emergencia».
- La HU sigue En revisión; el doc deja compilación y pruebas pendientes de CI.

## Commits cubiertos

| Commit | Fecha | Mensaje |
|---|---|---|
| `da0bde3` | 2026-11-25 | HU: Pantalla principal accesible |
