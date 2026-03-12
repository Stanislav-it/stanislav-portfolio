const menuButton = document.querySelector('.menu-button');
const mobileMenu = document.querySelector('#mobile-menu');
const menuClose = document.querySelector('.menu-close');
const mobileLinks = mobileMenu ? mobileMenu.querySelectorAll('a:not([data-contact-open])') : [];
const contactDrawer = document.querySelector('#contact-drawer');
const contactOpeners = Array.from(document.querySelectorAll('[data-contact-open]'));
const contactClosers = contactDrawer ? contactDrawer.querySelectorAll('[data-contact-close]') : [];

function syncOverlayState() {
  const isMenuOpen = mobileMenu && !mobileMenu.hidden;
  const isContactOpen = contactDrawer && !contactDrawer.hidden;
  document.body.classList.toggle('is-overlay-open', Boolean(isMenuOpen || isContactOpen));
}

function closeMenu() {
  if (!mobileMenu || !menuButton) return;
  mobileMenu.hidden = true;
  menuButton.setAttribute('aria-expanded', 'false');
  syncOverlayState();
}

function openMenu() {
  if (!mobileMenu || !menuButton) return;
  if (contactDrawer && !contactDrawer.hidden) {
    closeContactDrawer();
  }
  mobileMenu.hidden = false;
  menuButton.setAttribute('aria-expanded', 'true');
  syncOverlayState();
}

function closeContactDrawer() {
  if (!contactDrawer) return;
  contactDrawer.hidden = true;
  syncOverlayState();
}

function openContactDrawer() {
  if (!contactDrawer) return;
  closeMenu();
  contactDrawer.hidden = false;
  syncOverlayState();
}

if (menuButton && mobileMenu) {
  menuButton.addEventListener('click', () => {
    const isOpen = menuButton.getAttribute('aria-expanded') === 'true';
    isOpen ? closeMenu() : openMenu();
  });
}

if (menuClose) menuClose.addEventListener('click', closeMenu);
mobileLinks.forEach((link) => link.addEventListener('click', closeMenu));
if (mobileMenu) {
  mobileMenu.addEventListener('click', (event) => {
    if (event.target === mobileMenu) closeMenu();
  });
}

contactOpeners.forEach((trigger) => {
  trigger.addEventListener('click', (event) => {
    event.preventDefault();
    openContactDrawer();
  });
});
contactClosers.forEach((trigger) => trigger.addEventListener('click', closeContactDrawer));

document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  closeMenu();
  closeContactDrawer();
});

if (contactDrawer && contactDrawer.dataset.autoOpen === 'true') {
  window.addEventListener('load', openContactDrawer, { once: true });
}

const revealItems = Array.from(document.querySelectorAll('.reveal'));

function showRevealItem(item) {
  item.classList.add('is-visible');
}

let revealObserver = null;

if ('IntersectionObserver' in window) {
  revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        showRevealItem(entry.target);
        revealObserver.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.01,
    rootMargin: '0px 0px -4% 0px',
  });

  revealItems.forEach((item) => revealObserver.observe(item));

  window.addEventListener('load', () => {
    revealItems.forEach((item) => {
      const rect = item.getBoundingClientRect();
      const visibleHeight = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
      if (visibleHeight > 0) {
        showRevealItem(item);
        revealObserver.unobserve(item);
      }
    });
  }, { once: true });
} else {
  revealItems.forEach(showRevealItem);
}

const introScreen = document.querySelector('.intro-screen');
const typeTargets = Array.from(document.querySelectorAll('.type-target'));
let introFinished = false;

function typeLine(target) {
  const text = target.dataset.fullText || target.textContent.trim();
  target.dataset.fullText = text;
  target.textContent = '';
  target.classList.add('is-typing');

  const cursor = document.createElement('span');
  cursor.className = 'type-cursor';
  target.appendChild(cursor);

  let index = 0;
  const delay = Number(target.dataset.typeDelay || 20);
  const startDelay = Number(target.dataset.typeStart || 0);

  window.setTimeout(() => {
    const timer = window.setInterval(() => {
      if (index >= text.length) {
        window.clearInterval(timer);
        cursor.remove();
        target.classList.remove('is-typing');
        target.classList.add('is-typed');
        return;
      }

      cursor.insertAdjacentText('beforebegin', text[index]);
      index += 1;
    }, delay);
  }, startDelay);
}

