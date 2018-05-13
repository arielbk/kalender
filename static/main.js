var sideNav = document.getElementById('side-nav');
var title = document.getElementById('main-title');

function openMenu() {
  sideNav.style.width = '320px';
  title.style.marginLeft = '354px';
}

function closeMenu() {
  sideNav.style.width = '0';
  title.style.marginLeft = '7.5%';
}

window.addEventListener('click', outsideClick);

function outsideClick (e) {
  if (e.target == sideNav) {
    sideNav.style.width = '0';
  }
}
