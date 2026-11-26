# SCRUM-2 · HU: Iniciar Sesión

| | |
|---|---|
| Responsable (Jira) | Tulio Riaño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` (backend) y `LumioFrontend` (sesión en iOS) |
| Commits | 11 (2026-10-26 → 2026-11-25) |
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

### Prompt 6 · Iniciar sesión con Google en el backend (commit `4bd4f1f`, subtarea SCRUM-62)

```text
Implementa POST /users/login/google {"id_token"}: verifica el ID token de Google (firma con las
llaves públicas de Google, emisor, vigencia y audiencia contra GOOGLE_CLIENT_IDS) y entra a la
cuenta por el sub de Google. Si no existe, crea una cuenta sin contraseña con el correo verificado
(201). Un correo que ya es de una cuenta con contraseña no se asocia solo (409
google_account_conflict), porque el registro por correo no verifica el correo. Sin client IDs o
sin llaves responde 503. El verificador es una dependencia de FastAPI: las pruebas del endpoint
usan uno falso y las de la verificación firman tokens RSA locales, sin red.
```

### Prompt 7 · Cerrar el login con contraseña a las cuentas de Google (commit `1fcd7d0`)

```text
El login compara la contraseña contra un hash ficticio cuando la cuenta no tiene password_hash
(cuentas solo de Google), para igualar el tiempo, pero emite tokens si esa comparación acierta. La
contraseña ficticia está en el repo público, así que cualquiera que sepa el correo de una cuenta de
Google podría entrar. Sigue comprobando el hash ficticio por el tiempo, pero que nunca autentique.
Agrega la prueba en test_login.py.
```

### Prompt 8 · Asociar Google a una cuenta con contraseña (commit `3d7b92b`)

```text
Agrega POST /users/me/google {"id_token"}: con sesión iniciada, asocia la cuenta de Google con
las mismas verificaciones que /users/login/google. Es la vía segura para el caso del 409: el access
token ya prueba quién es el dueño, así que los correos no tienen que coincidir. Idempotente con la
misma cuenta de Google; 409 google_already_linked si ya tiene otra y google_account_in_use si esa
cuenta de Google es de otra cuenta de Lumio. Un token inválido es 403 (no 401) para que el cliente
no renueve la sesión. GET /users/me devuelve google_linked.
```

### Prompt 9 · «Continuar con Google» en iOS (commits `87830ea`, `dd797bb` y `a1a7dda`)

```text
En la app, «Continuar con Google» abre Google con ASWebAuthenticationSession (OAuth con PKCE,
state y nonce, sin SDK ni secreto de cliente), cambia el código por el ID token y lo envía a POST
/users/login/google; los tokens de Lumio se guardan en Keychain como con correo. El client ID va en
GoogleClientID del Info.plist; vacío, Google queda no disponible. Sin red no abre Google, y la
cancelación, la falta de red y los errores se dicen por el AudioArbiter (P2, contexto
google-sign-in) sin repetirlos con VoiceOver. Con el 409 explica que se entre con la contraseña y
se asocie Google desde Mi cuenta, donde «Asociar cuenta de Google» llama a POST /users/me/google y
se oculta si google_linked es true. Guarda el correo de Google en minúsculas, como el backend.
Pruebas en GoogleSignInTests y docs/HU-iniciar-sesion-con-google.md.
```

## Verificación final

- `pytest -rs` pasa login, me y refresh contra Postgres.
- En el iPhone: iniciar sesión, cerrar la app y abrirla sin red entra directo a Trayecto.
- `pytest tests/modules/users/test_login_google.py tests/modules/users/test_google_auth.py
  tests/modules/users/test_link_google.py` y `swift test --filter GoogleSignInTests` pasan.
- En el iPhone: «Continuar con Google» entra y crea la cuenta la primera vez. La subtarea SCRUM-62
  sigue en *Por hacer* en Jira aunque el código está.

## Commits cubiertos

| Commit | Repo | Fecha | Mensaje |
|---|---|---|---|
| `a4e4c71` | Lumio | 2026-10-26 | SCRUM-2 HU: Add auth session model and migration |
| `35ea343` | Lumio | 2026-10-26 | SCRUM-2 HU: Implement login endpoint with JWT |
| `0670366` | Lumio | 2026-10-26 | SCRUM-2 HU: Add current user dependency and /me endpoint |
| `545f2fd` | Lumio | 2026-10-26 | SCRUM-2 HU: Implement token refresh with rotation |
| `5672935` | LumioFrontend | 2026-11-08 | SCRUM-9 HU: Sign in with email and keep session tokens in Keychain |
| `4bd4f1f` | Lumio | 2026-11-25 | SCRUM-62 HU: Sign in and create accounts with Google |
| `1fcd7d0` | Lumio | 2026-11-25 | SCRUM-62 Fix: Reject password login for accounts without a password |
| `3d7b92b` | Lumio | 2026-11-25 | SCRUM-62 HU: Asociar una cuenta de Google a la cuenta de Lumio |
| `87830ea` | LumioFrontend | 2026-11-25 | SCRUM-62 HU: Iniciar sesión con Google y asociarla a la cuenta de Lumio |
| `dd797bb` | LumioFrontend | 2026-11-25 | SCRUM-62 Fix: Guardar en minúsculas el correo de la cuenta de Google |
| `a1a7dda` | LumioFrontend | 2026-11-25 | SCRUM-62 Config: Client ID de Google para iOS |

Las pantallas de bienvenida y formulario (`cff9ce9`) están en [SCRUM-1](SCRUM-1_Crear_Cuenta.md).
