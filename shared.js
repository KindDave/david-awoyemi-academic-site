const root = document.documentElement;
const storageKey = 'da-portfolio-theme';
const particleCanvas = document.getElementById('particles');

function applyTheme(theme) {
  root.setAttribute('data-theme', theme);
  document.querySelectorAll('[data-theme-label]').forEach((node) => {
    node.textContent = theme === 'dark' ? 'Light' : 'Dark';
  });
}

const savedTheme = localStorage.getItem(storageKey) || 'light';
applyTheme(savedTheme);

document.querySelectorAll('[data-theme-toggle]').forEach((button) => {
  button.addEventListener('click', () => {
    const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    localStorage.setItem(storageKey, next);
    applyTheme(next);
    initParticles();
  });
});

const mobileButton = document.querySelector('[data-mobile-toggle]');
const mobileNav = document.querySelector('[data-mobile-nav]');
if (mobileButton && mobileNav) {
  mobileButton.addEventListener('click', () => {
    const next = !mobileNav.classList.contains('is-open');
    mobileNav.classList.toggle('is-open', next);
    mobileButton.classList.toggle('is-open', next);
    mobileButton.setAttribute('aria-expanded', String(next));
  });

  mobileNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      mobileNav.classList.remove('is-open');
      mobileButton.classList.remove('is-open');
      mobileButton.setAttribute('aria-expanded', 'false');
    });
  });
}

const fadeObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('is-visible');
      fadeObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.fade').forEach((node) => fadeObserver.observe(node));

const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) {
      return;
    }

    entry.target.querySelectorAll('[data-target]').forEach((node) => {
      const target = Number(node.getAttribute('data-target') || '0');
      const suffix = node.getAttribute('data-suffix') || '+';
      let current = 0;
      const step = Math.max(1, Math.ceil(target / 30));
      const timer = window.setInterval(() => {
        current = Math.min(target, current + step);
        node.textContent = `${current}${suffix}`;
        if (current >= target) {
          window.clearInterval(timer);
        }
      }, 35);
    });

    counterObserver.unobserve(entry.target);
  });
}, { threshold: 0.32 });

document.querySelectorAll('[data-counter-group]').forEach((node) => counterObserver.observe(node));

document.querySelectorAll('[data-accordion-button]').forEach((button) => {
  button.addEventListener('click', () => {
    const item = button.closest('.accordion-item');
    const panel = item?.querySelector('[data-accordion-panel]');
    if (!item || !panel) {
      return;
    }

    const isOpen = item.classList.contains('is-open');
    item.classList.toggle('is-open', !isOpen);
    button.setAttribute('aria-expanded', String(!isOpen));
    panel.hidden = isOpen;
  });
});

document.querySelectorAll('[data-mailto-form]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const target = form.getAttribute('data-mailto-target');
    if (!target) {
      return;
    }

    const data = new FormData(form);
    const fullName = [data.get('first_name'), data.get('last_name')].filter(Boolean).join(' ').trim();
    const replyEmail = String(data.get('reply_email') || '').trim();
    const organization = String(data.get('organization') || '').trim();
    const inquiryType = String(data.get('inquiry_type') || '').trim();
    const subject = String(data.get('subject') || inquiryType || 'Website inquiry').trim();
    const message = String(data.get('message') || '').trim();

    const body = [
      fullName ? `Name: ${fullName}` : '',
      replyEmail ? `Reply email: ${replyEmail}` : '',
      organization ? `Organization: ${organization}` : '',
      inquiryType ? `Inquiry type: ${inquiryType}` : '',
      '',
      message,
    ].filter(Boolean).join('\n');

    window.location.href = `mailto:${encodeURIComponent(target)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  });
});

document.querySelectorAll('[data-play-video]').forEach((button) => {
  button.addEventListener('click', () => {
    const src = button.getAttribute('data-play-video');
    if (!src) {
      return;
    }

    button.innerHTML = `<iframe src="${src}" frameborder="0" allow="autoplay; accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>`;
    button.removeAttribute('data-play-video');
    button.disabled = true;
  });
});

document.querySelectorAll('[data-course-tab]').forEach((button) => {
  button.addEventListener('click', () => {
    const target = button.getAttribute('data-course-tab');
    if (!target) {
      return;
    }

    document.querySelectorAll('[data-course-tab]').forEach((tab) => {
      tab.classList.toggle('is-active', tab === button);
    });

    document.querySelectorAll('[data-course-panel]').forEach((panel) => {
      panel.classList.toggle('is-active', panel.getAttribute('data-course-panel') === target);
    });
  });
});

let particles = [];
let context = null;
let width = 0;
let height = 0;

function particlePalette() {
  return root.getAttribute('data-theme') === 'dark'
    ? ['#8bb4ff', '#b4ccff', '#f0c76a', '#ffffff']
    : ['#0f2d6b', '#1f4ba3', '#c3902f', '#6d8fd4'];
}

function resizeCanvas() {
  if (!particleCanvas) {
    return;
  }
  width = particleCanvas.width = window.innerWidth;
  height = particleCanvas.height = window.innerHeight;
}

function initParticles() {
  if (!particleCanvas) {
    return;
  }

  context = particleCanvas.getContext('2d');
  resizeCanvas();
  const colors = particlePalette();
  const count = Math.max(28, Math.floor((width * height) / 16000));
  particles = Array.from({ length: count }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    radius: Math.random() * 1.8 + 0.6,
    color: colors[Math.floor(Math.random() * colors.length)],
    driftX: (Math.random() - 0.5) * 0.15,
    driftY: Math.random() * 0.22 + 0.05,
    alpha: Math.random() * 0.45 + 0.25,
    phase: Math.random() * Math.PI * 2,
  }));
}

function animateParticles() {
  if (!context || !particleCanvas) {
    return;
  }

  context.clearRect(0, 0, width, height);
  particles.forEach((particle) => {
    particle.y -= particle.driftY;
    particle.x += particle.driftX;
    particle.phase += 0.02;

    if (particle.y < -6) particle.y = height + 6;
    if (particle.x < -6) particle.x = width + 6;
    if (particle.x > width + 6) particle.x = -6;

    context.beginPath();
    context.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
    context.fillStyle = particle.color;
    context.globalAlpha = particle.alpha * (0.7 + 0.3 * Math.sin(particle.phase));
    context.fill();
  });
  context.globalAlpha = 1;
  window.requestAnimationFrame(animateParticles);
}

if (particleCanvas) {
  initParticles();
  animateParticles();
  window.addEventListener('resize', initParticles, { passive: true });
}
