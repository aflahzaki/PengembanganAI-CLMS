# Panduan Deployment CLMS

## Daftar Isi

1. [Persyaratan Server](#persyaratan-server)
2. [Deployment Manual](#deployment-manual)
3. [Deployment dengan Docker](#deployment-dengan-docker)
4. [Konfigurasi Nginx (Reverse Proxy)](#konfigurasi-nginx-reverse-proxy)
5. [Systemd Service](#systemd-service)
6. [Environment Variables](#environment-variables)
7. [Post-Deployment Checklist](#post-deployment-checklist)

---

## Persyaratan Server

### Minimum Hardware

| Komponen | Minimum | Rekomendasi |
|----------|---------|-------------|
| CPU | 2 core | 4 core |
| RAM | 4 GB | 8 GB |
| Storage | 20 GB SSD | 50 GB SSD |
| Network | 100 Mbps | 1 Gbps |

### Software Requirements

- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **Python**: 3.10 - 3.12 (jangan gunakan 3.14, belum didukung beberapa library)
- **Node.js**: 18.x atau 20.x LTS
- **npm**: 9.x+
- **Git**: 2.x+
- **Docker** (opsional): 24.x+ dengan Docker Compose v2

---

## Deployment Manual

### 1. Clone Repository

```bash
cd /opt
git clone https://github.com/aflahzaki/PengembanganAI-CLMS.git clms
cd clms
```

### 2. Setup Backend

```bash
cd backend

# Buat virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Buat file .env
cp .env.example .env  # atau buat manual
```

Edit file `.env`:

```env
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat
LLM_API_KEY=sk-your-api-key-here
CHROMA_DB_PATH=data/chroma_db
TEMPLATES_DIR=data/templates
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 3. Ingest Template Data

```bash
# Pastikan virtual environment aktif
source venv/bin/activate

# Jalankan script ingest untuk memuat template ke ChromaDB
python scripts/ingest_templates.py
```

### 4. Setup Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Build untuk production
npm run build
```

### 5. Jalankan Aplikasi

Terminal 1 (Backend):
```bash
cd /opt/clms/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Terminal 2 (Frontend):
```bash
cd /opt/clms/frontend
npm run preview -- --host 0.0.0.0 --port 3000
```

---

## Deployment dengan Docker

### Dockerfile Backend

Buat `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ingest templates saat build
RUN python scripts/ingest_templates.py || true

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile Frontend

Buat `frontend/Dockerfile`:

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json .
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

CMD ["node", "build"]
```

### Docker Compose

Buat `docker-compose.yml` di root project:

```yaml
version: "3.8"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    volumes:
      - chroma_data:/app/data/chroma_db
      - ./backend/data/templates:/app/data/templates
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  chroma_data:
```

### Menjalankan dengan Docker

```bash
# Build dan jalankan semua service
docker compose up -d --build

# Lihat logs
docker compose logs -f

# Stop semua service
docker compose down
```

---

## Konfigurasi Nginx (Reverse Proxy)

### Install Nginx

```bash
sudo apt update
sudo apt install nginx -y
```

### Konfigurasi Virtual Host

Buat file `/etc/nginx/sites-available/clms`:

```nginx
server {
    listen 80;
    server_name clms.yourdomain.com;

    # Redirect HTTP ke HTTPS (opsional, aktifkan jika pakai SSL)
    # return 301 https://$server_name$request_uri;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout untuk request yang lama (AI generation)
        proxy_read_timeout 120s;
        proxy_connect_timeout 30s;
        proxy_send_timeout 120s;
    }

    # Upload size limit
    client_max_body_size 50M;
}
```

### Konfigurasi HTTPS dengan Certbot (Opsional)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d clms.yourdomain.com
```

### Aktifkan Site

```bash
sudo ln -s /etc/nginx/sites-available/clms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Systemd Service

### Backend Service

Buat file `/etc/systemd/system/clms-backend.service`:

```ini
[Unit]
Description=CLMS Backend (FastAPI)
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/clms/backend
Environment="PATH=/opt/clms/backend/venv/bin:/usr/local/bin:/usr/bin"
EnvironmentFile=/opt/clms/backend/.env
ExecStart=/opt/clms/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Frontend Service

Buat file `/etc/systemd/system/clms-frontend.service`:

```ini
[Unit]
Description=CLMS Frontend (SvelteKit)
After=network.target clms-backend.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/clms/frontend
ExecStart=/usr/bin/node build
Environment="PORT=3000"
Environment="HOST=0.0.0.0"
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Mengaktifkan Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable dan start backend
sudo systemctl enable clms-backend
sudo systemctl start clms-backend

# Enable dan start frontend
sudo systemctl enable clms-frontend
sudo systemctl start clms-frontend

# Cek status
sudo systemctl status clms-backend
sudo systemctl status clms-frontend

# Lihat logs
sudo journalctl -u clms-backend -f
sudo journalctl -u clms-frontend -f
```

---

## Environment Variables

| Variable | Deskripsi | Default | Required |
|----------|-----------|---------|----------|
| `LLM_BASE_URL` | URL endpoint LLM API | `https://api.deepseek.com/v1` | Ya |
| `LLM_MODEL_NAME` | Nama model LLM | `deepseek-chat` | Ya |
| `LLM_API_KEY` | API key untuk LLM | - | Ya |
| `CHROMA_DB_PATH` | Path penyimpanan ChromaDB | `data/chroma_db` | Tidak |
| `TEMPLATES_DIR` | Path folder templates | `data/templates` | Tidak |
| `HOST` | Host binding server | `0.0.0.0` | Tidak |
| `PORT` | Port backend | `8000` | Tidak |
| `DEBUG` | Mode debug | `false` | Tidak |

---

## Post-Deployment Checklist

- [ ] Backend berjalan dan merespons di `http://server:8000/docs`
- [ ] Frontend berjalan dan bisa diakses di `http://server:3000`
- [ ] API key LLM sudah dikonfigurasi dengan benar
- [ ] Template sudah di-ingest ke ChromaDB
- [ ] Nginx reverse proxy berfungsi
- [ ] SSL/HTTPS sudah aktif (production)
- [ ] Systemd service di-enable untuk auto-start
- [ ] Firewall mengizinkan port 80/443
- [ ] Backup strategy untuk `data/chroma_db`
- [ ] Log rotation sudah dikonfigurasi

---

## Tips Production

1. **Selalu gunakan HTTPS** di production untuk keamanan data kontrak
2. **Batasi akses** ke endpoint `/docs` (Swagger UI) di production
3. **Monitor disk usage** karena ChromaDB dan upload files bisa membesar
4. **Backup berkala** folder `data/` yang berisi database vector dan template
5. **Rate limiting** disarankan di Nginx untuk mencegah abuse API
