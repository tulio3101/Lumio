# SCRUM-1 · HU: Crear Cuenta

| | |
|---|---|
| Responsable (Jira) | Tulio Riaño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` (backend) y `LumioFrontend` (pantallas) |
| Commits | 4 (2026-10-26 → 2026-10-29) |
| Depende de | SCRUM-317 (esqueleto y `app/core/security.py`) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero crear una cuenta para guardar mi configuración, mis preferencias y mi
> historial de rutas.

**Criterios de aceptación**
- Registro con cuenta propia (correo y contraseña) o con Google.
- Valida los datos e informa por audio y de forma accesible si no son válidos.
- Crea la cuenta correctamente y confirma por audio.
- Contraseñas solo como hash seguro en el backend.
- Flujo completo usable con VoiceOver.
- Un correo ya registrado se informa sin exponer datos de otras cuentas.

Fuera del MVP: Sign in with Apple (SCRUM-323).

## Prompts

### Prompt 1 · Fixtures de base de datos de prueba (commit `676b634`)

```text
Antes de escribir el registro necesito pruebas contra Postgres real. En tests/conftest.py agrega
fixtures que lean TEST_DATABASE_URL, apliquen las migraciones una vez por sesión, den una sesión
SQLAlchemy por prueba y vacíen las tablas al terminar. Si TEST_DATABASE_URL no está, las
pruebas que la necesitan se marcan como skip con un motivo claro; las unitarias siguen corriendo.
Sobrescribe la dependencia get_db del TestClient para usar esa sesión.
```

### Prompt 2 · Repositorio y servicio de registro (commit `50458cc`)

```text
Implementa el registro en app/modules/users:
- repository.py: get_by_email y create.
- service.py: normalize_email (strip + minúsculas) y register(db, UserCreate) que guarda solo
  hash_password(password) de app/core/security (argon2). Si el correo existe lanza
  EmailAlreadyRegistered; captura también el IntegrityError del índice único por si dos
  registros llegan a la vez.
UserCreate valida email con EmailStr y password de 8 a 128 caracteres.
```

### Prompt 3 · Endpoint de registro (commit `e42b686`)

```text
Expón POST /users (201, response_model UserRead sin password_hash). Si el correo ya existe
responde 409 con "No se pudo crear la cuenta con ese correo": no digas si la cuenta es de otra
persona ni devuelvas datos. Los endpoints de Google quedan declarados con 501
"No implementado" hasta que se haga el spike de Google.
Escribe tests/modules/users/test_register.py: alta correcta, correo normalizado, el hash no es
la contraseña, correo duplicado (también con otras mayúsculas), contraseña corta o larga y
correo inválido (422). El modelo User ya trae google_sub (único, opcional) y password_hash
opcional para las cuentas de Google.
```

### Prompt 4 · Pantallas de bienvenida, crear cuenta e iniciar sesión (commit `cff9ce9`)

```text
En la app iOS crea la entrada a la cuenta, accesible primero con VoiceOver:
- Features/Welcome/Presentation/WelcomeView: logo, frase corta y dos acciones grandes
  «Crear cuenta» e «Iniciar sesión», más «Continuar con Google» (por ahora responde que no está
  disponible).
- Features/Users/Domain/AccountCredentials: CredentialsPolicy con las mismas reglas que
  UserCreate (correo con usuario y dominio con punto, sin espacios; contraseña 8...128) y los
  errores por campo (missing, invalidFormat, tooShort, tooLong).
- Users/Presentation/AccountFormView + AccountFormViewModel para .signUp y .signIn: un campo por
  fila, el error de cada campo en su pista de VoiceOver y anunciado con
  Shared/UI/AccessibilityAnnouncement; el botón principal no se desactiva en silencio.
- Contratos Authenticating y SessionRestoring con servicios Unavailable mientras no hay backend.
- Shared/UI/LumioTheme y docs/DESIGN_SYSTEM.md: Quicksand, colores con contraste AA, tamaños
  dinámicos. Agrega íconos, fuente (con su licencia OFL) y el AppIcon; declara los recursos en
  project.yml, Package.swift y xtool.yml.
Pruebas: CredentialsPolicyTests (cada error) y AppEntryTests (qué pantalla abre sin sesión).
```

### Prompt 5 · Conectar con el backend (se hizo dentro de SCRUM-9, commit `5672935`)

```text
Conecta AccountFormViewModel al backend real con RemoteAuthenticationService: POST /users y
luego login para guardar los tokens en Keychain. Locuta por el árbitro el resultado («Cuenta
creada…») y los errores: 409 como «Ya existe una cuenta con ese correo. Inicia sesión», sin
conexión y error del servidor con su propio mensaje.
```

## Verificación final

- `pytest -rs` con `TEST_DATABASE_URL` pasa las pruebas de registro.
- Con VoiceOver se puede crear una cuenta sin mirar y se oyen los errores de cada campo.
- **Pendiente según Jira:** registro con Google (subtarea SCRUM-68). El backend responde 501 y no
  hay commits que lo implementen.

## Commits cubiertos

| Commit | Repo | Fecha | Mensaje |
|---|---|---|---|
| `676b634` | Lumio | 2026-10-26 | SCRUM-1 HU: Add test database fixtures |
| `50458cc` | Lumio | 2026-10-26 | SCRUM-1 HU: Add user repository and registration service |
| `e42b686` | Lumio | 2026-10-26 | SCRUM-1 HU: Implement registration endpoint |
| `cff9ce9` | LumioFrontend | 2026-10-29 | style: landing and creater/login screens implemented |
