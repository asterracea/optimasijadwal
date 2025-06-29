const idSelect = document.getElementById('id_generate');
const hapusButton = document.querySelector('[data-modal-target="modalHapusHasil"]');
const hapusInput = document.getElementById('hapus_id_generate');
const modal = document.getElementById('modalHapusHasil');
const pesanPilihId = document.getElementById('pesanPilihId');

hapusButton.addEventListener('click', () => {
    const selectedId = idSelect.value;
     if (!cekIdGenerate()) return;
    hapusInput.value = selectedId;
    modal.classList.remove('hidden');
});

function tutupModal() {
    modal.classList.add('hidden');
}
