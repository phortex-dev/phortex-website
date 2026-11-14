/* ============================================================
   PHORTEX — Post-Quantum page interactions
   Everything runs in the browser; nothing is sent anywhere
   except the waitlist form, which posts to Formspree.
   ============================================================ */
(function () {
  'use strict';

  /* ── Mosca exposure check ─────────────────────────────── */
  var calc = document.querySelector('[data-mosca]');
  if (calc) {
    var v = { x: 7, y: 4, z: 10 };
    var out = function (k) { return calc.querySelector('[data-out="' + k + '"]'); };
    var render = function () {
      ['x', 'y', 'z'].forEach(function (k) { out(k).textContent = v[k] + ' yrs'; });
      var need = v.x + v.y, max = Math.max(need, v.z, 1);
      var pct = function (n) { return (n / max * 100).toFixed(1) + '%'; };
      calc.querySelector('[data-bar="x"]').style.width = pct(v.x);
      calc.querySelector('[data-bar="y"]').style.width = pct(v.y);
      calc.querySelector('[data-bar="z"]').style.width = pct(v.z);
      calc.querySelector('[data-need]').textContent = need;
      calc.querySelector('[data-zval]').textContent = v.z;
      var gap = v.z - need, box = calc.querySelector('[data-verdict]'), cls, tag, title, text;
      if (gap < 0) { cls = 'hi'; tag = 'ALREADY EXPOSED'; title = 'Data you send today could be read before you finish migrating.'; text = 'Start with an inventory and fix your longest-lived data paths first.'; }
      else if (gap <= 3) { cls = 'md'; tag = 'TIGHT'; title = 'Your margin is ' + gap + (gap === 1 ? ' year.' : ' years.'); text = 'One delayed vendor or hardware cycle puts you behind. Plan this budget year.'; }
      else { cls = 'ok'; tag = 'TIME TO PLAN'; title = 'About ' + gap + ' years of margin under this assumption.'; text = 'Use it: inventory now, migrate on normal replacement cycles, and stop buying anything that can’t be upgraded.'; }
      box.className = 'pq-verdict ' + cls;
      box.querySelector('b').textContent = tag;
      box.querySelector('strong').textContent = title;
      box.querySelector('span').textContent = text;
    };
    calc.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-k]');
      if (!b) return;
      var k = b.getAttribute('data-k');
      v[k] = Math.max(1, Math.min(30, v[k] + parseInt(b.getAttribute('data-d'), 10)));
      render();
    });
    render();
  }

  /* ── Toolkit demo tabs ────────────────────────────────── */
  var demo = document.querySelector('[data-demo]');
  if (demo) {
    var tabs = demo.querySelectorAll('[role="tab"]');
    var panels = demo.querySelectorAll('[role="tabpanel"]');
    var caption = demo.querySelector('[data-caption]');
    var next = demo.querySelector('[data-next]');
    var names = ['Scan', 'Analyze', 'Report'];
    var caps = ['5 assets discovered', 'Ranked by what an attacker could harvest', 'Plain-English plan'];
    var cur = 0;
    var show = function (i) {
      cur = i;
      tabs.forEach(function (t, j) { t.setAttribute('aria-selected', j === i ? 'true' : 'false'); t.tabIndex = j === i ? 0 : -1; });
      panels.forEach(function (p, j) { p.hidden = j !== i; });
      caption.textContent = caps[i];
      next.textContent = i === 2 ? 'Start the demo over' : 'Next: ' + names[i + 1] + ' →';
    };
    tabs.forEach(function (t, i) {
      t.addEventListener('click', function () { show(i); });
      t.addEventListener('keydown', function (e) {
        if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
          var n = (i + (e.key === 'ArrowRight' ? 1 : 2)) % 3; show(n); tabs[n].focus();
        }
      });
    });
    next.addEventListener('click', function () { show((cur + 1) % 3); });
    show(0);
  }

  /* ── Timeline filter ──────────────────────────────────── */
  var tl = document.querySelector('[data-timeline]');
  if (tl) {
    document.querySelectorAll('[data-tl-filter]').forEach(function (btn, _, all) {
      btn.addEventListener('click', function () {
        var f = btn.getAttribute('data-tl-filter');
        all.forEach(function (b) { b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'); });
        tl.querySelectorAll('li[data-aud]').forEach(function (li) {
          li.hidden = !(f === 'all' || li.getAttribute('data-aud') === f);
        });
      });
    });
  }

  /* ── Action-plan checklist (remembered in this browser only) ── */
  var steps = document.querySelector('[data-steps]');
  if (steps) {
    var KEY = 'phortex-pqc-steps';
    var state = {};
    try { state = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { state = {}; }
    var items = steps.querySelectorAll('.pq-step');
    var count = document.querySelector('[data-done-count]');
    var bar = document.querySelector('[data-done-bar]');
    var paint = function () {
      var n = 0;
      items.forEach(function (it, i) {
        var on = !!state[i]; if (on) n++;
        it.classList.toggle('done', on);
        var b = it.querySelector('.pq-check');
        b.setAttribute('aria-pressed', on ? 'true' : 'false');
        b.textContent = on ? '✓' : '';
      });
      if (count) count.textContent = n + '/' + items.length + ' done';
      if (bar) bar.style.width = (n / items.length * 100).toFixed(0) + '%';
    };
    items.forEach(function (it, i) {
      it.querySelector('.pq-check').addEventListener('click', function () {
        state[i] = !state[i];
        try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* private mode: still works for this visit */ }
        paint();
      });
    });
    paint();
  }

  /* ── Copy vendor questions ────────────────────────────── */
  var copyBtn = document.querySelector('[data-copy]');
  if (copyBtn) {
    copyBtn.addEventListener('click', function () {
      var list = document.getElementById(copyBtn.getAttribute('data-copy'));
      var text = Array.prototype.map.call(list.querySelectorAll('li'), function (li, i) { return (i + 1) + '. ' + li.textContent.trim(); }).join('\n');
      var status = document.querySelector('[data-copy-status]');
      var done = function (ok) { if (status) status.textContent = ok ? 'Copied. Paste it into an email.' : 'Select the questions and copy them manually.'; };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
      else done(false);
    });
  }

  /* ── Waitlist forms ───────────────────────────────────── */
  document.querySelectorAll('form.pq-wait').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var msg = f.querySelector('.pq-msg'), btn = f.querySelector('button[type="submit"]'), email = f.querySelector('input[type="email"]');
      if (!email.value || !email.checkValidity()) { msg.textContent = 'Please enter a valid email.'; return; }
      var label = btn.textContent;
      btn.disabled = true; btn.textContent = 'Sending…';
      fetch(f.action, { method: 'POST', body: new FormData(f), headers: { Accept: 'application/json' } })
        .then(function (r) { if (!r.ok) throw new Error(); f.reset(); btn.textContent = 'You’re on the list'; msg.textContent = 'Thanks. We’ll email you when the PQC Toolkit launches.'; })
        .catch(function () { btn.disabled = false; btn.textContent = label; msg.textContent = 'That didn’t go through. Please try again, or email contact@phortex.com.'; });
    });
  });
})();
