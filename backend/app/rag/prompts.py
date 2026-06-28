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

Output HARUS dalam format HTML yang valid untuk editor TipTap dengan format rapi dan profesional:
- <h1 style="text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 24px;"> untuk judul kontrak
- <h2 style="font-size: 14px; font-weight: bold; margin-top: 24px; margin-bottom: 12px;"> untuk setiap judul Pasal
- <h3> untuk sub-bagian dalam pasal
- <p style="margin-bottom: 12px; line-height: 1.6; text-align: justify;"> untuk paragraf isi
- <ol type="1"> untuk daftar bernomor utama (1. 2. 3.)
- <ol type="a" style="margin-left: 20px;"> untuk sub-item huruf (a. b. c.)
- <ol type="1" style="list-style-type: decimal; margin-left: 40px;"> untuk sub-sub-item angka (1) 2) 3))
- <li style="margin-bottom: 8px; line-height: 1.6; text-align: justify;"> untuk item list
- <hr class="pasal-separator" style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;" /> sebagai pemisah antar Pasal
- <strong> untuk penekanan teks penting
- Bungkus seluruh dokumen dalam <div class="contract-document">

== ATURAN FORMAT KERAPIAN ==

1. WAJIB ada pemisah <hr> antara setiap Pasal section.
2. Setiap paragraf <p> HARUS memiliki margin-bottom: 12px dan line-height: 1.6.
3. Text di paragraf HARUS rata kiri-kanan (text-align: justify).
4. Penomoran HARUS terstruktur: nomor utama (1. 2. 3.), sub-item huruf (a. b. c.), sub-sub-item (1) 2) 3)).
5. Sub-item HARUS di-indent dengan margin-left yang sesuai.
6. Judul kontrak HARUS di-center.
7. Judul Pasal HARUS memiliki margin-top: 24px untuk jarak yang jelas dari section sebelumnya.

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

SINGLE_CLAUSE_ASSEMBLY_PROMPT = """Proses SATU pasal berikut menjadi HTML yang rapi dan profesional.

== PASAL ==

{pasal_number}: {section_name}

{clause_text}

== DATA VARIABEL ==

{variables_json}

== INSTRUKSI ==

1. Salin teks pasal PERSIS seperti aslinya.
2. Ganti HANYA placeholder [Nama Variabel] yang datanya tersedia.
3. Jika variabel tidak tersedia, tulis [VARIABEL_NAMA] apa adanya -- JANGAN isi dengan data fiktif.
4. Format sebagai HTML dengan:
   - <h2 style="font-size: 14px; font-weight: bold; margin-top: 24px; margin-bottom: 12px;"> untuk judul pasal
   - <p style="margin-bottom: 12px; line-height: 1.6; text-align: justify;"> untuk isi paragraf
   - <ol type="1"> untuk daftar bernomor utama
   - <ol type="a" style="margin-left: 20px;"> untuk sub-item huruf
   - <li style="margin-bottom: 8px; line-height: 1.6; text-align: justify;"> untuk item list
5. JANGAN tambahkan teks, klausul, atau informasi apapun di luar template.

== OUTPUT HTML ==
"""

# =============================================================================
# FULL DOCUMENT ASSEMBLY PROMPT - Send all clauses at once (for fast cloud APIs)
# =============================================================================

