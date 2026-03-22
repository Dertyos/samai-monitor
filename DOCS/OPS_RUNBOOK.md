# Runbook de Operaciones — SAMAI Monitor
## Última actualización: 22 de marzo de 2026

---

# 1. RECURSOS AWS

## Stack CloudFormation
- **Nombre**: `samai-monitor`
- **Región**: `us-east-1`
- **Cuenta**: `236578428550`

## Recursos desplegados

| Recurso | ID / URL |
|---------|----------|
| API Gateway | `https://weo3vfe321.execute-api.us-east-1.amazonaws.com/prod` |
| CloudFront | `https://drwlltutwjjfd.cloudfront.net` |
| CloudFront Distribution ID | `EV92NLV7RNMAN` |
| S3 Frontend | `samai-frontend-236578428550` |
| Cognito User Pool | `us-east-1_fD99TyD9S` |
| Cognito Client ID | `2a1dun36pjrsgdj3bg0plms81k` |
| Cognito Domain | `samai-236578428550.auth.us-east-1.amazoncognito.com` |
| Lambda API | `samai-api` |
| Lambda Monitor | `samai-monitor` |
| DynamoDB Radicados | `samai-radicados` |
| DynamoDB Actuaciones | `samai-actuaciones` |
| DynamoDB Alertas | `samai-alertas` |
| EventBridge | Cron diario 7am COT (12:00 UTC) |
| SES Domain | `samai-monitor.dertyos.com` |
| SES Sender | `alertas@samai-monitor.dertyos.com` |

## Usuario de prueba
- **Email**: `juliansalcedo4@gmail.com`
- **Password**: `Test123*`

---

# 2. CI/CD — GitLab

## Repositorios
| Plataforma | URL | Uso |
|------------|-----|-----|
| GitLab (principal) | `gitlab.com/juliansalcedo4/samai-monitor` | CI/CD, deploy automático |
| GitHub (mirror) | `github.com/Dertyos/samai-monitor` | Respaldo |

## Remotes locales
```bash
git remote -v
# gitlab  git@gitlab.com:juliansalcedo4/samai-monitor.git (push/fetch)
# origin  https://github.com/Dertyos/samai-monitor.git (push/fetch)
```

## Pipeline (`.gitlab-ci.yml`)
El pipeline se ejecuta automáticamente en cada push a `main`:

```
Stage 1: test
  ├── test-backend   → Python 3.13, pytest (66+ tests)
  └── test-frontend  → Node 20, tsc --noEmit, npm run build

Stage 2: build
  └── build-backend  → sam build (solo en main)

Stage 3: deploy
  └── deploy         → sam deploy + s3 sync + cloudfront invalidation
```

## IAM User para CI/CD
- **User**: `samai-gitlab-ci`
- **Policy**: `samai-gitlab-ci-deploy` (managed policy, ver `scripts/gitlab-ci-policy.json`)
- **Access Key ID**: `AKIATOFJMK2DPRKJ7UQG`
- **Permisos**: CloudFormation, Lambda, API Gateway, DynamoDB, IAM (roles), S3, CloudFront, Cognito, SES, EventBridge

## Variables CI/CD en GitLab
Configuradas en **Settings → CI/CD → Variables**:

| Variable | Valor | Flags |
|----------|-------|-------|
| `AWS_ACCESS_KEY_ID` | `AKIATOFJMK2DPRKJ7UQG` | Protected |
| `AWS_SECRET_ACCESS_KEY` | *(masked)* | Protected, Masked |
| `AWS_DEFAULT_REGION` | `us-east-1` | Protected |

## Si necesitas rotar las credenciales
```bash
# Crear nueva key
aws iam create-access-key --user-name samai-gitlab-ci

# Desactivar la vieja
aws iam update-access-key --user-name samai-gitlab-ci \
  --access-key-id AKIATOFJMK2DPRKJ7UQG --status Inactive

# Actualizar en GitLab → Settings → CI/CD → Variables

# Eliminar la vieja
aws iam delete-access-key --user-name samai-gitlab-ci \
  --access-key-id AKIATOFJMK2DPRKJ7UQG
```

---

# 3. DEPLOY MANUAL

