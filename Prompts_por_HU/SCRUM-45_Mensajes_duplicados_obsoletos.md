# SCRUM-45 · HU: Gestionar Mensajes Duplicados u Obsoletos

| | |
|---|---|
| Responsable (Jira) | Daniel Patiño |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 1 (2026-10-25) |
| Depende de | SCRUM-43 (cola y árbitro) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero que el sistema descarte mensajes de audio duplicados u obsoletos para
> recibir información relevante sin repeticiones innecesarias.

**Criterios de aceptación**
- Identifica duplicados según reglas definidas.
- Descarta obsoletos antes de reproducirse.
- Una narración de una captura antigua no suena si hay información más reciente.
- Los mensajes de seguridad no se descartan solo por parecerse a otros.
- El descarte no afecta el funcionamiento de la cola.
- Se mantiene el orden y la prioridad de los mensajes válidos.

## Prompts

### Prompt 1 · Diseño del contrato

```text
Sobre el AudioArbiterService de SCRUM-43 quiero descartar duplicados y narraciones viejas. Antes
de escribir código propón el contrato que deben cumplir los productores y las reglas, y
espérame. Mi idea:
- deduplicationKey: identidad estable del evento, no el texto;
- contextID: grupo comparable (ruta, giro o escena);
- captureSequence: UInt64 creciente asignado al capturar la imagen, no al recibir la narración.
P1 nunca se descarta por clave ni por captura.
```

### Prompt 2 · Implementación (commit `9870b09`)

```text
Implementa la política acordada en Domain/AudioDeduplicationPolicy.swift y úsala en
AudioArbiterService. Reglas:
1. Un UUID activo o pendiente repetido se ignora sin cambiar el original.
2. P2/P3 con misma clave no vacía, mismo contexto no vacío y misma prioridad son duplicados
   mientras el anterior siga relevante y activo o pendiente; el nuevo se notifica como
   descartado. Sin clave o sin contexto no se aplica el filtro.
3. P1 no participa en deduplicación por clave ni por captura (sí en vencimiento, contexto y UUID).
4. Un P3 de captura más reciente reemplaza los pendientes de capturas anteriores del mismo
   contexto, sin interrumpir una narración que ya suena.
5. Solo un mensaje aceptado actualiza la última secuencia del contexto; una respuesta con
   secuencia menor se descarta aunque la reciente ya haya terminado. Secuencias iguales no
   son antiguas.
6. Guarda solo la última secuencia aceptada por contexto; se libera al invalidar el contexto o
   con resetSession(), que además detiene el audio, vacía la cola e invalida callbacks.
7. Los supervivientes conservan su orden; la narración nueva entra en su posición real de llegada.
Limpia los vencidos antes de comparar duplicados. Agrega los campos a AudioMessage y al contrato.
Escribe Tests/LumioFrontendTests/AudioDeduplicationTests.swift con un escenario por regla
(duplicados activos/pendientes, UUID, contextos y prioridades distintas, metadatos ausentes,
protección P1, reemplazo, respuestas fuera de orden, FIFO, expiración y limpieza de sesión)
y ajusta AudioArbiterTests si hace falta. Documenta el contrato en docs/ARCHITECTURE.md y el README.
```

## Verificación final

- `swift test --cache-path /tmp/lumio-swift-cache`: 23 pruebas pasan (13 previas + 10 nuevas).
- Validación con reproductor simulado; la integración con productores reales queda para sus HUs.

## Commits cubiertos

| Commit | Fecha | Mensaje |
|---|---|---|
| `9870b09` | 2026-10-25 | Manage duplicated or obsolence messages implemented |
