
  const btnEdit = document.getElementById('btn-edit');
  const modal = document.getElementById('editmodal');
  const btnCancel = document.getElementById('btn-cancel');
  const editForm = document.getElementById('editForm');
  const inputNama = document.getElementById('editNama');
  const inputNamaUtama = document.getElementById('nama');

  // Open modal
  btnEdit.addEventListener('click', () => {
    modal.classList.remove('hidden');
    inputNama.focus();
  });

  // Close modal on cancel
  btnCancel.addEventListener('click', () => {
    modal.classList.add('hidden');
  });

  // Close modal when clicking outside modal content
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.add('hidden');
    }
  });

  // Handle form submit
  
  editForm.addEventListener('submit', (e) => {
  
    // Ambil nilai nama baru
    const newName = inputNama.value.trim();
    if (newName === '') {
      alert('Nama tidak boleh kosong');
      return;
    }

    // Update input nama di halaman utama
    inputNamaUtama.value = newName;

    // Tutup modal
    modal.classList.add('hidden');

    // TODO: Kirim data ke backend dengan AJAX/fetch kalau perlu
    console.log('Nama baru:', newName);
  });
