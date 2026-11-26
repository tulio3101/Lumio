# SCRUM-3 · HU: Recuperar Contraseña

| | |
|---|---|
| Responsable (Jira) | Tulio Riaño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 3 (2026-11-25) |
| Depende de | SCRUM-1, SCRUM-2 |
| Autoría de los commits | Néstor López |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario registrado con cuenta propia, quiero recuperar el acceso a mi cuenta cuando no
> recuerde mi contraseña para volver a usar la aplicación sin crear una cuenta nueva.

**Criterios de aceptación**
- El usuario puede solicitar la recuperación de su contraseña.
- El sistema solicita el correo de la cuenta y envía un mensaje de verificación.
- El sistema informa por audio si la solicitud fue procesada, sin revelar si el correo existe.
- El usuario puede establecer una nueva contraseña mediante el mecanismo de recuperación.
- La nueva contraseña cumple las reglas de seguridad establecidas.
- El sistema informa si el proceso no puede completarse.
- Una vez restablecida, el usuario puede iniciar sesión con ella.
- El flujo es usable con VoiceOver.

**Alcance.** Solo cuentas propias. Google y Apple no usan contraseña de Lumio.

## Prompts

### Prompt 1 · Códigos de recuperación en el backend (commit `813eb8e`)

```text
Implementa la recuperación de contraseña para cuentas propias en app/modules/users:
- Migración alembic/versions/0009_password_reset_codes.py con la tabla de códigos (usuario,
  hash del código, vencimiento, intentos, usado). Nunca guardes el código en claro.
- password_reset.py: genera un código de 6 dígitos, guarda su hash y lo envía por correo. Vence
  en 15 min, admite 5 intentos, solo vale el último y se acepta un pedido por minuto.
- POST /users/password-reset {"email"}: responde siempre 202 con el mismo mensaje exista o no la
  cuenta, para no revelar qué correos están registrados. Las cuentas solo de Google no reciben
  código.
- POST /users/password-reset/confirm {"email", "code", "new_password"} (8–128 caracteres): valida
  el código, cambia el hash y cierra las sesiones de todos los dispositivos (204).
- Errores en español con {detail, code}: 400 invalid_reset_code con la misma respuesta para
  código incorrecto, vencido, agotado o correo sin cuenta; 500 password_reset_failed; 503.
Pruebas en tests/modules/users/test_password_reset.py y tests/integration/test_password_reset_api.py.
Documenta los dos endpoints en el README.
```

### Prompt 2 · Flujo accesible en iOS (commit `c06a9ee`)

```text
En la app agrega «¿Olvidaste tu contraseña?» en Iniciar sesión (AccountFormView):
- Users/Domain/PasswordRecovery.swift: pasos (pedir correo, código, contraseña nueva),
  validación local del correo, del código de 6 dígitos y de la contraseña con las mismas reglas
  del registro, y los textos que se locutan.
- PasswordRecoveryService: llama a RemotePasswordRecoveryService (POST /users/password-reset y
  /confirm) y anuncia cada resultado por el AudioArbiter en el contexto password-recovery. El
  aviso de envío es el mismo exista o no la cuenta.
- PasswordRecoveryView + ViewModel: un campo por paso, errores en la pista de VoiceOver del
  campo y foco al título de cada paso.
- Al terminar, la sesión nueva queda guardada como en el login.
Conecta todo en AppDependencies y RootView. Pruebas en PasswordRecoveryTests y
docs/HU-recuperar-contrasena.md; agrega la sección en ARCHITECTURE.md y el README.
```

### Prompt 3 · Arreglar el merge con la narración (commit `bac7fdc`)

```text
Al traer develop quedaron mezclados en RootView los parámetros nuevos passwordRecovery y
environmentNarration: el init tiene dos cierres de firma y en LumioApp falta una coma. Deja un
solo init que reciba narrationConsent, passwordRecovery y environmentNarration y los asigne una
vez, y corrige la llamada en LumioFrontend.swift.
```

## Verificación final

- `pytest tests/modules/users/test_password_reset.py tests/integration/test_password_reset_api.py` pasa.
- `swift test --filter PasswordRecoveryTests` pasa.
- Con VoiceOver: pedir el código, recibir el correo, crear la contraseña nueva e iniciar sesión con ella.
- Pedir el código con un correo que no existe da el mismo aviso que con uno registrado.

## Commits cubiertos

| Repo | Commit | Fecha | Mensaje |
|---|---|---|---|
| Lumio | `813eb8e` | 2026-11-25 | HU: Recuperar contrasena |
| LumioFrontend | `c06a9ee` | 2026-11-25 | HU: Recuperar contraseña |
| LumioFrontend | `bac7fdc` | 2026-11-25 | Corregir el merge de develop en RootView y LumioApp |
