<script lang="ts">
  import { page } from '$app/state';
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-50">
  <div class="text-center p-8 max-w-md">
    <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-red-500" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
      </svg>
    </div>
    <h1 class="text-2xl font-bold text-gray-900 mb-2">Terjadi Kesalahan</h1>
    <p class="text-gray-600 mb-4">
      {page.error?.message || 'Halaman tidak dapat dimuat. Silakan coba lagi.'}
    </p>
    <p class="text-sm text-gray-400 mb-6">Kode: {page.status}</p>
    <div class="flex gap-3 justify-center">
      <a href="/" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
        Kembali ke Dashboard
      </a>
      <button onclick={() => window.location.reload()} class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors">
        Muat Ulang
      </button>
    </div>
  </div>
</div>
