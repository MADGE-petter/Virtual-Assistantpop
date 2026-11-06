/* ============================================
   POP Assistant — Official Interactive Script
   High-performance animations & interactions
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  createStars();
  initMouseLight();
  initNavbar();
  initMobileMenu();
  initRevealAnimations();
  initSmoothScroll();
  initElectricEffects();
  initHaloLogoAnimation();
});

// ---------- Cosmic Starfield Generator ----------
function createStars() {
  const container = document.getElementById('starfield');
  if (!container) return;
  const count = 100;
  const frag = document.createDocumentFragment();
  for (let i = 0; i < count; i++) {
    const s = document.createElement('div');
    s.className = 'star';
    const dur = 2.5 + Math.random() * 4.5;
    const delay = Math.random() * 5;
    const size = 1.2 + Math.random() * 2.2;
    s.style.cssText = `left:${Math.random() * 100}%; top:${Math.random() * 100}%; --d:${dur}s; animation-delay:${delay}s; width:${size}px; height:${size}px;`;
    frag.appendChild(s);
  }
  container.appendChild(frag);
}

// ---------- Ambient Mouse Glow Light ----------
function initMouseLight() {
  const light = document.getElementById('mouse-light');
  if (!light) return;
  let mx = -500, my = -500, cx = -500, cy = -500;
  document.addEventListener('mousemove', e => { 
    mx = e.clientX; 
    my = e.clientY; 
  });
  document.addEventListener('mouseleave', () => { light.style.opacity = '0'; });
  document.addEventListener('mouseenter', () => { light.style.opacity = '1'; });
  
  function anim() {
    cx += (mx - cx) * 0.08;
    cy += (my - cy) * 0.08;
    light.style.left = cx + 'px';
    light.style.top = cy + 'px';
    requestAnimationFrame(anim);
  }
  anim();
}

// ---------- Header Navbar On Scroll ----------
function initNavbar() {
  const nav = document.getElementById('navbar');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 40);
  }, { passive: true });
}

// ---------- Mobile Hamburger Menu ----------
function initMobileMenu() {
  const toggle = document.getElementById('nav-toggle');
  const links = document.getElementById('nav-links');
  if (!toggle || !links) return;
  toggle.addEventListener('click', () => links.classList.toggle('open'));
  links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => links.classList.remove('open')));
}

// ---------- Scroll Reveal Intersection Observer ----------
function initRevealAnimations() {
  const reveals = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -30px 0px' });
  reveals.forEach(el => observer.observe(el));
}

// ---------- Smooth Anchor Scrolling ----------
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', e => {
      const href = anchor.getAttribute('href');
      if (!href || href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
}

// ---------- Cyber Electric Flash FX ----------
function initElectricEffects() {
  const overlay = document.getElementById('electric-overlay');
  if (!overlay) return;

  function createFlash() {
    const flash = document.createElement('div');
    flash.className = 'electric-flash';
    const x = Math.random() * window.innerWidth;
    const y = Math.random() * window.innerHeight;
    const rot = Math.random() * 360;
    
    flash.style.left = x + 'px';
    flash.style.top = y + 'px';
    flash.style.transform = `rotate(${rot}deg)`;
    document.body.appendChild(flash);
    
    setTimeout(() => {
      flash.style.opacity = '0.75';
      flash.style.transition = 'opacity 0.1s ease';
    }, 10);
    
    setTimeout(() => {
      flash.style.opacity = '0';
      flash.style.transition = 'opacity 0.35s ease';
      setTimeout(() => flash.remove(), 400);
    }, 160);
  }

  function loop() {
    const delay = 3500 + Math.random() * 6000;
    setTimeout(() => {
      createFlash();
      loop();
    }, delay);
  }
  loop();
}

// ---------- Halo Core Lightning Arcs ----------
function initHaloLogoAnimation() {
  const lightningContainer = document.getElementById('lightningContainer');
  if (!lightningContainer) return;

  function createLightning() {
    const lightning = document.createElement('div');
    lightning.className = 'lightning';

    const angle = Math.random() * Math.PI * 2;
    const distance = 75 + Math.random() * 65;
    const x = Math.cos(angle) * distance + 125;
    const y = Math.sin(angle) * distance + 125;

    const size = 12 + Math.random() * 36;
    const rotation = (angle * 180 / Math.PI) + (Math.random() * 20 - 10);

    lightning.style.left = x + 'px';
    lightning.style.top = y + 'px';
    lightning.style.width = size + 'px';
    lightning.style.height = '2px';
    lightning.style.transform = `rotate(${rotation}deg)`;

    lightningContainer.appendChild(lightning);

    setTimeout(() => {
      lightning.remove();
    }, 280);
  }

  function lightningLoop() {
    createLightning();
    const delay = 60 + Math.random() * 140;
    setTimeout(lightningLoop, delay);

    if (Math.random() > 0.65) {
      setTimeout(createLightning, 15);
      if (Math.random() > 0.5) {
        setTimeout(createLightning, 30);
      }
    }
  }

  lightningLoop();
}
