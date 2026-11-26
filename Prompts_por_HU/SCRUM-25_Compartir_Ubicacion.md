# SCRUM-25 · HU: Compartir Ubicación

| | |
|---|---|
| Responsable (Jira) | Juan Sebastián Puentes |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 2 (2026-11-25 → 2026-11-26) |
| Depende de | SCRUM-319 (contactos de confianza), SES |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio quiero compartir mi ubicación durante el trayecto para permitir que una
> persona de confianza pueda conocer mi posición actual.

**Criterios de aceptación**
- El usuario puede iniciar el uso compartido de su ubicación.
- El sistema solicita los permisos necesarios.
- El usuario debe confirmar explícitamente el inicio del uso compartido.
- La ubicación compartida corresponde a la posición actual del usuario.
- El usuario puede detener el uso compartido.
- El sistema informa al usuario cuando la ubicación está siendo compartida.
- Si se pierde la conexión, el sistema informa el estado correspondiente.

## Prompts

### Prompt 1 · Módulo location_sharing en el backend (commit `926a806`)

```text
Crea app/modules/location_sharing (router → service → repository → models) para compartir la
ubicación con los contactos de confianza:
- POST /location-shares {duración 15–240 min, posición inicial}: envía a cada contacto un correo
  por SES con un enlace privado. El token es aleatorio y solo se guarda su hash. Empezar otro
  compartido cierra el anterior.
- PUT /location-shares/{id}/position: reemplaza la última posición (no hay historial). Si ya
  terminó responde 410 location_share_ended.
- DELETE /location-shares/{id}: lo detiene y borra la posición.
- GET /location-shares/view/{token}: página sin sesión con la última posición y un enlace al
  mapa, con Cache-Control no-store, noindex y Referrer-Policy no-referrer.
- message.py arma el correo escapando todo lo que viene de la cuenta.
- Migración 0010_location_shares y PUBLIC_BASE_URL en config (.env.example; deploy.sh la arma
  con API_DOMAIN).
Pruebas en tests/modules/location_sharing/ y tests/integration/test_location_sharing_api.py.
```

### Prompt 2 · Compartir desde la app (commit `8ccb84c`)

```text
Agrega Features/LocationSharing en la app:
- LocationSharingService: pide confirmación explícita antes de empezar, verifica el permiso de
  ubicación, crea el compartido (POST /location-shares) y manda la posición cada 30 s. Sin
  conexión lo dice una vez y retoma al volver la red. Termina al detenerlo, al vencer (410) o al
  cerrar sesión. Todo se dice por el AudioArbiter como P2.
- RemoteLocationSharingService y los DTO del contrato del backend.
- LocationSharingView en Preferencias > Emergencia y un aviso fijo en Trayecto («Compartiendo tu
  ubicación», con Detener), accesibles con VoiceOver.
- SessionTeardown deja de compartir antes de borrar la sesión.
Pruebas en LocationSharingTests y docs/HU-compartir-ubicacion.md.
```

## Verificación final

- `pytest tests/modules/location_sharing` pasa, con la migración 0010 aplicada.
- `swift test --filter LocationSharingTests` pasa.
- En el iPhone: confirmar el inicio, abrir el enlace del correo en otro equipo y ver la posición actualizada; detenerlo deja el enlace sin posición.
- En modo avión se oye el aviso de conexión perdida y al volver la red se retoma.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| Lumio | `926a806` | 2026-11-25 | SCRUM-25 HU: Compartir ubicación con los contactos de confianza |
| LumioFrontend | `8ccb84c` | 2026-11-26 | SCRUM-25 HU: Compartir ubicación |
