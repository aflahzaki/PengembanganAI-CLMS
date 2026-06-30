# Script Demo CLMS - 5 Menit

## Persiapan
- Backend berjalan di port 8000
- Frontend berjalan di port 5173
- Groq API key sudah dikonfigurasi (opsional untuk Mode 2)

## Demo Flow

### Menit 1: Dashboard & Template Library
1. Buka browser → localhost:5173
2. Tunjukkan onboarding screen (first time)
3. Dashboard: "Lihat, ada 8 template kontrak resmi PLN yang sudah siap pakai"
4. Tunjukkan health status (hijau = backend connected)

### Menit 2: Mode 1 - Dari Template
1. Klik "Gunakan" pada template "Kontrak Harga Satuan"
2. "Template langsung dimuat di editor dengan format rapi"
3. Tunjukkan variabel yang ter-highlight kuning
4. "User tinggal klik dan ganti variabel sesuai kebutuhan"

### Menit 3: Fitur Editor
1. Tunjukkan toolbar (Bold, Italic, Heading, List)
2. Tunjukkan word count di footer ("± X halaman A4")
3. Klik tombol "Copy" → "Tersalin!"
4. Tunjukkan dark mode toggle

### Menit 4: Export & Download
1. Klik "Export DOCX" → file ter-download
2. Buka file di Microsoft Word → tunjukkan format rapi
3. Klik "Download Info" → tunjukkan metadata JSON

### Menit 5: Mode 2 - AI Generate (Jika API Key Tersedia)
1. Pindah ke tab "Generate Baru (AI)"
2. Isi deskripsi: "Buat kontrak pengadaan kabel listrik 150kV untuk wilayah Jawa Barat"
3. Isi variabel dasar
4. Klik "Generate dengan AI"
5. "AI menyusun dokumen berdasarkan deskripsi dan pola kontrak PLN"

## Penutup
- "Sistem ini bisa di-deploy ke server PLN menggunakan Docker"
- "Template bisa ditambah/dihapus sesuai kebutuhan"
- "Gratis, cepat, dan data tetap aman di server internal"
