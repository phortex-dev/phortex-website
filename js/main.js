/* ============================================================
   PHORTEX — Main JavaScript
   ============================================================ */

(function () {
  'use strict';

  // ── Nav scroll behavior ─────────────────────────────────
  const nav = document.querySelector('.nav');
  if (nav) {
    const onScroll = () => {
      nav.classList.toggle('scrolled', window.scrollY > 24);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // ── Mobile nav toggle ───────────────────────────────────
  const hamburger = document.querySelector('.nav-hamburger');
  const navLinks = document.querySelector('.nav-links');
  if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      const isOpen = navLinks.classList.contains('open');
      hamburger.setAttribute('aria-expanded', isOpen);
    });
    document.addEventListener('click', (e) => {
      if (!hamburger.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove('open');
      }
    });
  }

  // ── Active nav link ─────────────────────────────────────
  const path = window.location.pathname;
  document.querySelectorAll('.nav-links a:not(.nav-cta)').forEach(a => {
    const href = a.getAttribute('href') || '';
    const normalized = href.replace(/\/index\.html$/, '/').replace(/index\.html$/, '');
    if (path === normalized || (normalized !== '/' && path.startsWith(normalized))) {
      a.classList.add('active');
    }
  });

  // ── Scroll reveal ───────────────────────────────────────
  const revealEls = document.querySelectorAll('.reveal');
  if (revealEls.length) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach(el => io.observe(el));
  }

  // ── Services tab system ─────────────────────────────────
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanels.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add('active');
    });
  });

  // ── Animated counters ───────────────────────────────────
  const counters = document.querySelectorAll('[data-count]');
  if (counters.length) {
    const countIO = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (!e.isIntersecting) return;
        const el = e.target;
        const target = parseFloat(el.dataset.count);
        const prefix = el.dataset.prefix || '';
        const suffix = el.dataset.suffix || '';
        const decimals = el.dataset.decimals ? parseInt(el.dataset.decimals) : 0;
        const duration = 1600;
        const start = performance.now();
        const animate = (now) => {
          const elapsed = now - start;
          const progress = Math.min(elapsed / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          const current = target * eased;
          el.textContent = prefix + current.toFixed(decimals) + suffix;
          if (progress < 1) requestAnimationFrame(animate);
        };
        requestAnimationFrame(animate);
        countIO.unobserve(el);
      });
    }, { threshold: 0.5 });
    counters.forEach(c => countIO.observe(c));
  }

  // ── Hero stagger animation ──────────────────────────────
  const heroItems = document.querySelectorAll('.hero-stagger > *');
  heroItems.forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(22px)';
    el.style.transition = `opacity 0.6s ease ${i * 0.1}s, transform 0.6s ease ${i * 0.1}s`;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      el.style.opacity = '1';
      el.style.transform = 'none';
    }));
  });

  // ── Contact form ────────────────────────────────────────
  const form = document.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      const orig = btn.textContent;
      btn.disabled = true;
      btn.textContent = 'Sending…';

      // Formspree integration — replace action attr with real endpoint
      const action = form.getAttribute('action');
      if (action && action.includes('formspree')) {
        try {
          const res = await fetch(action, {
            method: 'POST',
            body: new FormData(form),
            headers: { Accept: 'application/json' }
          });
          if (res.ok) {
            btn.textContent = '✓ Message Sent!';
            btn.style.background = 'var(--emerald)';
            btn.style.color = 'var(--navy)';
            form.reset();
          } else {
            throw new Error();
          }
        } catch {
          btn.textContent = 'Error — try email';
          btn.style.background = '#e55';
        }
      } else {
        // Demo mode
        await new Promise(r => setTimeout(r, 1000));
        btn.textContent = '✓ Message Sent!';
        btn.style.background = 'var(--emerald)';
        btn.style.color = 'var(--navy)';
        setTimeout(() => {
          btn.textContent = orig;
          btn.style.background = '';
          btn.style.color = '';
          btn.disabled = false;
          form.reset();
        }, 3500);
      }
    });
  }

  // ── Current year in footer ──────────────────────────────
  document.querySelectorAll('.year').forEach(el => {
    el.textContent = new Date().getFullYear();
  });

})();
