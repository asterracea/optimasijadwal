function updateFileName() {
    const input = document.getElementById("file-upload");
    const fileNameDisplay = document.getElementById("file-name");

    if (input.files.length > 0) {
        fileNameDisplay.innerHTML = `<i class="fa-solid fa-file"></i> <span class="text-sm font-bold text-gray-600">${input.files[0].name}</span>`;
    } else {
        fileNameDisplay.innerHTML = `<i class="fa-solid fa-cloud-arrow-up"></i> <span class="text-sm font-bold text-gray-600">Unggah Berkas</span>`;
    }
}