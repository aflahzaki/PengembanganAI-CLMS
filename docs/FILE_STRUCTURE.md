# Struktur File Project CLMS

Penjelasan setiap file dan folder dalam project CLMS (Contract Lifecycle Management System) untuk memudahkan pemahaman bagi developer baru maupun non-teknis.

---

## Daftar Isi

1. [Struktur Root](#struktur-root)
2. [Backend](#backend)
3. [Frontend](#frontend)
4. [Docs](#docs)
5. [File Template Kontrak](#file-template-kontrak)

---

## Struktur Root

```
PengembanganAI-CLMS/
├── backend/              # Kode server (Python FastAPI)
├── frontend/             # Kode tampilan web (SvelteKit)
├── docs/                 # Dokumentasi project
├── postman/              # Koleksi API untuk testing
├── Template Kontrak - Mentah/  # File template mentah
├── *.docx               # Template kontrak Word (sumber data)
├── *.xlsx               # Pemetaan klausul kontrak
├── *.png                # Screenshot/gambar referensi
├── README.md            # Penjelasan umum project
└── Link Figma CLMS app pengembangan.txt  # Link desain UI
```

| File/Folder | Penjelasan |
|-------------|-----------|
| `README.md` | Halaman utama dokumentasi, berisi deskripsi project, cara install, dan cara menjalankan |
| `*.docx` | Template kontrak PLN dalam format Word, menjadi sumber data untuk sistem |
| `CLMS Pemetaan Kontrak.xlsx` | Spreadsheet pemetaan klausul-klausul kontrak beserta variabelnya |
| `*.png` | Gambar screenshot atau diagram untuk referensi visual |
| `postman/` | File koleksi Postman untuk menguji API backend tanpa frontend |

---

## Backend

Backend adalah "otak" aplikasi yang memproses data, berkomunikasi dengan AI, dan menyimpan informasi.

```
backend/
├── app/
│   ├── __init__.py          # Penanda bahwa folder ini adalah package Python
│   ├── main.py              # Entry point aplikasi, mendaftarkan semua routes
│   ├── config.py            # Konfigurasi (API keys, paths, settings)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py  # Dependency injection (koneksi database, dll)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── templates.py      # API endpoint untuk manajemen template
│   │       ├── drafting.py       # API endpoint untuk generate draft kontrak
│   │       ├── export.py         # API endpoint untuk export ke DOCX
│   │       └── docx_templates.py # API endpoint untuk upload template DOCX
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py     # Konfigurasi koneksi database
│   │   └── schemas.py      # Definisi struktur data (request/response)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py           # Komunikasi dengan AI (LLM)
│   │   ├── drafting_service.py      # Logika pembuatan draft kontrak
│   │   ├── export_service.py        # Logika export ke Word
│   │   └── docx_template_service.py # Logika manajemen template DOCX
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embeddings.py       # Mengubah teks jadi vektor (angka)
│   │   ├── ingest.py           # Memuat data template ke database vektor
│   │   ├── retriever.py        # Mencari klausul yang relevan
│   │   ├── prompts.py          # Template prompt untuk AI
│   │   └── template_registry.py # Daftar template yang tersedia
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── excel_parser.py   # Membaca dan memproses file Excel
│   │   └── text_processing.py # Utilitas pengolahan teks
│   └── middleware/           # Middleware (logging, CORS, dll)
├── data/
│   ├── chroma_db/           # Database vektor ChromaDB (auto-generated)
│   ├── templates/           # File template yang sudah diproses
│   └── uploads/             # File yang diupload user
├── scripts/
│   ├── ingest_templates.py  # Script untuk memuat template ke database
│   └── test_integration.py  # Script testing integrasi
├── tests/                   # Unit tests
├── requirements.txt         # Daftar library Python yang dibutuhkan
└── README.md               # Dokumentasi khusus backend
```

### Penjelasan Folder Utama Backend

| Folder | Fungsi |
|--------|--------|
| `app/api/routes/` | Menerima request dari frontend, seperti "pintu masuk" untuk setiap fitur |
| `app/services/` | Logika bisnis utama - memproses data dan menjalankan fitur |
| `app/rag/` | RAG (Retrieval-Augmented Generation) - sistem pencarian cerdas yang membantu AI menemukan klausul yang tepat |
| `app/models/` | Mendefinisikan "bentuk" data yang digunakan aplikasi |
| `app/utils/` | Fungsi pembantu yang dipakai di berbagai tempat |
| `data/` | Tempat menyimpan data (database, template, file upload) |
| `scripts/` | Script yang dijalankan manual untuk setup atau maintenance |

---

## Frontend

Frontend adalah tampilan web yang dilihat dan digunakan oleh pengguna.

```
frontend/
├── src/
│   ├── app.html             # Template HTML dasar
│   ├── app.css              # Style global
│   ├── app.d.ts             # Type definitions
│   ├── lib/
│   │   ├── index.ts         # Export utama library
│   │   ├── api/
│   │   │   └── client.ts    # Kode untuk berkomunikasi dengan backend
│   │   ├── components/
│   │   │   ├── ClauseToggle.svelte    # Tombol on/off untuk klausul
│   │   │   ├── ContractForm.svelte    # Form input data kontrak
│   │   │   ├── ExportButton.svelte    # Tombol export ke Word
│   │   │   ├── TemplateCard.svelte    # Kartu template di dashboard
│   │   │   ├── TipTapEditor.svelte    # Editor teks kaya (rich text)
│   │   │   └── Toast.svelte           # Notifikasi pop-up
│   │   └── stores/
│   │       └── contract.ts  # State management (menyimpan data sementara)
│   └── routes/
│       ├── +layout.svelte   # Layout utama (header, sidebar)
│       ├── +page.svelte     # Halaman utama (Template Library)
│       └── draft/
│           └── +page.svelte # Halaman draft kontrak
├── static/                  # File statis (gambar, favicon)
├── package.json             # Daftar library JavaScript dan scripts
├── package-lock.json        # Lock file versi library (auto-generated)
├── vite.config.ts           # Konfigurasi build tool (Vite)
├── tailwind.config.js       # Konfigurasi CSS framework (Tailwind)
├── tsconfig.json            # Konfigurasi TypeScript
├── postcss.config.js        # Konfigurasi PostCSS
└── README.md               # Dokumentasi khusus frontend
```

### Penjelasan Folder Utama Frontend

| Folder | Fungsi |
|--------|--------|
| `src/routes/` | Setiap folder/file = satu halaman web. `+page.svelte` adalah halaman utamanya |
| `src/lib/components/` | Komponen UI yang bisa dipakai ulang (seperti "blok Lego" untuk menyusun halaman) |
| `src/lib/api/` | Kode yang menghubungkan frontend ke backend (mengirim dan menerima data) |
| `src/lib/stores/` | Tempat menyimpan data sementara yang bisa diakses dari mana saja di frontend |
| `static/` | File yang langsung disajikan tanpa diproses (gambar, ikon) |

---

## Docs

```
docs/
├── ARCHITECTURE.md       # Diagram dan penjelasan arsitektur sistem
├── CHANGELOG.md          # Riwayat perubahan per versi
├── DEMO_SCRIPT.md        # Skrip panduan untuk demo aplikasi
├── DEPLOYMENT_GUIDE.md   # Panduan deploy ke server
├── FILE_STRUCTURE.md     # File ini - penjelasan struktur project
└── TROUBLESHOOTING.md    # Solusi error-error umum
```

---

## File Template Kontrak

File-file di root folder yang merupakan sumber data kontrak PLN:

| File | Penjelasan |
|------|-----------|
| `20241007 PLN - BPR - Template Kontrak Biaya Plus Imbalan.docx` | Template kontrak dengan skema pembayaran biaya ditambah imbalan |
| `20241007 PLN - BPR - Template Kontrak Gabungan.docx` | Template kontrak yang menggabungkan beberapa skema |
| `20241007 PLN - BPR - Template Kontrak Kesepakatan Harga Satuan.docx` | Template kontrak dengan harga per unit yang disepakati |
| `20241007 PLN - BPR - Template Kontrak Lumsum.docx` | Template kontrak dengan harga tetap (lump sum) |
| `20241007 PLN - BPR - Template Kontrak Payung.docx` | Template kontrak payung (framework agreement) |
| `20241007 PLN - BPR - Template Kontrak Terima Jadi.docx` | Template kontrak turnkey (terima jadi/selesai) |
| `20241007 PLN - BPR - Template Kontrak Waktu Penugasan.docx` | Template kontrak berdasarkan waktu penugasan |

---

## Cara Kerja Singkat

1. **User** membuka web browser dan mengakses frontend
2. **Frontend** menampilkan dashboard template dan form input
3. User memilih template dan mengisi data kontrak
4. **Frontend** mengirim request ke **Backend** via API
5. **Backend** menggunakan **RAG pipeline** untuk mencari klausul yang relevan dari ChromaDB
6. **Backend** mengirim klausul + data user ke **LLM (AI)** untuk generate draft
7. Draft kontrak ditampilkan di **TipTap Editor** untuk review
8. User bisa edit, lalu **export ke DOCX** (file Word)