## Backend (SAM)
```bash
cd samai-monitor
make test          # Verificar tests
make build         # sam build
make deploy        # sam deploy (usa samconfig.toml)
```

## Frontend (S3 + CloudFront)
```bash
cd samai-monitor/frontend
npm ci
npm run build

# Sync a S3 (assets con cache larga, index.html sin cache)
aws s3 sync dist/ s3://samai-frontend-236578428550/ \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html"

aws s3 cp dist/index.html s3://samai-frontend-236578428550/index.html \
  --cache-control "no-cache, no-store, must-revalidate"

# Invalidar cache de CloudFront
aws cloudfront create-invalidation \
  --distribution-id EV92NLV7RNMAN \
  --paths "/*"
```

## Solo backend (sin frontend)
```bash
make build && make deploy
```

## Solo frontend (sin backend)
```bash
cd frontend && npm run build
aws s3 sync dist/ s3://samai-frontend-236578428550/ --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html"
aws s3 cp dist/index.html s3://samai-frontend-236578428550/index.html \
  --cache-control "no-cache, no-store, must-revalidate"
aws cloudfront create-invalidation --distribution-id EV92NLV7RNMAN --paths "/*"
```

---

# 4. SES — Email

## Estado actual
- **Domain identity**: `samai-monitor.dertyos.com`
- **DKIM**: Habilitado (pendiente verificación DNS)
- **Sandbox**: Solicitud de production access enviada (22 mar 2026)
- **Sender**: `alertas@samai-monitor.dertyos.com`
- **Limitaciones sandbox**: Solo envía a emails verificados, 200/día, 1/seg

## Registros DKIM (Cloudflare DNS)
Agregar estos 3 registros **CNAME** con proxy **desactivado** (DNS only):

| Name | Target |
|------|--------|
| `3xwp6ewnk4k4lrmceggy27w4b3ixljjx._domainkey.samai-monitor` | `3xwp6ewnk4k4lrmceggy27w4b3ixljjx.dkim.amazonses.com` |
| `schgga57miygmfmejvk4b4elnt2nxuqt._domainkey.samai-monitor` | `schgga57miygmfmejvk4b4elnt2nxuqt.dkim.amazonses.com` |
| `qizgrlwz7okpso3o5a242gy5zmpfwqn7._domainkey.samai-monitor` | `qizgrlwz7okpso3o5a242gy5zmpfwqn7.dkim.amazonses.com` |

## Verificar estado DKIM
```bash
aws sesv2 get-email-identity \
  --email-identity samai-monitor.dertyos.com \
  --region us-east-1 \
  --query 'DkimAttributes.{Status: Status, Tokens: Tokens}'
```
Debe mostrar `Status: SUCCESS` cuando los DNS propaguen.

## Verificar estado del sandbox
```bash
aws sesv2 get-account --region us-east-1 \
  --query '{ProductionAccess: ProductionAccessEnabled, Quota: SendQuota}'
```
`ProductionAccessEnabled: true` = ya salió del sandbox.

## Si AWS rechaza la solicitud de producción
Reenviar con más detalle:
```bash
aws sesv2 put-account-details \
  --mail-type TRANSACTIONAL \
  --website-url "https://samai-monitor.dertyos.com" \
  --contact-language EN \
  --use-case-description "Descripción más detallada..." \
  --additional-contact-email-addresses "juliansalcedo4@gmail.com" \
  --production-access-enabled \
  --region us-east-1
```

---

# 5. MONITOREO Y DEBUGGING

## Invocar monitor manualmente
```bash
aws lambda invoke \
  --function-name samai-monitor \
  --region us-east-1 \
  /tmp/monitor-output.json && cat /tmp/monitor-output.json
```

## Ver logs del monitor
```bash
aws logs tail /aws/lambda/samai-monitor --since 1h --follow
```

## Ver logs de la API
```bash
aws logs tail /aws/lambda/samai-api --since 1h --follow
```

## Consultar DynamoDB
```bash
# Listar radicados de un usuario
aws dynamodb query \
  --table-name samai-radicados \
  --key-condition-expression "userId = :uid" \
  --expression-attribute-values '{":uid": {"S": "USER_SUB_ID"}}' \
  --region us-east-1

# Contar alertas
aws dynamodb scan \
  --table-name samai-alertas \
  --select COUNT \
  --region us-east-1
```

