  const logoutBtn = document.getElementById('btn-logout');
  const logoutModal = document.getElementById('logout-modal');
  const cancelBtn = document.getElementById('logout-cancel');

  // Tampilkan modal ketika tombol logout ditekan
  logoutBtn.addEventListener('click', () => {
    logoutModal.classList.remove('hidden');
  });

  // Tutup modal saat klik tombol batal
  cancelBtn.addEventListener('click', () => {
    logoutModal.classList.add('hidden');
  });

  // Opsional: tutup modal kalau klik di luar modal content
  logoutModal.addEventListener('click', (e) => {
    if (e.target === logoutModal) {
      logoutModal.classList.add('hidden');
    }
  });
