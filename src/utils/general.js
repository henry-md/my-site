import { MOBILE_NAV_BREAKPOINT_PX } from '../constants.ts';

function toggle() {
  const nav = document.getElementById('myTopnav');
  nav.classList.toggle('responsive');
}

function smoothScroll(event) {
  event.preventDefault();

  const targetId = event.currentTarget.getAttribute('href');
  if (!targetId) return;

  const target = document.querySelector(targetId);
  if (target) {
    target.scrollIntoView({ behavior: 'smooth' });
  }

  const nav = document.getElementById('myTopnav');
  if (window.innerWidth <= MOBILE_NAV_BREAKPOINT_PX && nav.classList.contains('responsive')) {
    nav.classList.remove('responsive');
  }
}

export { toggle, smoothScroll };
