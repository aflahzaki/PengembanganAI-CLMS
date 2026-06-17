"""Prompt templates for LLM interactions in CLMS.

Contains system prompts, few-shot examples, and prompt construction utilities
for legal document drafting using Llama-3 via LMStudio.

All prompts are designed for KHS (Kontrak Harga Satuan) contract drafting
for Material Ketenagalistrikan PLN.
"""

# =============================================================================
# SYSTEM PROMPT - Strict Legal Drafter Role Definition
# =============================================================================

LEGAL_DRAFTING_SYSTEM_PROMPT = """Anda adalah Legal Drafter AI untuk dokumen kontrak pengadaan PLN.
Tugas Anda adalah menyusun dokumen kontrak KHS (Kontrak Harga Satuan) untuk Material Ketenagalistrikan.

== ATURAN KETAT ==

1. Anda HANYA boleh menggunakan teks dari template yang diberikan.
2. DILARANG menambahkan klausul, pasal, ayat, atau ketentuan baru yang tidak ada dalam template.
3. DILARANG membuat data fiktif, angka fiktif, nama fiktif, atau informasi apapun yang tidak diberikan.
4. Jangan parafrase teks template. Salin persis, hanya ganti placeholder.
5. Jika variabel tidak tersedia, tulis [VARIABEL_NAMA] apa adanya -- JANGAN isi dengan data fiktif.
6. Gunakan bahasa hukum Indonesia yang kaku, formal, presisi, tanpa kata-kata kasual.
7. Pertahankan penomoran dan urutan pasal persis seperti dalam template.

== STRUKTUR DOKUMEN ==

Dokumen kontrak HARUS mengikuti urutan berikut:
1. HEADER: Judul kontrak (KONTRAK HARGA SATUAN) dan nomor kontrak
2. PREAMBLE: Identitas para pihak (PIHAK PERTAMA dan PIHAK KEDUA)
3. BODY: Pasal-pasal kontrak sesuai urutan nomor (Pasal 1, Pasal 2, dst)
4. PENUTUP: Klausul penutup dan tanda tangan

== FORMAT OUTPUT ==

Output HARUS dalam format HTML yang valid untuk editor TipTap:
- <h1> untuk judul kontrak
- <h2> untuk setiap judul Pasal
- <h3> untuk sub-bagian dalam pasal
- <p> untuk paragraf isi
- <ol> dan <li> untuk daftar bernomor
- <ul> dan <li> untuk daftar tidak bernomor
- <strong> untuk penekanan teks penting
- Hindari inline styles

== ANTI-HALLUSINASI ==

INGAT: Anda BUKAN penulis kreatif. Anda adalah mesin penyusun dokumen yang HANYA menyalin
dan mengisi template. Jika ragu, biarkan placeholder apa adanya daripada mengarang isi."""

# =============================================================================
# CLAUSE ASSEMBLY PROMPT - Process clause by clause
# =============================================================================

CLAUSE_ASSEMBLY_PROMPT = """Susun dokumen kontrak dari template klausul berikut.
Proses SETIAP pasal satu per satu sesuai urutan yang diberikan.

== TEMPLATE KLAUSUL ==

{clauses_text}

== DATA VARIABEL ==

{variables_json}

== INSTRUKSI PENYUSUNAN (CLAUSE-BY-CLAUSE MODE) ==

1. Proses setiap pasal SATU PER SATU sesuai urutan nomor Pasal.
2. Untuk setiap pasal:
   a. Salin teks template PERSIS seperti aslinya.
   b. Ganti HANYA placeholder [Nama Variabel] yang datanya tersedia di atas.
   c. Jika variabel tidak tersedia, tulis [VARIABEL_NAMA] apa adanya -- JANGAN isi dengan data fiktif.
   d. JANGAN mengubah, menambah, atau menghapus kata-kata lain.
3. Bungkus setiap pasal dalam tag HTML sesuai struktur di bawah.

== CONTOH OUTPUT HTML ==

<h1>KONTRAK HARGA SATUAN</h1>
<h2>Pasal 1 - DEFINISI DAN INTERPRETASI</h2>
<p>Dalam Kontrak ini, istilah-istilah berikut memiliki arti sebagai berikut:</p>
<ol>
  <li><strong>"Kontrak"</strong> berarti perjanjian yang ditandatangani oleh Para Pihak;</li>
  <li><strong>"Pemberi Kerja"</strong> berarti PT PLN (Persero);</li>
</ol>
<h2>Pasal 2 - LINGKUP PEKERJAAN</h2>
<p>Penyedia wajib melaksanakan pekerjaan pengadaan material sesuai spesifikasi teknis.</p>

== CONTOH PENGISIAN VARIABEL ==

Template: "Yang bertanda tangan di bawah ini [Nama Pejabat] selaku [Jabatan] dari [Nama Perusahaan]"
Variabel: {{"Nama Pejabat": "Ir. Budi Santoso", "Jabatan": "General Manager"}}
Hasil: "Yang bertanda tangan di bawah ini Ir. Budi Santoso selaku General Manager dari [Nama Perusahaan]"

Perhatikan: [Nama Perusahaan] TETAP ditulis apa adanya karena datanya tidak tersedia.

== MULAI PENYUSUNAN DOKUMEN ==

Output kontrak lengkap dalam format HTML:"""

# =============================================================================
# SINGLE CLAUSE ASSEMBLY PROMPT - For clause-by-clause processing mode
# =============================================================================

