/* ============================================================
   PHORTEX — Learning Academy course pages
   Click-to-load YouTube (youtube-nocookie), knowledge checks,
   per-device progress, self-issued certificate. No tracking.
   ============================================================ */
(function () {
  'use strict';

  // ---- progress (this browser only; storage can be blocked, so never rely on it)
  function key(course) { return 'phx-academy:' + course; }
  function getDone(course) {
    try {
      var v = JSON.parse(localStorage.getItem(key(course)) || '[]');
      return Array.isArray(v) ? v.map(Number) : [];
    } catch (e) { return []; }
  }
  function setDone(course, list) {
    try { localStorage.setItem(key(course), JSON.stringify(list)); } catch (e) { /* storage blocked */ }
  }
  function mark(course, n, on) {
    var d = getDone(course).filter(function (x) { return x !== n; });
    if (on) d.push(n);
    setDone(course, d.sort(function (a, b) { return a - b; }));
    paint();
  }

  function paint() {
    document.querySelectorAll('.lx-progress[data-course]').forEach(function (el) {
      var done = getDone(el.dataset.course).length, total = +el.dataset.total;
      if (!done) { el.hidden = true; return; }
      el.hidden = false;
      el.querySelector('.lx-bar span').style.width = Math.min(100, Math.round(done / total * 100)) + '%';
      el.querySelector('p').textContent = done >= total
        ? 'Course complete. Your certificate is ready.'
        : done + ' of ' + total + ' lessons complete';
      if (done >= total && !el.querySelector('a')) {
        var a = document.createElement('a');
        a.href = (location.pathname.indexOf('/_preview/') === 0 ? '/_preview' : '') + '/academy/' + el.dataset.course + '/certificate/';
        a.textContent = 'Get your certificate →';
        el.appendChild(a);
      }
    });
    document.querySelectorAll('[data-course] [data-lesson]').forEach(function (li) {
      var c = li.closest('[data-course]').dataset.course;
      li.classList.toggle('is-done', getDone(c).indexOf(+li.dataset.lesson) !== -1);
    });
    document.querySelectorAll('.lx-done').forEach(function (b) {
      var on = getDone(b.dataset.course).indexOf(+b.dataset.lesson) !== -1;
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
      b.textContent = on ? '✓ Lesson complete' : 'Mark lesson complete';
      b.classList.toggle('is-on', on);
    });
    // "Start the course" becomes "Continue" at the first unfinished lesson
    document.querySelectorAll('[data-resume]').forEach(function (a) {
      var list = document.querySelector('.lx-lessons[data-course]');
      if (!list) return;
      var done = getDone(list.dataset.course);
      if (!done.length) return;
      var next = Array.prototype.find.call(list.querySelectorAll('[data-lesson]'), function (li) {
        return done.indexOf(+li.dataset.lesson) === -1 && li.querySelector('a');
      });
      if (next) { a.href = next.querySelector('a').getAttribute('href'); a.textContent = 'Continue the course'; }
      else { a.textContent = 'Review the course'; }
    });
  }

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest('.lx-done');
    if (b) { mark(b.dataset.course, +b.dataset.lesson, b.getAttribute('aria-pressed') !== 'true'); return; }
    var nxt = ev.target.closest('[data-complete-on-click]');
    if (nxt) { var p = nxt.dataset.completeOnClick.split(':'); mark(p[0], +p[1], true); }
    if (ev.target.closest('[data-print]')) window.print();
  });

  // ---- YouTube: load the player only when asked (no third-party requests before a click)
  document.querySelectorAll('.lx-video[data-yt]').forEach(function (box) {
    var btn = box.querySelector('.lx-play');
    btn.addEventListener('click', function () {
      var f = document.createElement('iframe');
      f.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(box.dataset.yt) + '?autoplay=1&rel=0&modestbranding=1';
      f.title = box.dataset.title || 'Lesson video';
      f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
      f.allowFullscreen = true;
      f.referrerPolicy = 'strict-origin-when-cross-origin';
      box.innerHTML = '';
      box.appendChild(f);
      box.classList.add('is-playing');
      f.focus();
    });
  });

  // ---- knowledge checks
  document.querySelectorAll('form[data-quiz]').forEach(function (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var qs = form.querySelectorAll('.lx-q'), right = 0, unanswered = 0;
      qs.forEach(function (q) {
        var pick = q.querySelector('input:checked'), ans = q.dataset.answer, why = q.querySelector('.lx-why');
        q.classList.remove('is-right', 'is-wrong');
        q.querySelectorAll('.lx-opt').forEach(function (o) { o.classList.remove('is-answer'); });
        if (!pick) { unanswered++; why.hidden = true; return; }
        var ok = pick.value === ans;
        if (ok) right++;
        q.classList.add(ok ? 'is-right' : 'is-wrong');
        q.querySelectorAll('.lx-opt')[+ans].classList.add('is-answer');
        why.querySelector('strong').textContent = ok ? 'Correct.' : 'Not quite.';
        why.hidden = false;
      });
      var s = form.querySelector('.lx-score');
      s.textContent = unanswered
        ? 'Answer all ' + qs.length + ' questions to see your score.'
        : 'You got ' + right + ' of ' + qs.length + (right === qs.length ? '. Nicely done.' : '. Review the explanations above.');
    });
  });

  // ---- certificate
  var gate = document.querySelector('.lx-cert-gate');
  if (gate) {
    var course = gate.dataset.cert, total = +gate.dataset.total;
    var form = gate.querySelector('.lx-cert-form'), cert = document.querySelector('.lx-cert');
    if (getDone(course).length >= total) {
      gate.querySelector('.lx-cert-locked').textContent = 'You finished every lesson. Enter your name to create your certificate.';
      form.hidden = false;
    }
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var name = form.querySelector('input').value.trim();
      if (!name) return;
      cert.querySelector('.lx-cert-name').textContent = name;
      cert.querySelector('.lx-cert-date').textContent = new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
      gate.hidden = true;
      cert.hidden = false;
    });
  }

  paint();
})();
