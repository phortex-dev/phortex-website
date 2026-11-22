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
      <li><a href="/post-quantum/" class="nav-pq">Post-Quantum<span class="nav-new">New</span></a></li>
      <li><a href="/security/">Security</a></li>
      <li><a href="/ai/">AI Services</a></li>
      <li><a href="/security-tldr/">Sec TL;DR</a></li>
      <li><a href="/ai-security/">AI-Sec TL;DR</a></li>
      <li><a href="/academy/">Learning Academy</a></li>
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
        <p class="footer-tagline">Cybersecurity consulting, AI strategy, and a learning academy — built on 25 years of hands-on expertise and Wharton business thinking.</p>
        <p class="footer-contact"><a href="tel:+12676411557">267-641-1557</a><br><a href="mailto:jeff@phortex.com">jeff@phortex.com</a></p>
      </div>
      <div class="footer-col">
        <h5>Security</h5>
        <ul>
          <li><a href="/security/">Overview</a></li>
          <li><a href="/post-quantum/">Post-Quantum Readiness</a></li>
          <li><a href="/security/#health-check">Health Check</a></li>
          <li><a href="/security/#smb">SMB Assessment</a></li>
          <li><a href="/security/#vciso">Virtual CISO</a></li>
          <li><a href="/security/#consulting">Consulting</a></li>
          <li><a href="/security-tldr/">Security TL;DR</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h5>AI Services</h5>
        <ul>
          <li><a href="/ai/">Overview</a></li>
          <li><a href="/ai/#workshop">AI Workshop</a></li>
          <li><a href="/ai/#integration">AI Integration</a></li>
          <li><a href="/ai/#bundle">AI + Security</a></li>
          <li><a href="/ai-security/">AI Security TL;DR</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h5>Company</h5>
        <ul>
          <li><a href="/academy/">Learning Academy</a></li>
          <li><a href="/about/">About</a></li>
          <li><a href="/#contact">Contact</a></li>
          <li><a href="/post-quantum/risk/">Post-Quantum, Explained</a></li>
          <li><a href="/privacy/">Privacy Policy</a></li>
          <li><a href="/terms/">Terms of Service</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© <span class="year"></span> Phortex LLC · Doylestown, PA · All rights reserved</span>
      <span class="footer-legal"><a href="/privacy/">Privacy</a> · <a href="/terms/">Terms</a> · <a href="tel:+12676411557">267-641-1557</a></span>
      <span class="footer-mono">// Built on AI. Delivered by expertise.</span>
    </div>
  </div>
</footer>`;

  // Inject nav before first child of body
  const navEl = document.createElement('div');
  navEl.innerHTML = NAV_HTML;
  document.body.insertBefore(navEl.firstElementChild, document.body.firstChild);

  // Inject footer at end of body. This script runs at the top of <body>, so wait until the
  // page has been parsed; otherwise "the end of body" is still the top of the page.
  function addFooter() {
    const footerEl = document.createElement('div');
    footerEl.innerHTML = FOOTER_HTML;
    document.body.appendChild(footerEl.firstElementChild);
    document.querySelectorAll('footer .year').forEach(function (el) { el.textContent = new Date().getFullYear(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addFooter);
  else addFooter();

})();
