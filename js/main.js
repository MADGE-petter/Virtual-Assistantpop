/* ============================================
   POP Assistant — Official Website JS
   Animations & Interactions
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  createStars();
  initMouseLight();
  initNavbar();
  initMobileMenu();
  initRevealAnimations();
  initSmoothScroll();
  initElectricEffects();
  initLogoAnimation();
  initHaloLogoAnimation();
});

// ---------- Stars ----------
function createStars() {
  const container = document.getElementById('starfield');
  if (!container) return;
  const count = 120;
  const frag = document.createDocumentFragment();
  for (let i = 0; i < count; i++) {
    const s = document.createElement('div');
    s.className = 'star';
    s.style.cssText = `left:${Math.random()*100}%;top:${Math.random()*100}%;--d:${2+Math.random()*4}s;--dl:${Math.random()*5}s;width:${1+Math.random()*2}px;height:${1+Math.random()*2}px`;
    frag.appendChild(s);
  }
  container.appendChild(frag);
}

// ---------- Mouse Light ----------
function initMouseLight() {
  const light = document.getElementById('mouse-light');
  if (!light) return;
  let mx = -500, my = -500, cx = -500, cy = -500;
  document.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; });
  document.addEventListener('mouseleave', () => light.style.opacity = '0');
  document.addEventListener('mouseenter', () => light.style.opacity = '1');
  function anim() {
    cx += (mx - cx) * 0.07;
    cy += (my - cy) * 0.07;
    light.style.left = cx + 'px';
    light.style.top = cy + 'px';
    requestAnimationFrame(anim);
  }
  anim();
}

// ---------- Navbar ----------
function initNavbar() {
  const nav = document.getElementById('navbar');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 50);
  });
}

// ---------- Mobile Menu ----------
function initMobileMenu() {
  const toggle = document.getElementById('nav-toggle');
  const links = document.getElementById('nav-links');
  if (!toggle || !links) return;
  toggle.addEventListener('click', () => links.classList.toggle('open'));
  links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => links.classList.remove('open')));
}

// ---------- Reveal on Scroll ----------
function initRevealAnimations() {
  const reveals = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  reveals.forEach(el => observer.observe(el));
}

// ---------- Smooth Scroll ----------
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', e => {
      e.preventDefault();
      const href = anchor.getAttribute('href');
      if (!href || href === '#') return;
      const target = document.querySelector(href);
      if (target) target.scrollIntoView({ behavior: 'smooth' });
    });
  });
}

// ---------- Electric Effects ----------
function initElectricEffects() {
  const overlay = document.getElementById('electric-overlay');
  if (!overlay) return;

  function createFlash() {
    const flash = document.createElement('div');
    flash.className = 'electric-flash';
    
    // Random position and rotation
    const x = Math.random() * window.innerWidth;
    const y = Math.random() * window.innerHeight;
    const rot = Math.random() * 360;
    
    flash.style.left = x + 'px';
    flash.style.top = y + 'px';
    flash.style.transform = `rotate(${rot}deg)`;
    
    document.body.appendChild(flash);
    
    // Animation sequence
    setTimeout(() => {
      flash.style.opacity = '0.8';
      flash.style.transition = 'opacity 0.1s ease';
    }, 10);
    
    setTimeout(() => {
      flash.style.opacity = '0';
      flash.style.transition = 'opacity 0.4s ease';
      setTimeout(() => flash.remove(), 500);
    }, 150);
  }

  // Randomly trigger flashes
  function loop() {
    const delay = 3000 + Math.random() * 7000;
    setTimeout(() => {
      createFlash();
      loop();
    }, delay);
  }
  loop();
}

// ---------- Logo Animation ----------
function initLogoAnimation() {
  const logoContainer = document.querySelector('.hero-core .logo-container');
  if (!logoContainer) return;

  const logoSvg = logoContainer.querySelector('.logo-svg');
  const logoHalo = logoContainer.querySelector('.logo-halo');

  if (logoSvg) {
    logoSvg.style.animation = 'corePulse 3s ease-in-out infinite';
  }

  if (logoHalo) {
    logoHalo.style.animation = 'haloRotate 20s linear infinite';
  }

  const logoRing = logoContainer.querySelector('.logo-ring');
  if (logoRing) {
    logoRing.style.animation = 'ringDraw 4s ease-in-out infinite';
  }

  const logoIcon = logoContainer.querySelector('.logo-icon');
  if (logoIcon) {
    logoIcon.style.animation = 'iconGlow 2.5s ease-in-out infinite';
  }

  const logoDot = logoContainer.querySelector('.logo-dot');
  if (logoDot) { logoDot.style.animation = 'dotPulse 2s ease-in-out infinite'; }
}

// ---------- Halo Logo Animation ----------
function initHaloLogoAnimation() {
    const lightningContainer = document.getElementById('lightningContainer');
    if (!lightningContainer) return;

    function createLightning() {
        const lightning = document.createElement('div');
        lightning.className = 'lightning';

        const angle = Math.random() * Math.PI * 2;
        const distance = 80 + Math.random() * 70;
        const x = Math.cos(angle) * distance + 125;
        const y = Math.sin(angle) * distance + 125;

        const size = 10 + Math.random() * 40;
        const rotation = angle * 180 / Math.PI + (Math.random() * 20 - 10);

        lightning.style.left = x + 'px';
        lightning.style.top = y + 'px';
        lightning.style.width = size + 'px';
        lightning.style.height = '2px';
        lightning.style.transform = `rotate(${rotation}deg)`;

        lightningContainer.appendChild(lightning);

        setTimeout(() => {
            lightning.remove();
        }, 300);
    }

    function lightningLoop() {
        createLightning();
        const delay = 50 + Math.random() * 150;
        setTimeout(lightningLoop, delay);

        if (Math.random() > 0.7) {
            setTimeout(createLightning, 10);
            if (Math.random() > 0.5) {
                setTimeout(createLightning, 20);
            }
        }
    }

    lightningLoop();
}