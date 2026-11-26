#!/bin/bash
# Despliega una versión del backend en la EC2. Lo ejecuta GitHub Actions por SSM Run Command.
# Uso: deploy.sh <tag-de-imagen>   (el tag es el SHA del commit)
set -euo pipefail

IMAGE_TAG="${1:?Uso: deploy.sh <tag-de-imagen>}"
APP_DIR=/opt/lumio
cd "$APP_DIR"

# Datos de la infraestructura escritos por CloudFormation al crear la EC2 (no son secretos).
source "$APP_DIR/infra.env"

# 1. Secretos desde Parameter Store: nunca están en el repo ni en GitHub.
param() {
  aws ssm get-parameter --region "$AWS_REGION" --with-decryption \
    --name "/lumio/$ENV_NAME/$1" --query Parameter.Value --output text
}
JWT_SECRET="$(param JWT_SECRET)"
DB_PASSWORD="$(param DB_PASSWORD)"
# Remitente verificado en SES para las alertas de emergencia. Es opcional: sin este parámetro la
# API despliega igual, pero el envío de alertas falla con un error claro (no finge enviar).
SES_SENDER_EMAIL="$(param SES_SENDER_EMAIL 2>/dev/null || true)"
# Modelo de Bedrock para la narración del entorno (ADR-308), p. ej.
# us.anthropic.claude-haiku-5-5. Opcional: sin él la narración responde 503 narration_unavailable.
NARRATION_MODEL_ID="$(param NARRATION_MODEL_ID 2>/dev/null || true)"
# Client ID de OAuth de Google (iOS, y web si la hay), separados por comas. No es secreto.
# Opcional: sin él POST /users/login/google responde 503 google_auth_unavailable.
GOOGLE_CLIENT_IDS="$(param GOOGLE_CLIENT_IDS 2>/dev/null || true)"

# 2. Archivo .env para Compose, legible solo por root.
umask 077
cat > .env <<EOF
API_IMAGE=$ECR_REPOSITORY_URI:$IMAGE_TAG
AWS_REGION=$AWS_REGION
LOG_GROUP=$LOG_GROUP
API_DOMAIN=$API_DOMAIN
ENVIRONMENT=$ENV_NAME
DEBUG=false
DATABASE_URL=postgresql+psycopg://lumio:$DB_PASSWORD@$DB_HOST:5432/lumio
JWT_SECRET=$JWT_SECRET
PUBLIC_BASE_URL=https://$API_DOMAIN
EOF
if [ -n "$SES_SENDER_EMAIL" ]; then
  {
    echo "EMAIL_BACKEND=ses"
    echo "SES_SENDER_EMAIL=$SES_SENDER_EMAIL"
  } >> .env
fi

if [ -n "$NARRATION_MODEL_ID" ]; then
  {
    echo "NARRATION_BACKEND=bedrock"
    echo "NARRATION_MODEL_ID=$NARRATION_MODEL_ID"
  } >> .env
fi

if [ -n "$GOOGLE_CLIENT_IDS" ]; then
  echo "GOOGLE_CLIENT_IDS=$GOOGLE_CLIENT_IDS" >> .env
fi

# 3. Descargar la imagen desde ECR con el rol de la instancia.
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "${ECR_REPOSITORY_URI%%/*}"
docker compose pull

# 4. Levantar. El entrypoint de la imagen aplica las migraciones (alembic upgrade head).
docker compose up -d --remove-orphans

# 5. Esperar a que la API quede sana; si no, fallar para que el pipeline quede en rojo.
for _ in $(seq 1 30); do
  status="$(docker inspect --format '{{.State.Health.Status}}' "$(docker compose ps -q api)" 2>/dev/null || echo starting)"
  if [ "$status" = "healthy" ]; then
    echo "Despliegue OK: $IMAGE_TAG"
    docker image prune -af --filter "until=72h" >/dev/null || true
    exit 0
  fi
  sleep 5
done

echo "La API no quedó sana después del despliegue. Últimos logs:" >&2
docker compose logs --tail 50 api >&2 || true
exit 1