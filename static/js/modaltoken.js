// Ambil semua elemen yang dibutuhkan
const pilihId = document.getElementById('id_generate');
const bukaModalToken = document.querySelector('[data-modal-target="modalToken"]');
const modalToken = document.getElementById('modalToken');
const notifIdSelected = document.getElementById('pesanPilihId');
const cancelModalToken = document.getElementById('cancelModalToken');
const formToken = document.getElementById('formToken');

// Tombol "Kirim" ditekan
bukaModalToken.addEventListener('click', () => {
    const selectedId = pilihId.value;

    // Cek apakah ID Generate dipilih
    if (!selectedId) {
        notifIdSelected.classList.remove('hidden');
        setTimeout(() => notifIdSelected.classList.add('hidden'), 5000);
        return;
    }

    // Jika dipilih, tampilkan modal token
    modalToken.classList.remove('hidden');
});

// Tombol "Batal" dalam modal token ditekan
cancelModalToken.addEventListener('click', () => {
    modalToken.classList.add('hidden');
});

// Submit form token
formToken.addEventListener('submit', function (e) {
    e.preventDefault();

    const username = this.username.value.trim();
    const password = this.password.value.trim();
    const id_generate = pilihId.value;

    // Validasi input username/password
    if (!username || !password) {
        tampilkanModalPesan('Username dan Password tidak boleh kosong!');
        return;
    }

    // Ambil token dari API Node.js
    fetch('http://192.168.1.225:8081/optimasi/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    })
    .then(res => res.json())
    .then(data => {
        if (data.access_token) {
            // Kirim ke server Flask
            fetch('/api/send-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id_generate: id_generate,
                    token: data.access_token
                })
            })
            .then(res => res.json())
            .then(response => {
                if (response.message) {
                    modalToken.classList.add('hidden');
                    tampilkanModalPesan(response.message);
                } else {
                    tampilkanModalPesan('Server tidak memberikan pesan.');
                }
            })
            .catch(() => tampilkanModalPesan('Gagal mengirim data ke server Flask.'));
        } else {
            const pesanError = data.message
            tampilkanModalPesan(pesanError);
        }
    })
    .catch(() => tampilkanModalPesan('Gagal menghubungi server autentikasi.'));
});

