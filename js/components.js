/* ============================================================
   PHORTEX — Shared Components
   Injects nav and footer into every page
   ============================================================ */

(function () {

  const NAV_HTML = `
<nav class="nav" role="navigation" aria-label="Main navigation">
  <div class="nav-inner">
    <a href="/" class="nav-logo" aria-label="Phortex home">PHORTEX<span class="nav-logo-dot">.</span></a>
    <ul class="nav-links" role="list">
      <li><a href="/security/">Security</a></li>
      <li><a href="/ai/">AI Services</a></li>
      <li><a href="/campus/">Campus</a></li>
      <li><a href="/about/">About</a></li>
      <li><a href="/#contact" class="nav-cta">Book a Call</a></li>
    </ul>
    <button class="nav-hamburger" aria-label="Toggle menu" aria-expanded="false">
      <span></span><span></span><span></span>
    </button>
  </div>
</nav>`;

  const FOOTER_HTML = `
<footer>
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="footer-brand-logo">PHORTEX<span style="color:var(--cyan)">.</span></div>
        <p class="footer-tagline">Cybersecurity consulting, AI strategy, and college admissions guidance — built on 25 years of hands-on expertise and Wharton business thinking.</p>
        <div class="footer-socials">
          <a href="https://linkedin.com/company/phortex-llc" target="_blank" rel="noopener" class="footer-social-btn" aria-label="LinkedIn">in</a>
          <a href="https://x.com/PhortexLLC" target="_blank" rel="noopener" class="footer-social-btn" aria-label="X / Twitter">𝕏</a>
          <a href="https://youtube.com/@PhortexLLC" target="_blank" rel="noopener" class="footer-social-btn" aria-label="YouTube">▶</a>
          <a href="https://tiktok.com/@PhortexSecure" target="_blank" rel="noopener" class="footer-social-btn" aria-label="TikTok">♪</a>
        </div>
      </div>
      <div class="footer-col">
        <h5>Security</h5>
        <ul>
          <li><a href="/security/">Overview</a></li>
          <li><a href="/security/#health-check">Health Check</a></li>
          <li><a href="/security/#smb">SMB Assessment</a></li>
          <li><a href="/security/#vciso">Virtual CISO</a></li>
          <li><a href="/security/#consulting">Consulting</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h5>AI Services</h5>
        <ul>
          <li><a href="/ai/">Overview</a></li>
          <li><a href="/ai/#workshop">AI Workshop</a></li>
          <li><a href="/ai/#integration">AI Integration</a></li>
          <li><a href="/ai/#bundle">AI + Security</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h5>Company</h5>
        <ul>
          <li><a href="/campus/">Phortex Campus</a></li>
          <li><a href="/about/">About</a></li>
          <li><a href="/#contact">Contact</a></li>
          <li><a href="https://x.com/PhortexLLC" target="_blank" rel="noopener">@PhortexLLC</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span class="year"></span> Phortex LLC · Doylestown, PA · All rights reserved</span>
      <span class="footer-mono">// Built on AI. Delivered by expertise.</span>
    </div>
  </div>
</footer>`;

  // Inject nav before first child of body
  const navEl = document.createElement('div');
  navEl.innerHTML = NAV_HTML;
  document.body.insertBefore(navEl.firstElementChild, document.body.firstChild);

  // Inject footer at end of body
  const footerEl = document.createElement('div');
  footerEl.innerHTML = FOOTER_HTML;
  document.body.appendChild(footerEl.firstElementChild);

})();
