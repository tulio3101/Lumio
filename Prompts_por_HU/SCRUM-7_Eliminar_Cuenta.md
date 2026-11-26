# SCRUM-7 · HU: Eliminar Cuenta

| | |
|---|---|
| Responsable (Jira) | Tulio Riaño (commits de Daniel Patiño) |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 11 (5 backend, 6 iOS; 2026-11-20) |
| Rama | `SCRUM-7-hu-eliminar-cuenta` |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero eliminar mi cuenta para dejar de usar el servicio y borrar la
> información asociada.

**Criterios de aceptación**
- Se pide desde la app, con confirmación explícita por audio que evita accidentes.
- Se informan las consecuencias.
- Confirmada, la cuenta deja de estar disponible.
- Se borran la cuenta y sus datos: contactos de confianza, historial de rutas y preferencias.
- No se puede volver a iniciar sesión con ella.
- Flujo usable con VoiceOver.

Por confirmar en Jira: si algún dato se conserva por razones legales (se asume que no).

## Prompts · Backend

### Prompt 1 · Borrado en cascada (commit `8f8ff70`)

```text
Eliminar Cuenta (SCRUM-7): al borrar el usuario debe desaparecer todo lo que lo referencia.
Revisa que las FK hacia users (auth_sessions, routes) ya tengan ondelete="CASCADE"; si es así,
no hace falta migración. Implementa repository.delete_user y service.delete_account en una sola
transacción, con excepciones propias en users/exceptions.py (fallo de borrado y base no
disponible). Deja anotado que las tablas futuras (contactos de confianza, eventos SOS) deben
declarar su FK con CASCADE.
```

### Prompt 2 · Endpoint (commit `f8bc3bd`)

```text
Expón DELETE /users/me con Authorization: Bearer: 204 sin cuerpo. Después sus tokens responden
401 y el login con ese correo 401; el correo puede registrarse de nuevo como cuenta vacía.
Errores: 401 invalid_session, 500 account_deletion_failed y 503 database_unavailable (en ambos
casos la cuenta sigue intacta).
```

### Prompt 3 · Pruebas y documentación (commits `212d43e`, `33e9c98`, `5621d7a`)

```text
Pruebas unitarias del servicio y del router, y de integración con Postgres: se borran sesiones de
todos los dispositivos, la ruta activa y el historial; los tokens dejan de servir; el login falla;
volver a registrar el correo da una cuenta vacía; un fallo deja todo intacto. Documenta el
endpoint en el README.
```

## Prompts · iOS

### Prompt 4 · Borrar en el backend y olvidar en el teléfono (commit `2c23137`)

```text
Crea AccountDeletionService y RemoteAccountService (DELETE /users/me con AuthorizedHTTPClient,
que renueva el access token una vez si hace falta). Solo con 204 se borra el teléfono: se
descarta el historial pendiente (no se envía), la ruta activa, las rutas recientes, los tokens y
las preferencias locales; se reinicia el árbitro y se anuncia «Cuenta eliminada…». Errores
(sin conexión, 500/503, sesión rechazada) se locutan y la cuenta sigue; con sesión rechazada se
borran los tokens y se vuelve a la bienvenida. Un segundo toque mientras se elimina se ignora.
```

### Prompt 5 · Pantalla con dos confirmaciones habladas (commit `9a397e6`)

```text
Crea DeleteAccountView:
1. Al entrar explica las consecuencias (cuenta, contactos, historial y preferencias; no se puede
   deshacer). Sin VoiceOver las locuta el servicio por el árbitro (contexto account-deletion);
   con VoiceOver el foco va a la explicación para no hablar a la vez. «Escuchar de nuevo» la repite.
2. «Eliminar mi cuenta» abre la última confirmación («Eliminar definitivamente» / «Cancelar»),
   también locutada sin VoiceOver. Cancelar corta ese audio.
```

### Prompt 6 · Entrada en Preferencias, pruebas y documentación (commits `5f4c358`, `9b49513`, `f136e54`, `e947220`)

```text
Agrega «Eliminar cuenta» en Preferencias. Escribe pruebas unitarias del servicio (solo borra con
204, cada error conserva todo, doble toque) e integración con árbitro, disco y backend falsos (no
se sube historial pendiente, se borran ruta, recientes y tokens). Documenta en
docs/ARCHITECTURE.md.
```

## Verificación final

- Backend: `pytest -rs` comprueba la cascada y que los tokens y el login dejan de funcionar.
- iOS: con VoiceOver se escuchan las consecuencias, se confirma dos veces y la app vuelve a la
  bienvenida; en modo avión dice que no se pudo y la cuenta sigue.

## Commits cubiertos

| Commit | Repo | Mensaje |
|---|---|---|
| `8f8ff70` | Lumio | Delete the account and everything that references it in cascade |
| `f8bc3bd` | Lumio | Implement endpoint to delete the authenticated account |
| `212d43e` | Lumio | Add unit tests for deleting the account |
| `33e9c98` | Lumio | Add Postgres integration tests for deleting the account |
| `5621d7a` | Lumio | Document the delete account endpoint |
| `2c23137` | LumioFrontend | Delete the account in the backend and forget it on the phone |
| `9a397e6` | LumioFrontend | Add the delete account screen with two spoken confirmations |
| `5f4c358` | LumioFrontend | Add the delete account action to Preferences |
| `9b49513` | LumioFrontend | Add unit tests for deleting the account |
| `f136e54` | LumioFrontend | Add integration tests for deleting the account with audio, disk and backend |
| `e947220` | LumioFrontend | Document account deletion |
