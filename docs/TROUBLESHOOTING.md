# Troubleshooting CLMS

Panduan penyelesaian masalah umum yang sering ditemui saat development dan deployment CLMS.

---

## Daftar Isi

1. [ModuleNotFoundError](#1-modulenotfounderror)
2. [Python 3.14 Compatibility Issue](#2-python-314-compatibility-issue)
3. [HTTP 402 Payment Required](#3-http-402-payment-required)
4. [HTTP 429 Too Many Requests](#4-http-429-too-many-requests)
5. [HTTP 401 Unauthorized](#5-http-401-unauthorized)
6. [Telemetry Warning ChromaDB](#6-telemetry-warning-chromadb)
7. [WinError 32 (Windows)](#7-winerror-32-windows)
8. [Template Tidak Muncul di Dashboard](#8-template-tidak-muncul-di-dashboard)
9. [Frontend Blank / Halaman Kosong](#9-frontend-blank--halaman-kosong)
10. [Prompt Too Large / Context Length Exceeded](#10-prompt-too-large--context-length-exceeded)
11. [Export DOCX Gagal](#11-export-docx-gagal)
12. [Upload File Gagal](#12-upload-file-gagal)

---

## 1. ModuleNotFoundError

### Gejala

```
ModuleNotFoundError: No module named 'chromadb'
ModuleNotFoundError: No module named 'langchain'
ModuleNotFoundError: No module named 'fastapi'
```

### Penyebab

- Virtual environment belum diaktifkan
- Dependencies belum di-install
- Menggunakan Python system alih-alih venv

### Solusi

```bash
# Pastikan berada di folder backend
cd backend

# Aktifkan virtual environment
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Install ulang dependencies
pip install -r requirements.txt
```

Jika venv belum dibuat:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 2. Python 3.14 Compatibility Issue

### Gejala

```
ERROR: Could not find a version that satisfies the requirement chromadb==0.4.22
ERROR: No matching distribution found for chromadb==0.4.22
```

Atau error terkait `distutils`, `imp`, atau `pkgutil` deprecated modules.

### Penyebab

Python 3.14 menghapus beberapa modul legacy (`distutils`, `imp`) yang masih digunakan oleh beberapa library seperti ChromaDB versi lama dan langchain.

### Solusi

Gunakan Python 3.10, 3.11, atau 3.12:

```bash
# Cek versi Python
python3 --version

# Install Python 3.11 jika belum ada (Ubuntu)
sudo apt install python3.11 python3.11-venv

# Buat venv dengan Python 3.11
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Jika menggunakan `pyenv`:

```bash
pyenv install 3.11.7
pyenv local 3.11.7
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 3. HTTP 402 Payment Required

### Gejala

```
HTTP 402: Payment Required
{"error": "Insufficient balance", "detail": "..."}
```

### Penyebab

Saldo/kredit API LLM (DeepSeek, Groq, atau provider lain) sudah habis.

### Solusi

1. Cek saldo di dashboard provider API:
   - DeepSeek: https://platform.deepseek.com
   - Groq: https://console.groq.com
2. Top-up kredit atau upgrade plan
3. Untuk development, pertimbangkan menggunakan model gratis atau LLM lokal (LMStudio)
4. Jika menggunakan LMStudio, ubah `.env`:

```env
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL_NAME=local-model
LLM_API_KEY=not-needed
```

---

## 4. HTTP 429 Too Many Requests

### Gejala

```
HTTP 429: Too Many Requests
{"error": "Rate limit exceeded", "retry_after": 60}
```

### Penyebab

Terlalu banyak request ke API LLM dalam waktu singkat (rate limit).

### Solusi

1. **Tunggu** sesuai `retry_after` yang diberikan API
2. **Kurangi frekuensi** request - jangan spam tombol "Generate"
3. **Implementasi retry logic** dengan exponential backoff (sudah ada di `llm_service.py`)
4. **Upgrade plan** API jika rate limit terlalu rendah untuk kebutuhan
5. Untuk testing intensif, gunakan LLM lokal:

```env
LLM_BASE_URL=http://localhost:1234/v1
```

---

## 5. HTTP 401 Unauthorized

### Gejala

```
HTTP 401: Unauthorized
{"error": "Invalid API key", "message": "..."}
```

### Penyebab

- API key salah atau expired
- API key belum di-set di file `.env`
- File `.env` tidak terbaca

### Solusi

1. Cek file `backend/.env`:

```bash
cat backend/.env | grep LLM_API_KEY
```

2. Pastikan API key valid dan tidak ada spasi/newline tambahan:

```env
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

3. Generate API key baru jika expired
4. Restart backend setelah mengubah `.env`:

```bash
# Kill proses lama
sudo systemctl restart clms-backend
# atau jika manual:
# Ctrl+C lalu jalankan ulang uvicorn
```

---

## 6. Telemetry Warning ChromaDB

### Gejala

```
WARNING: Anonymized telemetry enabled. To disable, set ANONYMIZED_TELEMETRY=False
```

Atau:

```
chromadb.telemetry.product.posthog - WARNING - Failed to send telemetry event
```

### Penyebab

ChromaDB secara default mengirim data telemetry anonim. Warning muncul jika pengiriman gagal (offline) atau belum di-disable.

### Solusi

Ini hanya **warning** dan tidak mempengaruhi fungsionalitas. Untuk menghilangkan:

1. Tambahkan di file `.env`:

```env
ANONYMIZED_TELEMETRY=False
```

2. Atau set environment variable sebelum menjalankan:

```bash
export ANONYMIZED_TELEMETRY=False
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

3. Atau set secara programatis sebelum import chromadb:

```python
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
import chromadb
```

---

## 7. WinError 32 (Windows)

### Gejala

```
PermissionError: [WinError 32] The process cannot access the file because it is being used by another process
```

### Penyebab

File ChromaDB (SQLite) sedang diakses oleh proses lain. Biasanya terjadi saat:
- Menjalankan 2 instance backend bersamaan
- IDE (VS Code) mengunci file database
- Proses sebelumnya belum terminate dengan benar

### Solusi

1. **Tutup instance backend lain**:

```powershell
# Cari proses Python yang menggunakan port 8000
netstat -ano | findstr :8000
# Kill proses berdasarkan PID
taskkill /PID <pid_number> /F
```

2. **Restart VS Code** atau tutup terminal lain yang menjalankan backend

3. **Hapus lock file** ChromaDB jika ada:

```powershell
# Hati-hati: pastikan backend tidak sedang berjalan
Remove-Item backend\data\chroma_db\chroma.sqlite3-journal -ErrorAction SilentlyContinue
```

4. **Gunakan satu terminal saja** untuk menjalankan backend

5. Jika masih terjadi, hapus database dan ingest ulang:

```powershell
Remove-Item -Recurse backend\data\chroma_db
python scripts\ingest_templates.py
```

---

## 8. Template Tidak Muncul di Dashboard

### Gejala

- Halaman Template Library kosong
- Tidak ada card template yang tampil
- API `/api/templates` mengembalikan array kosong `[]`

### Penyebab

- Template belum di-ingest ke ChromaDB
- Folder `data/templates` kosong
- ChromaDB corrupt atau belum diinisialisasi

### Solusi

1. **Cek apakah template files ada**:

```bash
ls backend/data/templates/
```

2. **Jalankan ingest ulang**:

```bash
cd backend
source venv/bin/activate
python scripts/ingest_templates.py
```

3. **Verifikasi melalui API**:

```bash
curl http://localhost:8000/api/templates
```

4. Jika masih kosong, **reset ChromaDB**:

```bash
rm -rf backend/data/chroma_db
python scripts/ingest_templates.py
```

5. Pastikan backend sudah restart setelah ingest

---

## 9. Frontend Blank / Halaman Kosong

### Gejala

- Browser menampilkan halaman putih kosong
- Console browser menunjukkan error JavaScript
- Tidak ada komponen yang ter-render

### Penyebab

- Backend tidak berjalan (API unreachable)
- CORS error
- Build frontend rusak
- Environment variable API URL salah

### Solusi

1. **Cek apakah backend berjalan**:

```bash
curl http://localhost:8000/docs
# Harus mengembalikan Swagger UI HTML
```

2. **Cek Console browser** (F12 > Console):
   - Jika ada CORS error, pastikan backend mengizinkan origin frontend
   - Jika ada network error, pastikan URL API benar

3. **Rebuild frontend**:

```bash
cd frontend
rm -rf node_modules .svelte-kit
npm install
npm run dev
```

4. **Cek environment** frontend mengarah ke backend yang benar:

```bash
# Development
# API URL biasanya hardcoded di frontend/src/lib/api/client.ts
```

5. **Cek versi Node.js** (harus 18.x atau 20.x):

```bash
node --version
```

---

## 10. Prompt Too Large / Context Length Exceeded

### Gejala

```
Error: Maximum context length exceeded
{"error": "prompt_too_large", "max_tokens": 8192, "requested_tokens": 12500}
```

Atau respons AI terpotong / tidak lengkap.

### Penyebab

- Terlalu banyak klausul yang di-retrieve dari ChromaDB
- Template kontrak terlalu panjang
- Model LLM memiliki context window terbatas

### Solusi

1. **Kurangi jumlah klausul** yang di-retrieve:
   - Edit parameter `top_k` di `backend/app/rag/retriever.py`
   - Default biasanya 10, coba kurangi ke 5-7

2. **Gunakan model dengan context lebih besar**:

```env
# DeepSeek Chat mendukung 32K context
LLM_MODEL_NAME=deepseek-chat

# Atau gunakan model 128K context jika tersedia
```

3. **Optimasi prompt** di `backend/app/rag/prompts.py`:
   - Kurangi system prompt yang tidak perlu
   - Ringkas instruksi

4. **Pilih klausul secara selektif** - jangan centang semua klausul saat generate

---

## 11. Export DOCX Gagal

### Gejala

```
Error: Export failed
Internal Server Error saat download DOCX
```

Atau file `.docx` yang dihasilkan corrupt / tidak bisa dibuka.

### Penyebab

- Library `python-docx` error karena HTML tidak valid
- Content mengandung karakter yang tidak didukung
- Memory tidak cukup untuk dokumen besar
- Template DOCX base corrupt

### Solusi

1. **Cek log backend** untuk detail error:

```bash
sudo journalctl -u clms-backend --since "5 minutes ago"
# atau lihat terminal jika manual
```

2. **Validasi content** sebelum export:
   - Pastikan tidak ada tag HTML yang rusak di editor
   - Hapus karakter special yang tidak umum

3. **Test export dengan content minimal**:
   - Coba export dengan hanya 1-2 paragraf untuk isolasi masalah

4. **Reinstall python-docx**:

```bash
pip install --force-reinstall python-docx==1.1.0
```

5. **Cek disk space**:

```bash
df -h
# Pastikan ada cukup ruang untuk generate file
```

---

## 12. Upload File Gagal

### Gejala

```
Error: Upload failed
HTTP 413: Request Entity Too Large
Error: File type not supported
```

### Penyebab

- File terlalu besar (melebihi limit)
- Tipe file tidak didukung
- Folder upload tidak writable
- Nginx membatasi upload size

### Solusi

1. **Cek ukuran file** - default limit biasanya 10-50 MB

2. **Pastikan tipe file didukung**:
   - `.xlsx` untuk template Excel
   - `.docx` untuk template Word

3. **Cek permission folder upload**:

```bash
ls -la backend/data/uploads/
# Pastikan writable oleh user yang menjalankan backend
sudo chown -R www-data:www-data backend/data/uploads/
sudo chmod 755 backend/data/uploads/
```

4. **Jika pakai Nginx**, naikkan limit upload:

```nginx
# Di /etc/nginx/sites-available/clms
client_max_body_size 50M;
```

Lalu reload:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

5. **Cek disk space**:

```bash
df -h /opt/clms/backend/data/uploads/
```

6. **Buat folder uploads** jika belum ada:

```bash
mkdir -p backend/data/uploads
chmod 755 backend/data/uploads
```

---

## Tips Umum Debugging

### Melihat Log Backend

```bash
# Jika pakai systemd
sudo journalctl -u clms-backend -f

# Jika manual
# Output akan langsung terlihat di terminal
```

### Melihat Log Frontend

```bash
# Browser DevTools: F12 > Console
# Network tab untuk cek API calls
```

### Reset Lengkap (Nuclear Option)

Jika semua troubleshooting gagal, lakukan reset lengkap:

```bash
cd /opt/clms

# Backend
cd backend
rm -rf venv data/chroma_db __pycache__
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/ingest_templates.py

# Frontend
cd ../frontend
rm -rf node_modules .svelte-kit build
npm install
npm run build
```

### Mendapatkan Bantuan

Jika masalah belum terselesaikan:
1. Cek issue di repository GitHub
2. Sertakan log error lengkap
3. Sebutkan OS, versi Python, versi Node.js
4. Jelaskan langkah yang sudah dicoba
