# SCRUM-5 · HU: Cerrar Sesión (incluye el bug SCRUM-360)

| | |
|---|---|
| Responsable (Jira) | Tulio Riaño |
| Estado Jira | Finalizado (el bug SCRUM-360 tiene su arreglo en `ce437bb`) |
| Repositorios | `Lumio` (backend) y `LumioFrontend` |
| Commits | 2 (2026-10-26 y 2026-11-24) |
| Depende de | SCRUM-2 (sesiones y refresh) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario autenticado de Lumio quiero cerrar sesión para impedir que otra persona pueda acceder a
> mi cuenta desde el dispositivo.

**Criterios de aceptación**
- El usuario puede pedir el cierre de sesión.
- Se elimina o invalida la sesión activa del dispositivo.
- El usuario deja de considerarse autenticado.
- No se accede a funciones con autenticación sin volver a iniciar sesión.
- Se confirma que la sesión fue cerrada.

**Bug relacionado (SCRUM-360):** al cerrar sesión con una ruta activa, la cámara y las indicaciones
seguían activas.

## Prompts

### Prompt 1 · Logout en el backend (commit `d602871`)

```text
Implementa POST /users/logout {refresh_token}: resuelve la sesión con ese refresh y la revoca
(revoked_at = ahora). Responde 204. Con un token inválido o ya revocado responde 401 "Sesión no
válida". Después del logout, el access token de esa sesión debe dejar de funcionar en /users/me
porque get_current_user ya comprueba revoked_at.
Pruebas en tests/modules/users/test_logout.py: logout correcto, el access deja de servir, el
refresh deja de servir, doble logout y token inválido.
```

### Prompt 2 · Cerrar sesión en la app

```text
En Preferencias agrega «Cerrar sesión» con confirmación. SignOutService llama POST /users/logout
(sin bloquear si no hay red), borra los tokens de Keychain, borra la ruta local y las rutas
recientes, vacía la cola de historial pendiente (no subirla con otra cuenta) y detiene el audio.
Locuta «Sesión cerrada» y vuelve a la bienvenida.
```

### Prompt 3 · Teardown central de la sesión (commit `ce437bb`, bug SCRUM-360)

```text
Bug SCRUM-360: si cierro sesión con una ruta activa, la cámara y las indicaciones siguen.
Además, cuando el refresh caduca, AuthorizedHTTPClient borra la sesión y eso no debería apagar
una ruta en curso. Propón primero el diseño y luego impleméntalo:
- Users/Domain/CurrentAccount: quién está autenticado, observable por la app.
- Users/Application/SessionTeardown: un único punto que, al cerrar sesión a propósito, detiene
  la detección y la cámara, finaliza o descarta la ruta activa, cancela los contextos de audio de
  la ruta y de seguridad, vacía la cola de FinishedRouteSynchronizer y borra datos locales de la
  cuenta. SignOutService lo usa.
- Users/Application/SessionExpiryCoordinator: cuando la sesión expira (refresh rechazado), NO
  apaga la ruta: la guía sigue con la copia local, se avisa por audio que hay que volver a
  iniciar sesión y el teardown corre cuando el usuario sale de la ruta o vuelve a la bienvenida.
- SessionAudio con los textos de ambos casos.
- RemoteAuthenticationService y AuthorizedHTTPClient notifican la expiración al coordinador en
  lugar de borrar todo directamente. Conéctalo en AppDependencies y RootView.
Pruebas en SessionTeardownTests: cerrar sesión con ruta activa detiene cámara y audio; expirar
con ruta activa la conserva; después de expirar, salir limpia todo; no queda historial de una
cuenta para la siguiente. Ajusta RouteFinishTests si cambia la firma del sincronizador.
```

## Verificación final

- `pytest -rs`: logout revoca la sesión y los tokens dejan de servir.
- En el iPhone: cerrar sesión con ruta activa apaga cámara e indicaciones y vuelve a la bienvenida.
- Al traer develop volvió una asignación duplicada de `authenticationService` en AppDependencies;
  `8b74bdc` deja solo la de SCRUM-360.

## Commits cubiertos

| Commit | Repo | Fecha | Autor | Mensaje |
|---|---|---|---|---|
| `d602871` | Lumio | 2026-10-26 | Tulio Riaño | SCRUM-5 HU: Implement logout revoking the session |
| `ce437bb` | LumioFrontend | 2026-11-24 | Samuel Gil | fix(SCRUM-360): teardown central de sesion; la expiracion no apaga la ruta activa |
| `8b74bdc` | LumioFrontend | 2026-11-25 | Daniel Patiño | Quitar la asignación duplicada de authenticationService |
