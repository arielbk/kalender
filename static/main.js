var sideNav = document.getElementById('side-nav');

function openMenu() {
  sideNav.style.width = '320px';
}

function closeMenu() {
  sideNav.style.width = '0';
}

window.addEventListener('click', outsideClick);

function outsideClick (e) {
  if (e.target == sideNav) {
    sideNav.style.width = '0';
  }
}
