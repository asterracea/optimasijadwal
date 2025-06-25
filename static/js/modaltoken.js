
document.querySelector('[data-modal-target="modalToken"]').addEventListener('click', () => {
    document.getElementById('modalToken').classList.remove('hidden');
});

document.getElementById('cancelModal').addEventListener('click', () => {
    document.getElementById('modalToken').classList.add('hidden');
});

document.getElementById('formToken').addEventListener('submit', function(e) {
    e.preventDefault();

    const username = this.username.value;
    const password = this.password.value;
    const id_generate = document.getElementById('id_generate').value;

    if (!id_generate) {
        tampilkanModalPesan("Pilih ID Generate terlebih dahulu!");
        return;
    }

    // Ambil token ke API Node.js
    fetch('http://192.168.1.194:8081/optimasi/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    })
    .then(res => res.json())
    .then(data => {
        if (data.access_token) {
            // Kirim data ke backend Flask untuk diteruskan ke API tujuan
            fetch('/send-data', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    id_generate: id_generate,
                    token: data.access_token
                })
            })
            .then(res => res.json())
            .then(response => {
               if (response.message) {
                    document.getElementById('modalToken').classList.add('hidden');
                    tampilkanModalPesan(response.message || 'Tidak ada pesan dari server.');
                    
                }
            })
            .catch(() => tampilkanModalPesan('Gagal mengirim data ke server.'));
        } else {
             tampilkanModalPesan('Gagal mendapatkan token. Cek username/password!');
        }
    })
    .catch(() => tampilkanModalPesan('Gagal menghubungi server autentikasi.'));
});

