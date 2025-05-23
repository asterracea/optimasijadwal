function toggleSubmenu() {
    const submenu = document.getElementById('submenu');
    submenu.classList.toggle('hidden');    
    submenu.classList.toggle('block');
}
function toggleSubmenudat() {
    const submenu = document.getElementById('submenudat');
    submenu.classList.toggle('hidden');    
    submenu.classList.toggle('block');
}
const btnHamburger = document.getElementById('btn-hamburger');
const sidebar = document.getElementById('sidebar');
const overlay = document.getElementById('overlay');

btnHamburger.addEventListener('click', () => {
  sidebar.classList.toggle('-translate-x-full');
  overlay.classList.toggle('hidden');
});

function closeSidebar() {
  sidebar.classList.add('-translate-x-full');
  overlay.classList.add('hidden');
}
