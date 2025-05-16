// static/js/modal.js

function showModal(message) {
  document.getElementById('modalMessage').innerText = message;
  document.getElementById('notifModal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('notifModal').classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', () => {
  const modalMessageElement = document.getElementById('modalMessage');
  if (modalMessageElement && modalMessageElement.dataset.message) {
    showModal(modalMessageElement.dataset.message);
  }
});