## Verificar API manualmente
```bash
# Obtener token JWT
TOKEN=$(aws cognito-idp initiate-auth \
  --client-id 2a1dun36pjrsgdj3bg0plms81k \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=juliansalcedo4@gmail.com,PASSWORD=Test123* \
  --region us-east-1 \
  --query 'AuthenticationResult.IdToken' --output text)

# Listar radicados
curl -H "Authorization: Bearer $TOKEN" \
  https://weo3vfe321.execute-api.us-east-1.amazonaws.com/prod/radicados

# Listar alertas
curl -H "Authorization: Bearer $TOKEN" \
  https://weo3vfe321.execute-api.us-east-1.amazonaws.com/prod/alertas
```

---

# 6. SSH KEYS

## GitLab SSH
- **Key file**: `~/.ssh/id_ed25519`
- **Public key**: `ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIO67pV1iyyUH9up6+DYkEUQTfde5FuvpJtkU4hy8aunb juliansalcedo4@gmail.com`
- **Configurada en**: GitLab → Settings → SSH Keys

## Regenerar si se pierde
```bash
ssh-keygen -t ed25519 -C "juliansalcedo4@gmail.com" -f ~/.ssh/id_ed25519
cat ~/.ssh/id_ed25519.pub
# Copiar y pegar en GitLab → Settings → SSH Keys
```

---

# 7. TROUBLESHOOTING

## Pipeline de GitLab falla en deploy
1. Verificar variables CI/CD en GitLab (Settings → CI/CD → Variables)
2. Verificar que el IAM user tiene permisos: `aws iam list-attached-user-policies --user-name samai-gitlab-ci`
3. Si el access key expiró: rotar (ver sección 3)

## API retorna 403 Forbidden
- El JWT token expiró (duran 1 hora)
- Generar nuevo token con el comando de la sección 5

## API retorna "Ruta no encontrada"
- API Gateway v2 incluye stage prefix en `rawPath` (`/prod/radicados`)
- El handler ya lo stripea automáticamente, pero si se agrega un endpoint nuevo, verificar que esté en el router

## Frontend no carga cambios nuevos
- CloudFront cache (TTL largo para assets)
- Ejecutar invalidación: `aws cloudfront create-invalidation --distribution-id EV92NLV7RNMAN --paths "/*"`

## SES no envía emails
1. Verificar sandbox: `aws sesv2 get-account --query ProductionAccessEnabled`
2. Si sandbox=true, solo puede enviar a emails verificados
3. Verificar DKIM: `aws sesv2 get-email-identity --email-identity samai-monitor.dertyos.com`
4. Verificar sender en template.yaml: `SES_SENDER`

## Lambda "No module named..."
- `ContentUri` en template.yaml apunta mal
- Verificar con `sam build` localmente antes de deploy

## EventBridge no ejecuta el monitor
```bash
aws events describe-rule --name "samai-monitor-*" --region us-east-1
aws events list-targets-by-rule --rule "RULE_NAME" --region us-east-1
```

---

# 8. FASES FUTURAS PENDIENTES

### Fase 8: Custom Domain (`samai-monitor.dertyos.com`)
1. Solicitar certificado ACM en us-east-1: `aws acm request-certificate --domain-name samai-monitor.dertyos.com --validation-method DNS`
2. Agregar CNAME de validación en Cloudflare
3. Actualizar CloudFront: agregar Alias + certificado ACM
4. Agregar CNAME en Cloudflare: `samai-monitor` → `drwlltutwjjfd.cloudfront.net`
5. Actualizar Cognito callback URLs (ya están pre-configuradas en template.yaml)

### Fase 9: SES Production (en progreso)
1. ✅ Solicitud enviada
2. Pendiente: Agregar DKIM DNS records en Cloudflare
3. Pendiente: Esperar aprobación AWS (~24h)
4. Futuro: Crear plantilla HTML profesional para emails

### Fase 10-13
Ver `DOCS/DEV_LOG.md` sección "Fases Futuras"
