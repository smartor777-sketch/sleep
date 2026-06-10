# InnerCore — production deploy

Production environment runs on **msk-1** (`5.42.100.202`) via Docker Compose.
Images are built by GitHub Actions and pushed to `ghcr.io/core-euler/sna_net-*`.

## Layout

```
deploy/
├── Caddyfile                # Reverse-proxy + auto-TLS (Let's Encrypt)
├── docker-compose.prod.yml  # All prod services
├── deploy.sh                # Pull-and-restart script (called by CI over SSH)
└── README.md                # This file
```

## Domains

| Host                 | Service       | Container       |
|---------------------|---------------|-----------------|
| `innercore.art`     | landing       | `landing` → :80 |
| `app.innercore.art` | web app       | `frontend` → :80|
| `api.innercore.art` | backend API   | `backend` → :8000|

DNS A-records must all point to `5.42.100.202`. Caddy obtains TLS automatically
on first request to each host.

## One-time server bootstrap (manual)

```bash
ssh msk-1
mkdir -p ~/innercore/deploy
# Copy from local machine:
#   scp deploy/* msk-1:~/innercore/deploy/
#   scp .env     msk-1:~/innercore/deploy/.env
```

Update `~/innercore/deploy/.env` for prod values:
- `CORS_ORIGINS=https://innercore.art,https://app.innercore.art`
- `DATABASE_URL=postgresql+asyncpg://USER:PASS@postgres:5432/DB`
- `REDIS_URL=redis://redis:6379/0`
- `S3_ENDPOINT=http://minio:9000`
- `LLM_SERVICE_URL=http://llm_service:8001`
- Strong `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, `MINIO_ROOT_PASSWORD`

First-time start (after images are available in GHCR):
```bash
cd ~/innercore/deploy
echo "$GHCR_PAT" | docker login ghcr.io -u <GH_USER> --password-stdin
IMAGE_TAG=latest ./deploy.sh
```

## CI/CD — required GitHub repo secrets

| Secret                  | Value |
|-------------------------|-------|
| `MSK1_SSH_HOST`         | `5.42.100.202` |
| `MSK1_SSH_PORT`         | `2222` |
| `MSK1_SSH_USER`         | `work` |
| `MSK1_SSH_KEY`          | Private SSH key (ed25519, no passphrase) for deploy user |
| `GHCR_DEPLOY_TOKEN`     | PAT with `read:packages` (server pulls images) |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth Web Client ID (baked into frontend bundle) |

Add deploy public key to `/home/work/.ssh/authorized_keys` on msk-1.

## CI flow

1. Push to `main`
2. GH Actions builds 4 images in parallel (backend, llm_service, frontend, landing)
3. Pushed to `ghcr.io/core-euler/sna_net-*:main-<sha7>` + `:latest`
4. Deploy job SSHs into msk-1, exports `IMAGE_TAG`, runs `deploy.sh`
5. `deploy.sh` does `docker compose pull && up -d`

Rollback: SSH to server, `IMAGE_TAG=main-<previous-sha7> ./deploy.sh`.

## Operational commands

```bash
# Tail logs
cd ~/innercore/deploy
docker compose -f docker-compose.prod.yml logs -f backend

# Check status
docker compose -f docker-compose.prod.yml ps

# Force-pull latest and restart
IMAGE_TAG=latest ./deploy.sh

# Restart single service
docker compose -f docker-compose.prod.yml restart backend
```

## Notes

- Postgres, Redis, MinIO ports are **not** exposed to host — only on `innercore_network`.
- Caddy holds 80/443; only services that need to be public go through it.
- Postgres backups are NOT configured here — add a separate cron + `pg_dump` to S3 before going to real prod.