function startHeroText() {
  typeTargets.forEach((target) => typeLine(target));
}

function finishIntro() {
  if (introFinished) return;
  introFinished = true;
  document.body.classList.remove('is-intro-active');
  document.body.classList.add('is-ready');

  if (introScreen) {
    introScreen.classList.add('is-hidden');
    window.setTimeout(() => introScreen.remove(), 950);
  }

  startHeroText();
  startHeroLogoRotation();
}

if (introScreen) {
  window.addEventListener('load', () => {
    window.setTimeout(finishIntro, 1800);
  }, { once: true });

  window.setTimeout(finishIntro, 3200);
} else {
  document.body.classList.add('is-ready');
  startHeroText();
  window.addEventListener('load', startHeroLogoRotation, { once: true });
}

const heroVideos = Array.from(document.querySelectorAll('.hero-cycle-video'));

function playVideo(video) {
  const promise = video.play();
  if (promise && typeof promise.catch === 'function') {
    promise.catch(() => {});
  }
}

if (heroVideos.length) {
  heroVideos.forEach((video) => {
    video.muted = true;
    video.playsInline = true;
    video.loop = true;
  });

  window.addEventListener('load', () => {
    heroVideos.forEach((video) => playVideo(video));
  }, { once: true });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stopHeroLogoRotation();
      heroVideos.forEach((video) => video.pause());
      return;
    }
    heroVideos.forEach((video) => playVideo(video));
    startHeroLogoRotation();
  });
}


const showcaseRoot = document.querySelector('[data-showcase-root]');
const showcaseScene = showcaseRoot ? showcaseRoot.querySelector('.showcase-scene') : null;
const showcaseFloating = showcaseRoot ? showcaseRoot.querySelector('[data-showcase-floating]') : null;
const showcaseTarget = showcaseRoot ? showcaseRoot.querySelector('[data-showcase-target]') : null;
const showcasePrimaryMedia = showcaseRoot ? showcaseRoot.querySelector('[data-showcase-primary]') : null;

function clamp01(value) {
  return Math.max(0, Math.min(1, value));
}

function lerp(start, end, amount) {
  return start + (end - start) * amount;
}

function easeInOutCubic(value) {
  return value < 0.5
    ? 4 * value * value * value
    : 1 - Math.pow(-2 * value + 2, 3) / 2;
}

function updateShowcaseLayout() {
  if (!showcaseRoot || !showcaseScene || !showcaseFloating || !showcaseTarget) return;

  const sectionRect = showcaseRoot.getBoundingClientRect();
  const sceneRect = showcaseScene.getBoundingClientRect();
  const targetRect = showcaseTarget.getBoundingClientRect();
  const maxScroll = Math.max(showcaseRoot.offsetHeight - window.innerHeight, 1);
  const progress = clamp01(-sectionRect.top / maxScroll);
  const eased = easeInOutCubic(clamp01((progress - 0.04) / 0.8));

  let baseWidth = Math.min(sceneRect.width * 0.78, 1180);
  let baseTopRatio = 0.58;

  if (window.innerWidth <= 900) {
    baseWidth = Math.min(sceneRect.width * 0.86, 780);
    baseTopRatio = 0.5;
  }

  if (window.innerWidth <= 560) {
    baseWidth = sceneRect.width - 36;
    baseTopRatio = 0.5;
  }

  const baseHeight = baseWidth * 9 / 16;
  const startX = (sceneRect.width - baseWidth) / 2;
  const startY = sceneRect.height * baseTopRatio - baseHeight / 2;
  const endX = targetRect.left - sceneRect.left;
  const endY = targetRect.top - sceneRect.top;
  const endWidth = targetRect.width;
  const endHeight = targetRect.height;

  showcaseFloating.style.left = `${lerp(startX, endX, eased)}px`;
  showcaseFloating.style.top = `${lerp(startY, endY, eased)}px`;
  showcaseFloating.style.width = `${lerp(baseWidth, endWidth, eased)}px`;
  showcaseFloating.style.height = `${lerp(baseHeight, endHeight, eased)}px`;
  showcaseFloating.style.borderRadius = `${lerp(window.innerWidth <= 560 ? 24 : 34, 30, eased)}px`;
  showcaseFloating.style.transform = 'none';

  showcaseScene.style.setProperty('--showcase-progress', progress.toFixed(4));
  showcaseScene.style.setProperty('--showcase-ease', eased.toFixed(4));
}

