# SCRUM-2 · HU: Iniciar Sesión

| | |
|---|---|
| Responsable (Jira) | Tulio Riaño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` (backend) y `LumioFrontend` (sesión en iOS) |
| Commits | 5 (2026-10-26 → 2026-11-08) |
| Depende de | SCRUM-1 (usuarios), SCRUM-317 |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario registrado de Lumio, quiero iniciar sesión en mi cuenta para acceder a mi configuración,
> mis preferencias y mi historial.

**Criterios de aceptación**
- Inicio con cuenta propia o con Google.
- Con cuenta propia se valida el formato y se verifica en el backend.
- Credenciales correctas inician la sesión; incorrectas se informan por audio y con mensaje accesible.
- La sesión se guarda de forma segura en el dispositivo.
- Se puede continuar a la app tras autenticarse.
- Errores de conexión se informan por audio.
- Flujo usable con VoiceOver.

## Prompts

### Prompt 1 · Modelo de sesión (commit `a4e4c71`)

```text
Vamos a usar access token corto (15 min) y refresh token largo (30 días) con rotación, para
poder revocar sesiones por dispositivo. Agrega AuthSession en app/modules/users/models.py
(id UUID, user_id con FK a users ondelete CASCADE, created_at, revoked_at) y la migración
alembic/versions/0002_create_auth_sessions.py. No guardes tokens en la base: los dos JWT de una
sesión llevan su id en el claim jti, y revocar la sesión invalida ambos.
```

### Prompt 2 · Login con JWT (commit `35ea343`)

```text
Implementa POST /users/login con UserLogin (email, password):
- service.login normaliza el correo y verifica con verify_password. Si el correo no existe,
  verifica contra un hash ficticio para que el tiempo de respuesta no delate qué cuentas existen.
- issue_tokens crea la AuthSession y devuelve TokenPair (access_token, refresh_token,
  token_type="bearer", expires_in). Cada JWT lleva sub=user_id, type ("access" o "refresh"),
  iat, exp y jti=id de la sesión.
- Correo inexistente y contraseña incorrecta responden igual: 401 "Correo o contraseña
  incorrectos". Declara POST /users/login/google con 501 hasta el spike de Google.
Pruebas en tests/modules/users/test_login.py: correcto, contraseña mala, correo inexistente,
correo con mayúsculas y la sesión creada en la base.
```

### Prompt 3 · Usuario actual y /me (commit `0670366`)

```text
Agrega service.resolve_session(token, token_type): decodifica el JWT, busca la sesión por jti y
exige que el type coincida, que sub sea el dueño de la sesión y que no esté revocada. Crea
app/modules/users/dependencies.py con get_current_user, que lee Authorization: Bearer y usa
resolve_session con "access" para devolver el usuario. Cualquier fallo es 401 "Sesión no válida". Agrega GET /users/me con UserRead.
Pruebas en test_me.py: sin token, token mal firmado, vencido, refresh usado como access, sesión
revocada y caso correcto.
```

### Prompt 4 · Renovar con rotación (commit `545f2fd`)

```text
Implementa POST /users/refresh {refresh_token}: resolve_session con "refresh" (el exp del JWT
cubre el vencimiento), revoca esa sesión y emite un TokenPair nuevo con una sesión nueva. Reusar un
refresh ya rotado responde 401. Pruebas en test_refresh.py: rotación correcta, reuso del
anterior, token de access en lugar de refresh y sesión revocada.
```

### Prompt 5 · Sesión en iOS con Keychain (commit `5672935`, dentro de SCRUM-9)

```text
En la app conecta el inicio de sesión real:
- Users/Data/AuthAPI: DTOs de /users, /users/login, /users/refresh y /users/logout.
- KeychainTokenStore: guarda access y refresh en Keychain
  (kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly);
  nunca en UserDefaults.
- RemoteAuthenticationService: registro e inicio de sesión que guardan la sesión.
- AuthorizedHTTPClient: agrega Authorization: Bearer; ante un 401 renueva una sola vez con
  /users/refresh y repite la petición; si el refresh se rechaza, borra la sesión.
- StoredSessionService decide la pantalla inicial sin red (hay tokens → app; no → bienvenida).
- AccountFormViewModel: 401 se locuta «Correo o contraseña incorrectos», sin conexión
  «No hay conexión…», y el éxito lleva a Trayecto.
- SignOutService base para cerrar sesión desde Preferencias (se completa en SCRUM-5).
```

## Verificación final

- `pytest -rs` pasa login, me y refresh contra Postgres.
- En el iPhone: iniciar sesión, cerrar la app y abrirla sin red entra directo a Trayecto.
- **Pendiente según Jira:** inicio de sesión con Google (subtarea SCRUM-62). `POST /users/login/google`
  responde 501 y no hay commits que lo implementen.

## Commits cubiertos

| Commit | Repo | Fecha | Mensaje |
|---|---|---|---|
| `a4e4c71` | Lumio | 2026-10-26 | SCRUM-2 HU: Add auth session model and migration |
| `35ea343` | Lumio | 2026-10-26 | SCRUM-2 HU: Implement login endpoint with JWT |
| `0670366` | Lumio | 2026-10-26 | SCRUM-2 HU: Add current user dependency and /me endpoint |
| `545f2fd` | Lumio | 2026-10-26 | SCRUM-2 HU: Implement token refresh with rotation |
| `5672935` | LumioFrontend | 2026-11-08 | SCRUM-9 HU: Sign in with email and keep session tokens in Keychain |

Las pantallas de bienvenida y formulario (`cff9ce9`) están en [SCRUM-1](SCRUM-1_Crear_Cuenta.md).
