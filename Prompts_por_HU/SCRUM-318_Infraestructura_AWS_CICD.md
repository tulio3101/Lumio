# SCRUM-318 · HU: Aprovisionar infraestructura base en AWS y CI/CD

| | |
|---|---|
| Responsable (Jira) | Juan Sebastián Puentes |
| Estado Jira | Finalizado |
| Repositorio | `Lumio` (backend) |
| Commits | 5 (2026-11-08) |
| Depende de | SCRUM-310 (spike de arquitectura AWS), SCRUM-317 (esqueleto) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como equipo de desarrollo, queremos infraestructura base en AWS y un pipeline de CI/CD para
> desplegar el backend de forma repetible.

**Criterios de aceptación**
- Entorno de desarrollo en AWS según el spike SCRUM-310.
- Secretos fuera del código.
- Base de datos aprovisionada según el spike.
- Un pipeline construye, prueba y despliega el backend al hacer merge.
- Errores y logs observables.

## Prompts

### Prompt 1 · Plantilla CloudFormation del entorno dev (commit `9657709`)

```text
Según el ADR del spike SCRUM-310, el entorno dev de Lumio es: una EC2 t4g.small con Docker,
RDS PostgreSQL 16 (db.t4g.micro) en subredes privadas, imágenes en ECR, logs en CloudWatch y
secretos en SSM Parameter Store. Escribe infra/lumio-dev.yaml (CloudFormation) con:
- VPC con subredes pública y privadas, security groups (80/443 públicos a la EC2; 5432 solo
  desde la EC2 a RDS);
- AWS::RDS::DBSubnetGroup y AWS::RDS::DBInstance (postgres 16, cifrado, sin acceso público,
  contraseña gestionada fuera de la plantilla);
- AWS::ECR::Repository para la imagen de la API;
- AWS::Logs::LogGroup para los contenedores;
- rol e instance profile de la EC2 con permisos mínimos: leer ECR, leer /lumio/dev/* de SSM,
  escribir logs y usar SSM Session Manager (sin SSH abierto);
- AWS::IAM::OIDCProvider de GitHub y un rol de despliegue que solo pueda asumir este repo;
- un SNS::Topic, un CloudWatch::Alarm y un Logs::MetricFilter que cuente errores 5xx de la API.
Parametriza el entorno para poder crear prod más adelante.
```

### Prompt 2 · Compose de producción, Caddy y script de despliegue (commit `60119fc`)

```text
Crea en deploy/:
- docker-compose.yml para la EC2: el servicio api con la imagen de ECR, el driver de logs
  awslogs hacia el log group, healthcheck sobre /health y Caddy delante;
- Caddyfile: HTTPS automático con el dominio del entorno y reverse_proxy a api:8000;
- deploy.sh: lee los parámetros /lumio/<env>/* de SSM (con --with-decryption), escribe el .env
  en la EC2, hace login en ECR, descarga la imagen nueva y levanta el compose. Las migraciones
  (`alembic upgrade head`) las aplica el entrypoint de la imagen al arrancar. Que se detenga
  ante cualquier error (set -euo pipefail). Caddy también manda sus logs a CloudWatch.
```

### Prompt 3 · No arrancar con un secreto JWT inseguro (commit `0b3f599`)

```text
El JWT_SECRET de ejemplo no puede llegar a dev ni a prod. En app/core/config.py valida al
cargar Settings que, si ENVIRONMENT no es local, el secreto no sea el de ejemplo ni tenga menos
de 32 caracteres; en ese caso la app no arranca y el error dice por qué. Agrega .gitattributes
para que deploy.sh y el Caddyfile tengan siempre finales de línea LF (el equipo usa Windows).
```

### Prompt 4 · Pipeline de despliegue al hacer merge a develop (commit `0b431f0`)

```text
Crea .github/workflows/deploy.yml que en push a develop:
1. ejecute el CI (ruff + pytest) reutilizando ci.yml;
2. asuma el rol de despliegue con aws-actions/configure-aws-credentials por OIDC (sin claves
   guardadas en GitHub);
3. construya la imagen, la etiquete con el sha y la suba a ECR (amazon-ecr-login);
4. ejecute deploy.sh en la EC2 con `aws ssm send-command` y espere el resultado con
   get-command-invocation;
5. compruebe /health al final con curl y reintentos (12 intentos cada 5 s) y falle si no responde.
Ajusta ci.yml para que se pueda llamar desde otro workflow (workflow_call).
```

### Prompt 5 · Confianza OIDC con el subject inmutable (commit `af6890f`)

```text
La condición del rol de despliegue usa el nombre del repo en el subject. Si alguien renombra o
transfiere el repo, otro con el mismo nombre podría asumirlo. Agrega el parámetro
GitHubRepoImmutable (dueño y repo con sus IDs numéricos, formato immutable subject de GitHub
OIDC) y acepta en la condición `sub` ese subject limitado a refs/heads/${DeployBranch}, además
del actual mientras se migra; `aud` debe ser sts.amazonaws.com. Explica qué cambia al
actualizar el stack.
```

## Verificación final

- `aws cloudformation deploy` crea el stack sin errores y la EC2 no tiene SSH abierto.
- Un merge a develop construye, prueba, publica en ECR y despliega; `/health` responde por HTTPS.
- Los logs de la API aparecen en CloudWatch y la alarma de 5xx notifica por SNS.
- Ningún secreto está en el repo: JWT y base de datos viven en SSM.

## Commits cubiertos

| Commit | Fecha | Mensaje |
|---|---|---|
| `9657709` | 2026-11-08 | Add CloudFormation template for the AWS dev environment |
| `60119fc` | 2026-11-08 | Add production compose, Caddy reverse proxy and deploy script |
| `0b3f599` | 2026-11-08 | Refuse to start outside local with an insecure JWT secret |
| `0b431f0` | 2026-11-08 | Add deploy pipeline to AWS on merge to develop |
| `af6890f` | 2026-11-08 | Trust GitHub OIDC immutable subject in the deploy role |
