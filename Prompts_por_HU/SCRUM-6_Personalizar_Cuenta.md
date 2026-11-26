# SCRUM-6 · HU: Personalizar Cuenta

| | |
|---|---|
| Responsable (Jira) | Tulio Riaño (commits de Daniel Patiño) |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 15 (7 backend, 8 iOS; 2026-11-20) |
| Rama | `SCRUM-6-hu-personalizar-cuenta` |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero modificar la información de mi cuenta para mantener mis datos
> actualizados.

**Criterios de aceptación**
- Se consulta la información configurable de la cuenta.
- Se modifican los datos permitidos, validados antes de guardar.
- Los cambios válidos se guardan.
- Se informa por audio si se guardaron o si hubo error.
- Pantalla usable con VoiceOver.

Alcance: solo datos de perfil. Las preferencias de voz y háptica son de SCRUM-27 y SCRUM-28.

## Prompts · Backend

### Prompt 1 · Nombre y celular en el perfil (commit `e9992f0`)

```text
Personalizar Cuenta (SCRUM-6): el perfil tiene correo (no editable), nombre y celular. Agrega a
User display_name y phone, ambos opcionales, con la migración 0005. GET /users/me debe devolver
email, display_name y phone (los dos últimos pueden ser null).
```

### Prompt 2 · Validación (commit `321bd39`)

```text
Crea en users/schemas.py UserProfileUpdate y PasswordChange:
- display_name: 1–60 caracteres después de recortar y unir espacios, en NFC; solo letras,
  espacios, ', . y -.
- phone: celular colombiano, 10 dígitos que empiezan por 3; acepta espacios y guiones y se
  guarda sin ellos.
- null o "" quitan el dato. Cualquier otro campo (incluido email) responde 422 (extra="forbid").
- PasswordChange: current_password y new_password de 8–128, distinta de la actual
  (password_unchanged).
```

### Prompt 3 · Guardar el perfil y cambiar la contraseña (commit `83c5be9`)

```text
En users/service.py:
- update_profile cambia solo los campos enviados.
- change_password verifica la actual, guarda el hash nuevo y revoca todas las demás sesiones del
  usuario; la sesión de este dispositivo se conserva.
Errores con el formato común: invalid_current_password es 403 (no 401, para que el cliente no
intente renovar la sesión), password_not_set 409 si la cuenta es solo de Google,
profile_update_failed y password_change_failed 500, base caída 503.
```

### Prompt 4 · Endpoints, pruebas y documentación (commits `b5dc35e`, `746479b`, `b5a8b9c`, `57f8e81`)

```text
Expón PATCH /users/me (devuelve la cuenta) y PUT /users/me/password (204). Pruebas unitarias de
schemas y servicio (cada regla, quitar datos, campos extra, contraseña igual) e integración con
Postgres (persistencia, otra sesión queda revocada y esta no, 403 con la actual mala). Documenta
la tabla «Cuenta» en el README con cada código de error.
```

## Prompts · iOS

### Prompt 5 · Detección común de fallos de conexión (commit `d29302e`)

```text
Varias pantallas repiten la misma lógica para saber si un error es de conectividad. Extráela a
una función compartida en Core/Networking y úsala en los servicios existentes, sin cambiar
comportamiento.
```

### Prompt 6 · Modelo y reglas del perfil (commit `3e33a61`)

```text
Crea el modelo de perfil y ProfilePolicy con las mismas reglas que UserProfileUpdate (nombre
1–60 en NFC con letras, espacios, ' . -; celular de 10 dígitos que empieza por 3) y
PasswordChangePolicy (actual, nueva de 8–128 distinta de la actual y confirmación igual).
Errores por campo con su texto en español.
```

### Prompt 7 · Servicio con resultados hablados (commit `ecd86be`)

```text
Crea ProfileService con RemoteProfileService (AuthorizedHTTPClient):
1. GET /users/me: correo (solo lectura), nombre y celular.
2. Guardar valida con ProfilePolicy; con errores o sin cambios no envía nada.
3. PATCH /users/me con los dos campos (null quita) y anuncia «Cambios guardados.». Un fallo deja
   los datos como estaban.
4. Cambiar contraseña con PUT /users/me/password; el 403 se locuta como contraseña actual
   incorrecta.
Todo resultado y error se locuta por el árbitro (contexto account-profile). Si la sesión se
rechaza, se borran los tokens y se vuelve a la bienvenida.
```

### Prompt 8 · Pantalla «Mi cuenta» (commits `81e01a4`, `14a8251`)

```text
Crea ProfileView y ProfileViewModel en Preferencias > Mi cuenta: correo como texto, campos de
nombre y celular, sección de cambio de contraseña. El error de cada campo va en su pista de
VoiceOver y el resultado en un aviso; no muevas el foco para no superponer VoiceOver con el
árbitro. Agrega la entrada en SettingsView.
```

### Prompt 9 · Pruebas y documentación (commits `1ef8eb5`, `f9fcc6a`, `4ea006b`)

```text
Escribe pruebas unitarias de ProfilePolicy, PasswordChangePolicy y ProfileService, e integración
con el árbitro real y un backend falso: guardar se oye una vez, 403 no renueva la sesión, sesión
rechazada vuelve a la bienvenida. Documenta Personalizar Cuenta en docs/ARCHITECTURE.md.
```

## Verificación final

- Backend: `pytest -rs` cubre validación, revocación de las otras sesiones y códigos de error.
- iOS: cambiar el nombre con VoiceOver dice «Cambios guardados.»; un celular inválido dice el error
  del campo sin enviar nada.

## Commits cubiertos

| Commit | Repo | Mensaje |
|---|---|---|
| `e9992f0` | Lumio | Add display name and phone to the user profile |
| `321bd39` | Lumio | Validate the profile and the password change |
| `83c5be9` | Lumio | Save the profile and change the password closing the other sessions |
| `b5dc35e` | Lumio | Implement endpoints to personalize the account |
| `746479b` | Lumio | Add unit tests for personalizing the account |
| `b5a8b9c` | Lumio | Add Postgres integration tests for personalizing the account |
| `57f8e81` | Lumio | Document the profile and password endpoints |
| `d29302e` | LumioFrontend | Share the check for connectivity failures |
| `3e33a61` | LumioFrontend | Add the profile model and its validation rules |
| `ecd86be` | LumioFrontend | Load and save the profile and change the password with spoken results |
| `81e01a4` | LumioFrontend | Add the My account screen |
| `14a8251` | LumioFrontend | Add My account to Preferences |
| `1ef8eb5` | LumioFrontend | Add unit tests for personalizing the account |
| `f9fcc6a` | LumioFrontend | Add integration tests for the profile with audio and backend |
| `4ea006b` | LumioFrontend | Document personalizing the account |
