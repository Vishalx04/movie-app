# 🚀 Production Deployment & Operations Guide — Movie App

This document is the complete, single source of truth for the deployment architecture, configuration, exact commands, and operational procedures used to deploy the **Movie App** across **AWS EC2**, **Neon Serverless PostgreSQL**, and **Vercel**.

---

## 📑 Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Database Migration (Local PostgreSQL → Neon Cloud)](#2-database-migration-local-postgresql--neon-cloud)
3. [Backend Containerization & Optimization](#3-backend-containerization--optimization)
4. [AWS EC2 Provisioning & System Hardening](#4-aws-ec2-provisioning--system-hardening)
5. [Running the Backend on EC2](#5-running-the-backend-on-ec2)
6. [Frontend Deployment (Vercel) & The HTTPS Security Model](#6-frontend-deployment-vercel--the-https-security-model)
7. [Domain & Automated SSL Setup (Caddy Reverse Proxy)](#7-domain--automated-ssl-setup-caddy-reverse-proxy)
8. [Automated CI/CD Pipeline Blueprint (GitHub Actions)](#8-automated-cicd-pipeline-blueprint-github-actions)
9. [Operational Cheat Sheet & Maintenance](#9-operational-cheat-sheet--maintenance)

---

## 1. Architecture Overview

```
                                  ┌────────────────────────────────────────┐
                                  │             User Browser               │
                                  └──────────────────┬─────────────────────┘
                                                     │
                    ┌────────────────────────────────┴────────────────────────────────┐
                    │                                                                 │
         HTTPS Requests (HTML/JS/Assets)                                   HTTPS API Requests (JSON/Cookies)
                    │                                                                 │
                    ▼                                                                 ▼
       ┌─────────────────────────┐                                       ┌─────────────────────────┐
       │      Vercel Edge        │                                       │   AWS EC2 (us-east-2)   │
       │   Next.js 15 App        │                                       │   movie-app-backend     │
       │ movie-app-nine-livid-45 │                                       │                         │
       └─────────────────────────┘                                       │  ┌───────────────────┐  │
                                                                         │  │ Caddy / Port 443  │  │
                                                                         │  │  (Auto TLS/SSL)   │  │
                                                                         │  └─────────┬─────────┘  │
                                                                         │            │ :8000      │
                                                                         │  ┌─────────▼─────────┐  │
                                                                         │  │  Docker: API      │  │
                                                                         │  │  (FastAPI / Uvic) │  │
                                                                         │  └─────────┬─────────┘  │
                                                                         │            │            │
                                                                         │  ┌─────────▼─────────┐  │
                                                                         │  │  Docker: Redis    │  │
                                                                         │  │  (127.0.0.1:6379) │  │
                                                                         │  └───────────────────┘  │
                                                                         └────────────┬────────────┘
                                                                                      │
                                                                         Database Pool Connection
                                                                         (SSL Encrypted - Port 5432)
                                                                                      │
                                                                                      ▼
                                                                         ┌─────────────────────────┐
                                                                         │ Neon Serverless Postgres│
                                                                         │ (AWS us-east-2, Ohio)   │
                                                                         └─────────────────────────┘
```

| Component | Technology | Hosting / Infrastructure | Role |
| :--- | :--- | :--- | :--- |
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind | Vercel Serverless Edge | UI, Client State, SSR/SSG |
| **Backend API** | FastAPI, Uvicorn, Python 3.11, Pydantic v2 | AWS EC2 `t3.small` (`us-east-2`) | REST API, Auth, Business Logic |
| **Database** | PostgreSQL 16 | Neon Serverless (`us-east-2`) | Persistent data storage, Pooling |
| **Cache / Broker** | Redis 7 | AWS EC2 (Dockerized) | Rate limiting, async task queue |
| **Reverse Proxy** | Caddy v2 (or Nginx) | AWS EC2 (Native or Docker) | Automatic Let's Encrypt SSL, Proxy |

---

## 2. Database Migration (Local PostgreSQL → Neon Cloud)

### 2.1 Why Migrate?
Local PostgreSQL running inside a local Docker container (`movie-postgres`) cannot be reached by cloud deployments. **Neon** provides managed, serverless PostgreSQL with automated backups, branching, and connection pooling. Placing Neon in AWS region **`us-east-2` (Ohio)** ensures single-digit millisecond latency to our EC2 backend.

### 2.2 Export Local Database Dump
**Executed from developer machine terminal in repository root (`c:\Users\HP\Desktop\movie-app`):**

```powershell
docker exec -t movie-postgres pg_dump -U postgres -d movie_db --clean --if-exists > dump.sql
```

*Notes:*
- `--clean`: Generates `DROP TABLE IF EXISTS` statements before creating tables.
- `--if-exists`: Prevents errors if tables don't exist yet on the target database.

### 2.3 Restore Dump to Neon Cloud Database
Neon requires SSL mode (`sslmode=require`). Using an ephemeral Docker container avoids installing PostgreSQL client tools on Windows:

```powershell
docker run --rm -i -v ${PWD}:/data postgres:16 psql "postgresql://<user>:<password>@<neon-host>/movie_db?sslmode=require" -f /data/dump.sql
```

### 2.4 Verifying the Migration
Verify table counts and row counts on Neon:
```powershell
docker run --rm -i postgres:16 psql "postgresql://<user>:<password>@<neon-host>/movie_db?sslmode=require" -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
```

### 2.5 Connection String Format in Production
In `apps/api/.env`:
```ini
DATABASE_URL=postgresql+psycopg2://<neon_user>:<neon_password>@<neon_host>/movie_db?sslmode=require
```
*Best Practice:* Neon provides two endpoints:
- **Direct connection:** `<project-id>.us-east-2.aws.neon.tech` (ideal for Alembic migrations and persistent pools).
- **Pooled connection (PgBouncer):** `<project-id>-pooler.us-east-2.aws.neon.tech` (recommended for serverless environments with high concurrency).

---

## 3. Backend Containerization & Optimization

### 3.1 `apps/api/Dockerfile`
Key production patterns implemented:
1. **Unprivileged User (`appuser`, UID 1000):** Containers never run as root.
2. **CPU-only PyTorch optimization:** Standard `sentence-transformers` pulls in ~4.5 GB of NVIDIA CUDA binary wheels. Pre-installing CPU PyTorch cuts image build size down to ~180 MB, preventing EC2 disk exhaustion (`[Errno 28] No space left on device`).

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged user
RUN useradd -m -u 1000 appuser

# Install CPU-only PyTorch first (avoids downloading 4.5GB CUDA packages)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3.2 `apps/api/.dockerignore`
Prevents copying host binaries, virtualenvs, local caches, and large ML model checkpoints into the Docker context:
```ini
venv/
__pycache__/
*.pyc
.env
.env.*
app/ml/models/*.pkl
celerybeat-schedule*
.pytest_cache/
tests/
.git/
```

### 3.3 `infra/docker-compose.yml`
Local `postgres` was completely removed; `api` points directly to cloud Neon DB via `.env`, and `redis` is bound exclusively to `127.0.0.1` so port 6379 is never exposed to the public internet:

```yaml
services:
  api:
    build:
      context: ../apps/api
      dockerfile: Dockerfile
    container_name: movie-api
    restart: always
    ports:
      - "8000:8000"
    env_file:
      - ../apps/api/.env
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    container_name: movie-redis
    restart: always
    ports:
      - "127.0.0.1:6379:6379"
```

### 3.4 Production Code Fixes Applied
- **`apps/api/app/core/config.py`**:
  - Removed dead `SECRET_KEY` (auth exclusively uses `JWT_SECRET_KEY`).
  - Set `DATABASE_URL: str` as required with no default localhost fallback.
  - Set `case_sensitive = True` in Pydantic Config.
- **`apps/api/app/api/v1/auth.py`**:
  - Refresh cookie configured with `secure=True` and `samesite="none"` when `APP_ENV != "development"` to allow secure cross-domain transmission from Vercel to EC2.
- **`apps/api/migrations/env.py`**:
  - Alembic now dynamically reads `settings.DATABASE_URL` instead of relying on hardcoded localhost in `alembic.ini`.
- **`apps/api/app/ml/model_loader.py`**:
  - Gracefully checks `if not MODEL_PATH.exists(): return None` to prevent cold-start container crashes when large binary `.pkl` files are not present in git.

---

## 4. AWS EC2 Provisioning & System Hardening

### 4.1 Instance Details
- **Name:** `movie-app-backend`
- **Instance Type:** `t3.small` (2 vCPU, 2.0 GiB RAM)
- **AMI:** Ubuntu 24.04 LTS (Noble Numbat), 64-bit (x86_64)
- **Region:** `us-east-2` (Ohio)
- **Public IPv4:** `3.21.27.173`

### 4.2 Security Group Rules (`movie-app-sg`)
| Type | Protocol | Port Range | Source | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| SSH | TCP | 22 | Your IP / My IP | Secure server administration |
| Custom TCP | TCP | 8000 | `0.0.0.0/0` | Direct backend API access (Dev/Staging) |
| HTTP | TCP | 80 | `0.0.0.0/0` | Let's Encrypt ACME verification & HTTP redirect |
| HTTPS | TCP | 443 | `0.0.0.0/0` | Secure SSL production API traffic |

### 4.3 EBS Volume Storage Expansion
Initial 20 GB volume reached capacity during Docker builds. Expanded to 35 GB:
1. In AWS Management Console: **EC2 → Volumes → Select Volume → Actions → Modify Volume → Size: 35 GiB**.
2. Run partition and filesystem expansion in Ubuntu SSH session:

```bash
# Expand the partition table
sudo growpart /dev/nvme0n1 1 2>/dev/null || sudo growpart /dev/xvda 1 2>/dev/null

# Expand the ext4 filesystem online without reboot
sudo resize2fs /dev/root 2>/dev/null || sudo resize2fs /dev/nvme0n1p1 2>/dev/null

# Verify free space (should show ~17-18 GB available)
df -h /
```

### 4.4 Docker Engine Installation (Ubuntu 24.04)
Run on EC2 to install official Docker and Compose v2:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Grant non-root access
sudo usermod -aG docker $USER
newgrp docker
```

---

## 5. Running the Backend on EC2

### 5.1 Clone Codebase
```bash
cd ~
git clone https://github.com/Vishalx04/movie-app.git
cd ~/movie-app
```

### 5.2 Configure Environment Variables
Create the production environment file at `~/movie-app/apps/api/.env`:

```bash
nano ~/movie-app/apps/api/.env
```

Populate with production values:
```ini
APP_ENV=production
APP_TITLE=Movie App
APP_VERSION=0.1.0

DATABASE_URL=postgresql+psycopg2://<neon_user>:<neon_password>@<neon_host>/movie_db?sslmode=require

ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_SECRET_KEY=<generate_secure_random_key_using_openssl_rand_hex_32>
JWT_ALGORITHM=HS256

TMDB_READ_ACCESS_TOKEN=<your_tmdb_jwt_token>
TMDB_BASE_URL=https://api.themoviedb.org/3
TMDB_IMAGE_BASE_URL=https://image.tmdb.org/t/p/original

REDIS_URL=redis://redis:6379/0

ALLOWED_ORIGINS=["https://movie-app-nine-livid-45.vercel.app","http://localhost:3000"]

GROQ_API_KEY=<your_groq_api_key>
```

**Lock file permissions so only root/owner can read:**
```bash
chmod 600 ~/movie-app/apps/api/.env
```

### 5.3 Build & Start Containers
```bash
cd ~/movie-app/infra
docker compose up -d --build
```

*In case of stale container name conflict:*
```bash
docker compose down --remove-orphans
docker compose up -d
```

### 5.4 Verify Server Health
```bash
# Internal check on EC2
curl http://localhost:8000/health
# Output: {"database":"connected","status":"healthy"}

# External check from developer machine or browser
curl http://3.21.27.173:8000/health
```

---

## 6. Frontend Deployment (Vercel) & The HTTPS Security Model

### 6.1 The Problem: Browser Mixed-Content Blocking
- The frontend is served via Vercel at `https://movie-app-nine-livid-45.vercel.app` (Encrypted / HTTPS).
- When the frontend calls `http://3.21.27.173:8000/api/v1/movies/`, web browsers enforce the **W3C Mixed Content Specification**:
  > *"An HTTPS page may not make asynchronous XMLHttpRequest or fetch requests to an insecure HTTP URL."*
- The browser halts the request before sending any bytes over the network, displaying:
  `Status: (blocked:mixed-content)`
  `A Provisional headers are shown`

### 6.2 Why Next.js Rewrites Were Reverted
We tested a temporary Next.js rewrite proxy in `next.config.ts`. While it routed requests, it introduced:
1. Significant latency overhead (browser → Vercel serverless function → EC2 → Vercel → browser).
2. Consumption of Vercel serverless execution limits on every single API call.
3. Obfuscation of real client IP addresses.
4. Masking underlying network errors as 308 redirects.

**Decision:** The rewrite was cleanly reverted. In production, web clients should communicate directly with the API over HTTPS.

---

## 7. Domain & Automated SSL Setup (Caddy Reverse Proxy)

This is the standard, production-grade solution.

### Step 1: Assign an AWS Elastic IP (Static IPv4)
AWS EC2 public IP addresses are dynamic and change if an instance is stopped and started.
1. Go to **AWS Console → EC2 → Network & Security → Elastic IPs**.
2. Click **Allocate Elastic IP address** (`us-east-2`).
3. Select the allocated IP → **Actions → Associate Elastic IP address**.
4. Choose Instance: `movie-app-backend` → Click **Associate**.
*(AWS Free Tier includes 1 Elastic IP free of charge while associated with a running instance).*

### Step 2: Map Domain DNS
Create an **A Record** at your DNS registrar (Namecheap, GoDaddy, Cloudflare, Route 53, or free DuckDNS):
- **Type:** `A`
- **Name / Host:** `api` (e.g., `api.yourdomain.com`) or `@` for apex domain.
- **Value / Target:** Your EC2 Elastic IP address.
- **TTL:** `300` (5 minutes).

### Step 3: Install Caddy Reverse Proxy on EC2
Caddy automatically provisions, verifies, and renews SSL certificates via Let's Encrypt with zero manual intervention:

```bash
# Install Caddy on Ubuntu 24.04
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLF 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLF 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

### Step 4: Configure `/etc/caddy/Caddyfile`
Edit the Caddyfile:
```bash
sudo nano /etc/caddy/Caddyfile
```

Replace its contents with:
```caddy
api.yourdomain.com {
    reverse_proxy localhost:8000
}
```

Reload Caddy:
```bash
sudo systemctl reload caddy
```

*Caddy automatically performs the ACME TLS handshake, requests the certificate from Let's Encrypt, binds Port 443, and forwards all requests to `http://localhost:8000`.*

### Step 5: Update Vercel Environment Variable
1. Open **Vercel Dashboard → movie-app project → Settings → Environment Variables**.
2. Edit or add `NEXT_PUBLIC_API_URL`:
   - **Value:** `https://api.yourdomain.com/api/v1`
   - **Environments:** Production, Preview, Development.
3. Trigger a redeploy: **Deployments → Select latest deployment → Redeploy**.

---

## 8. Automated CI/CD Pipeline Blueprint (GitHub Actions)

When you are ready to automate deployments, create `.github/workflows/deploy.yml` in your repository. This triggers automated tests on pull requests and deploys to EC2 on push to `main`.

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    name: Run Unit & Integration Tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: password
          POSTGRES_DB: movie_db_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install Dependencies
        run: |
          pip install --upgrade pip
          pip install torch --index-url https://download.pytorch.org/whl/cpu
          pip install -r apps/api/requirements.txt

      - name: Run Pytest
        env:
          DATABASE_URL: postgresql+psycopg2://postgres:password@localhost:5432/movie_db_test
          TEST_DATABASE_URL: postgresql+psycopg2://postgres:password@localhost:5432/movie_db_test
          JWT_SECRET_KEY: testsecretkeyformockingenvironments12345
          TMDB_READ_ACCESS_TOKEN: mock_token
          GROQ_API_KEY: mock_key
          APP_ENV: testing
        run: |
          cd apps/api
          pytest

  deploy:
    name: Deploy to EC2
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ubuntu
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd ~/movie-app
            git pull origin main
            cd infra
            docker compose up -d --build
            docker image prune -f
```

---

## 9. Operational Cheat Sheet & Maintenance

### 9.1 Container Management (Execute inside `~/movie-app/infra`)
```bash
# Check status of containers
docker compose ps

# View live API logs
docker compose logs -f api

# View live Redis logs
docker compose logs -f redis

# Restart the API container
docker compose restart api

# Rebuild and restart API after pulling new code
docker compose up -d --build api

# Stop all containers
docker compose down
```

### 9.2 Disk & Resource Monitoring
```bash
# Check disk usage
df -h /

# Check live memory and CPU usage per container
docker stats --no-stream

# Prune unused build caches and dangling images
docker system prune -f
```

### 9.3 Database Migrations (Alembic)
To run database schema migrations against Neon from the EC2 instance:
```bash
docker exec -it movie-api alembic upgrade head
```

---
*Document Version: 1.0.0 | Updated: November 2026*