FULL_DOCUMENT_ASSEMBLY_PROMPT = """Susun SELURUH dokumen kontrak dari template klausul berikut dalam SATU kali proses.
Anda menerima SEMUA pasal sekaligus dan harus menghasilkan dokumen kontrak lengkap dengan format rapi dan profesional.

== SEMUA TEMPLATE KLAUSUL ==

{clauses_text}

== DATA VARIABEL ==

{variables_json}

== INSTRUKSI PENYUSUNAN (FULL DOCUMENT MODE) ==

1. Proses SEMUA pasal sekaligus dan hasilkan dokumen kontrak LENGKAP.
2. Untuk setiap pasal:
   a. Salin teks template PERSIS seperti aslinya.
   b. Ganti HANYA placeholder [Nama Variabel] yang datanya tersedia di atas.
   c. Jika variabel tidak tersedia, tulis [VARIABEL_NAMA] apa adanya -- JANGAN isi dengan data fiktif.
   d. JANGAN mengubah, menambah, atau menghapus kata-kata lain.
3. Bungkus output dalam tag HTML yang valid untuk editor TipTap.
4. Pastikan SEMUA pasal ada dalam output -- jangan ada yang terlewat.

== FORMAT OUTPUT HTML (WAJIB DIIKUTI) ==

- Bungkus seluruh dokumen dalam <div class="contract-document">
- <h1 style="text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 24px;"> untuk judul kontrak
- <h2 style="font-size: 14px; font-weight: bold; margin-top: 24px; margin-bottom: 12px;"> untuk judul setiap Pasal
- <p style="margin-bottom: 12px; line-height: 1.6; text-align: justify;"> untuk paragraf isi
- <ol type="1"> dan <li style="margin-bottom: 8px; line-height: 1.6; text-align: justify;"> untuk daftar bernomor utama (1. 2. 3.)
- <ol type="a" style="margin-left: 20px;"> untuk sub-item huruf (a. b. c.)
- <ol type="1" style="list-style-type: decimal; margin-left: 40px;"> untuk sub-sub-item angka (1) 2) 3))
- <hr class="pasal-separator" style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;" /> sebagai PEMISAH antara setiap Pasal
- <strong> untuk penekanan teks penting

== ATURAN KERAPIAN ==

1. WAJIB ada <hr class="pasal-separator"> antara setiap Pasal.
2. Setiap <p> HARUS memiliki inline style margin-bottom: 12px dan line-height: 1.6.
3. Text paragraf HARUS rata kiri-kanan (text-align: justify).
4. Sub-item (a. b. c.) HARUS nested di dalam parent <li> dengan margin-left.
5. Judul kontrak HARUS centered.

== CONTOH FORMAT ==

<div class="contract-document">
<h1 style="text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 24px;">KONTRAK HARGA SATUAN</h1>
<h2 style="font-size: 14px; font-weight: bold; margin-top: 24px; margin-bottom: 12px;">Pasal 1 - DEFINISI DAN INTERPRETASI</h2>
<p style="margin-bottom: 12px; line-height: 1.6; text-align: justify;">Dalam Kontrak ini, istilah-istilah berikut memiliki arti sebagai berikut:</p>
<ol type="1">
  <li style="margin-bottom: 8px; line-height: 1.6; text-align: justify;"><strong>"Kontrak"</strong> berarti perjanjian yang ditandatangani oleh Para Pihak;</li>
</ol>
<hr class="pasal-separator" style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;" />
<h2 style="font-size: 14px; font-weight: bold; margin-top: 24px; margin-bottom: 12px;">Pasal 2 - LINGKUP PEKERJAAN</h2>
<p style="margin-bottom: 12px; line-height: 1.6; text-align: justify;">Penyedia wajib melaksanakan pekerjaan pengadaan material sesuai spesifikasi teknis.</p>
</div>

== MULAI PENYUSUNAN DOKUMEN LENGKAP ==

Output kontrak lengkap dalam format HTML:"""

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
dengan editor TipTap dan menghasilkan dokumen yang rapi dan profesional:

<div class="contract-document">
<h1 style="text-align: center; font-size: 18px; font-weight: bold; margin-bottom: 24px;">KONTRAK HARGA SATUAN</h1>
<h2 style="font-size: 14px; font-weight: bold; margin-top: 24px; margin-bottom: 12px;">Pasal 1 - DEFINISI DAN INTERPRETASI</h2>
<p style="margin-bottom: 12px; line-height: 1.6; text-align: justify;">Dalam Kontrak ini, istilah-istilah berikut memiliki arti sebagai berikut:</p>
<ol type="1">
  <li style="margin-bottom: 8px; line-height: 1.6; text-align: justify;"><strong>"Kontrak"</strong> berarti perjanjian yang ditandatangani...</li>
  <li style="margin-bottom: 8px; line-height: 1.6; text-align: justify;"><strong>"Para Pihak"</strong> berarti Pemberi Kerja dan Penyedia...
    <ol type="a" style="margin-left: 20px;">
      <li style="margin-bottom: 4px; line-height: 1.6;">Sub item pertama;</li>
      <li style="margin-bottom: 4px; line-height: 1.6;">Sub item kedua;</li>
    </ol>
  </li>
</ol>
<hr class="pasal-separator" style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;" />
<h2 style="font-size: 14px; font-weight: bold; margin-top: 24px; margin-bottom: 12px;">Pasal 2 - LINGKUP PEKERJAAN</h2>
<p style="margin-bottom: 12px; line-height: 1.6; text-align: justify;">Dokumen-dokumen berikut merupakan satu kesatuan...</p>
</div>

Catatan:
- Gunakan tag semantik HTML5 dengan inline styles untuk spacing
- Gunakan <hr class="pasal-separator"> sebagai pemisah antar Pasal
- Gunakan <ol type="1"> untuk penomoran utama, <ol type="a"> untuk sub-item
- Setiap <p> harus memiliki margin-bottom: 12px, line-height: 1.6, text-align: justify
- Judul kontrak centered, judul pasal bold dengan margin-top: 24px
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


def build_full_document_prompt(
    clauses: list,
    variables: dict,
) -> str:
    """Build a full document assembly prompt with all clauses at once.

    Optimized for fast cloud APIs (e.g., DeepSeek) that can handle
    large context and produce the entire document in one call.

    Args:
        clauses: List of clause dictionaries with metadata and document text.
        variables: Variable name to value mapping.

    Returns:
        Complete prompt string for full document generation.
    """
    import json

    # Format all clauses into a single text block
    parts = []
    for clause in clauses:
        meta = clause.get("metadata", {})
        pasal = meta.get("pasal_number", "")
        section = meta.get("section_name", "")
        doc = clause.get("document", "")

        header = f"--- {pasal}: {section} ---" if pasal else f"--- {section} ---"
        parts.append(f"{header}\n{doc}")

    clauses_text = "\n\n".join(parts)
    variables_json = json.dumps(variables, ensure_ascii=False, indent=2)

    return FULL_DOCUMENT_ASSEMBLY_PROMPT.format(
        clauses_text=clauses_text,
        variables_json=variables_json,
    )
