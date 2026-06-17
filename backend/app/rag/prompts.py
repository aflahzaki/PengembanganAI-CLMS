"""Prompt templates for LLM interactions in CLMS.

Contains system prompts and few-shot examples for legal document drafting
using Llama-3 via LMStudio.
"""

# System prompt for legal drafting tasks
LEGAL_DRAFTING_SYSTEM_PROMPT = """Anda adalah asisten hukum AI yang ahli dalam menyusun dokumen kontrak 
pengadaan barang dan jasa di Indonesia. Anda harus:

1. Menggunakan bahasa hukum formal Indonesia yang sesuai standar.
2. Tidak menambahkan klausul atau ketentuan yang tidak ada dalam template.
3. Mengisi variabel/placeholder dengan data yang diberikan secara akurat.
4. Mempertahankan format dan struktur dokumen asli.
5. Tidak melakukan hallusinasi - hanya gunakan informasi dari template dan data yang diberikan.
6. Menghasilkan output dalam format HTML yang kompatibel dengan editor TipTap.

Anda bekerja berdasarkan template kontrak KHS (Kontrak Harga Satuan) untuk 
pengadaan material ketenagalistrikan PLN."""

# Prompt for assembling clauses into a complete contract
CLAUSE_ASSEMBLY_PROMPT = """Berdasarkan template klausul kontrak berikut, susun dokumen kontrak 
lengkap dengan mengisi semua variabel yang diberikan.

Template Klausul:
{clauses_text}

Data Variabel:
{variables_json}

Instruksi:
1. Susun semua klausul dalam urutan yang benar (sesuai nomor Pasal).
2. Isi semua placeholder [Nama Variabel] dengan data yang sesuai.
3. Jika ada variabel yang tidak memiliki data, biarkan dalam format [Nama Variabel].
4. Format output sebagai HTML dengan struktur:
   - Gunakan <h1> untuk judul kontrak
   - Gunakan <h2> untuk setiap Pasal
   - Gunakan <p> untuk paragraf isi
   - Gunakan <ol> dan <li> untuk daftar bernomor
   - Gunakan <strong> untuk penekanan teks penting

Output kontrak dalam format HTML:"""

# Prompt for filling specific variables in a clause
VARIABLE_FILLING_PROMPT = """Isi variabel-variabel berikut dalam klausul kontrak.

Klausul:
{clause_text}

Variabel yang harus diisi:
{variables_json}

Instruksi:
1. Ganti setiap [Nama Variabel] dengan nilai yang sesuai dari data.
2. Pastikan format dan tata bahasa tetap benar setelah pengisian.
3. Jangan ubah teks lain selain placeholder variabel.
4. Kembalikan klausul lengkap dengan variabel yang sudah terisi.

Hasil:"""

# Few-shot examples for consistent output
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

# HTML formatting instructions for TipTap compatibility
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