let showcaseTicking = false;

function requestShowcaseLayout() {
  if (showcaseTicking) return;
  showcaseTicking = true;
  window.requestAnimationFrame(() => {
    updateShowcaseLayout();
    showcaseTicking = false;
  });
}

if (showcaseRoot && showcaseScene && showcaseFloating && showcaseTarget) {
  window.addEventListener('load', requestShowcaseLayout, { once: true });
  window.addEventListener('resize', requestShowcaseLayout);
  window.addEventListener('scroll', requestShowcaseLayout, { passive: true });

}

const showcaseGlowCanvas = document.createElement('canvas');
const showcaseGlowContext = showcaseGlowCanvas.getContext('2d', { willReadFrequently: true });
showcaseGlowCanvas.width = 24;
showcaseGlowCanvas.height = 14;

function sampleShowcaseGlow() {
  if (!showcasePrimaryMedia || !showcaseScene || !showcaseGlowContext) return;

  try {
    showcaseGlowContext.clearRect(0, 0, showcaseGlowCanvas.width, showcaseGlowCanvas.height);
    showcaseGlowContext.drawImage(showcasePrimaryMedia, 0, 0, showcaseGlowCanvas.width, showcaseGlowCanvas.height);
    const { data } = showcaseGlowContext.getImageData(0, 0, showcaseGlowCanvas.width, showcaseGlowCanvas.height);
    let red = 0;
    let green = 0;
    let blue = 0;
    let count = 0;

    for (let index = 0; index < data.length; index += 4) {
      const alpha = data[index + 3] / 255;
      if (alpha < 0.1) continue;
      red += data[index];
      green += data[index + 1];
      blue += data[index + 2];
      count += 1;
    }

    if (count) {
      const r = Math.min(255, Math.round((red / count) * 1.08));
      const g = Math.min(255, Math.round((green / count) * 1.08));
      const b = Math.min(255, Math.round((blue / count) * 1.08));
      showcaseScene.style.setProperty('--glow-r', String(r));
      showcaseScene.style.setProperty('--glow-g', String(g));
      showcaseScene.style.setProperty('--glow-b', String(b));
    }
  } catch (error) {
    // ignore image sampling failures
  }
}

if (showcasePrimaryMedia && showcaseScene && showcaseGlowContext) {
  if (showcasePrimaryMedia.complete) {
    sampleShowcaseGlow();
  } else {
    showcasePrimaryMedia.addEventListener('load', sampleShowcaseGlow, { once: true });
  }
}

// Scroll media motion removed by request.


const heroLogoLines = Array.from(document.querySelectorAll('.hero-logo-line'));
let heroLogoIndex = 0;
let heroLogoTimer = null;

function stopHeroLogoRotation() {
  if (heroLogoTimer) {
    window.clearInterval(heroLogoTimer);
    heroLogoTimer = null;
  }
}

function setHeroLogo(index) {
  if (!heroLogoLines.length) return;
  heroLogoIndex = index;
  heroLogoLines.forEach((line, lineIndex) => {
    line.classList.toggle('is-active', lineIndex === index);
  });
}

function startHeroLogoRotation() {
  if (!heroLogoLines.length || heroLogoTimer) return;
  setHeroLogo(0);
  heroLogoTimer = window.setInterval(() => {
    setHeroLogo((heroLogoIndex + 1) % heroLogoLines.length);
  }, 1000);
}