SINGLE_CLAUSE_ASSEMBLY_PROMPT = """Proses SATU pasal berikut menjadi HTML.

== PASAL ==

{pasal_number}: {section_name}

{clause_text}

== DATA VARIABEL ==

{variables_json}

== INSTRUKSI ==

1. Salin teks pasal PERSIS seperti aslinya.
2. Ganti HANYA placeholder [Nama Variabel] yang datanya tersedia.
3. Jika variabel tidak tersedia, tulis [VARIABEL_NAMA] apa adanya -- JANGAN isi dengan data fiktif.
4. Format sebagai HTML dengan <h2> untuk judul pasal dan <p> untuk isi.
5. JANGAN tambahkan teks, klausul, atau informasi apapun di luar template.

== OUTPUT HTML ==
"""

# =============================================================================
# VARIABLE FILLING PROMPT
# =============================================================================

VARIABLE_FILLING_PROMPT = """Isi variabel-variabel berikut dalam klausul kontrak.

== KLAUSUL ==

{clause_text}

== VARIABEL YANG HARUS DIISI ==

{variables_json}

== INSTRUKSI KETAT ==

1. Ganti setiap [Nama Variabel] dengan nilai yang sesuai dari data di atas.
2. Jika variabel tidak tersedia dalam data, tulis [VARIABEL_NAMA] apa adanya -- JANGAN isi dengan data fiktif.
3. JANGAN ubah teks lain selain placeholder variabel.
4. JANGAN parafrase atau meringkas teks.
5. Kembalikan klausul lengkap dengan variabel yang sudah terisi.

== CONTOH ==

Input: "[Nama] selaku [Jabatan] dari [Perusahaan]"
Data: {{"Nama": "Ahmad", "Jabatan": "Direktur"}}
Output: "Ahmad selaku Direktur dari [Perusahaan]"

== HASIL ==
"""

# =============================================================================
# FEW-SHOT EXAMPLES
# =============================================================================

FEW_SHOT_CLAUSE_EXAMPLE = """
Contoh Input:
Klausul: "Yang bertanda tangan di bawah ini [Nama Pejabat] selaku [Jabatan]
dari [Nama Perusahaan], yang berkedudukan di [Alamat], selanjutnya disebut PIHAK PERTAMA."

Variabel: {
  "Nama Pejabat": "Ir. Budi Santoso",
  "Jabatan": "General Manager",
  "Nama Perusahaan": "PT PLN (Persero)",
  "Alamat": "Jl. Trunojoyo Blok M I/135, Jakarta 12160"
}

Contoh Output:
"Yang bertanda tangan di bawah ini Ir. Budi Santoso selaku General Manager
dari PT PLN (Persero), yang berkedudukan di Jl. Trunojoyo Blok M I/135, Jakarta 12160,
selanjutnya disebut PIHAK PERTAMA."
"""

# =============================================================================
# HTML FORMAT INSTRUCTIONS
# =============================================================================

HTML_FORMAT_INSTRUCTIONS = """Format HTML harus mengikuti struktur berikut untuk kompatibilitas
dengan editor TipTap:

<h1>KONTRAK HARGA SATUAN</h1>
<h2>Pasal 1 - DEFINISI DAN INTERPRETASI</h2>
<p>Dalam Kontrak ini, istilah-istilah berikut memiliki arti sebagai berikut:</p>
<ol>
  <li><strong>"Kontrak"</strong> berarti perjanjian yang ditandatangani...</li>
  <li><strong>"Para Pihak"</strong> berarti Pemberi Kerja dan Penyedia...</li>
</ol>
<p>Dokumen-dokumen berikut merupakan satu kesatuan dan bagian yang tidak terpisahkan
dari Kontrak ini:</p>

Catatan:
- Gunakan tag semantik HTML5
- Hindari inline styles
- Gunakan <br> untuk line breaks dalam paragraf
- Gunakan <table> untuk data tabular (jika ada)
"""


# =============================================================================
# PROMPT BUILDER FUNCTIONS
# =============================================================================


def build_drafting_prompt(
    clauses_text: str,
    variables_json: str,
) -> str:
    """Build a complete drafting prompt with system context.

    Args:
        clauses_text: Formatted text of all relevant clauses.
        variables_json: JSON string of variable mappings.

    Returns:
        Complete prompt string ready for LLM submission.
    """
    return CLAUSE_ASSEMBLY_PROMPT.format(
        clauses_text=clauses_text,
        variables_json=variables_json,
    )


def build_single_clause_prompt(
    pasal_number: str,
    section_name: str,
    clause_text: str,
    variables_json: str,
) -> str:
    """Build a prompt for processing a single clause.

    Used in clause-by-clause processing mode for more reliable output
    with smaller language models.

    Args:
        pasal_number: The pasal number (e.g., "Pasal 1").
        section_name: The section name (e.g., "DEFINISI DAN INTERPRETASI").
        clause_text: The clause template text.
        variables_json: JSON string of variable mappings.

    Returns:
        Complete prompt string for single clause processing.
    """
    return SINGLE_CLAUSE_ASSEMBLY_PROMPT.format(
        pasal_number=pasal_number,
        section_name=section_name,
        clause_text=clause_text,
        variables_json=variables_json,
    )


def build_variable_filling_prompt(
    clause_text: str,
    variables_json: str,
) -> str:
    """Build a variable-filling prompt for a single clause.

    Args:
        clause_text: The clause text with placeholders.
        variables_json: JSON string of variable values.

    Returns:
        Complete prompt string for variable filling.
    """
    return VARIABLE_FILLING_PROMPT.format(
        clause_text=clause_text,
        variables_json=variables_json,
    )
