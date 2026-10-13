// Behaviour for generated content pages: FAQ search, contact form, calculator, wishlist, collection preset.
(() => {
  // FAQ search
  const fq = document.getElementById('faq-q');
  if (fq) {
    const items = [...document.querySelectorAll('#faq-list .faq')];
    const count = document.getElementById('faq-count'), empty = document.getElementById('faq-empty');
    fq.addEventListener('input', () => {
      const t = fq.value.trim().toLowerCase(); let n = 0;
      items.forEach(d => { const ok = !t || d.textContent.toLowerCase().includes(t); d.hidden = !ok; if (ok) n++; if (t && ok) d.open = true; });
      count.textContent = `${n} ${n === 1 ? 'question' : 'questions'}`; empty.hidden = n > 0;
    });
  }
  // Contact form → live /api/contact
  const cf = document.getElementById('contact-form');
  if (cf) {
    const msg = cf.querySelector('#c-message'), counter = document.getElementById('c-counter'), status = document.getElementById('contact-status');
    msg.addEventListener('input', () => counter.textContent = msg.value.length);
    cf.addEventListener('submit', async e => {
      e.preventDefault();
      const fields = [...cf.querySelectorAll('input,select,textarea')];
      let bad = null; fields.forEach(f => { const ok = f.checkValidity(); f.setAttribute('aria-invalid', String(!ok)); if (!ok && !bad) bad = f; });
      if (bad) { status.dataset.state = 'error'; status.textContent = 'Please complete the highlighted fields.'; bad.focus(); return; }
      const btn = cf.querySelector('button[type=submit]'); btn.disabled = true; status.dataset.state = ''; status.textContent = 'Sending…';
      try {
        const body = {name: cf.querySelector('#c-name').value, email: cf.querySelector('#c-email').value, subject: cf.querySelector('#c-subject').value, message: msg.value};
        const r = await fetch('/api/contact', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body), signal: AbortSignal.timeout(20000)});
        const d = await r.json().catch(() => ({}));
        if (r.ok) { status.dataset.state = 'success'; status.textContent = d.message || 'Message sent. We aim to respond within 24 hours on business days.'; cf.reset(); counter.textContent = '0'; }
        else { status.dataset.state = 'error'; status.textContent = d.error || d.message || 'Something went wrong. Please email contact@maylene.uk.'; }
      } catch { status.dataset.state = 'error'; status.textContent = 'Could not send. Please email contact@maylene.uk.'; }
      finally { btn.disabled = false; }
    });
  }
  // Dosage calculator
  const calc = document.getElementById('calc');
  if (calc) {
    const products = JSON.parse(calc.dataset.products);
    const sel = document.getElementById('calc-product'), mg = document.getElementById('calc-mg'), cl = document.getElementById('calc-clicks');
    const out = document.getElementById('calc-out'), meta = document.getElementById('calc-meta'), pts = document.getElementById('calc-points'), note = document.getElementById('calc-note'), link = document.getElementById('calc-link');
    const fmt = n => (Math.round(n * 100) / 100).toString();
    const cur = () => products.find(p => p.handle === sel.value);
    const ready = () => { out.innerHTML = '<strong>Ready when you are.</strong><p>Enter milligrams or clicks to see the matching amount here.</p>'; };
    function setup() {
      const p = cur(); meta.textContent = `Labelled content per pen: ${p.strengthMg} mg`; link.href = '/products/' + p.handle;
      const rp = p.conversion && p.conversion.referencePoints;
      pts.innerHTML = rp ? 'Published conversion points: ' + rp.map(r => `<span>${r.mg} mg · ${r.clicks} clicks</span>`).join('') : '';
      note.textContent = p.note || 'Based on the published values for matching pens. Check your pen’s instructions. This tool does not choose a dose.';
      mg.disabled = cl.disabled = !p.conversion; mg.value = cl.value = '';
      if (!p.conversion) out.innerHTML = '<strong>Not available.</strong><p>A confirmed click conversion is not available for this product.</p>'; else ready();
    }
    function convert(from) {
      const p = cur(); if (!p.conversion) return;
      const c = p.conversion, rp = c.referencePoints;
      if (from === 'mg') {
        const v = parseFloat(mg.value); if (!(v > 0)) { cl.value = ''; return ready(); }
        let clicks; if (rp) { const hit = rp.find(r => r.mg === v); if (!hit) { cl.value = ''; out.innerHTML = '<strong>Reference only.</strong><p>This blend uses supplied reference points only. Choose one of the published values.</p>'; return; } clicks = hit.clicks; } else clicks = Math.round(v * c.clicksPerMg);
        cl.value = clicks; out.innerHTML = `<strong>${fmt(v)} mg ≈ ${clicks} clicks</strong><p>${p.label}, ${p.strengthMg} mg per pen.</p>`;
      } else {
        const v = parseInt(cl.value, 10); if (!(v > 0)) { mg.value = ''; return ready(); }
        let m; if (rp) { const hit = rp.find(r => r.clicks === v); if (!hit) { mg.value = ''; out.innerHTML = '<strong>Reference only.</strong><p>This blend uses supplied reference points only. Choose one of the published values.</p>'; return; } m = hit.mg; } else m = v / c.clicksPerMg;
        mg.value = fmt(m); out.innerHTML = `<strong>${v} clicks ≈ ${fmt(m)} mg</strong><p>${p.label}, ${p.strengthMg} mg per pen.</p>`;
      }
    }
    sel.addEventListener('change', setup); mg.addEventListener('input', () => convert('mg')); cl.addEventListener('input', () => convert('clicks'));
    document.getElementById('calc-clear').addEventListener('click', () => { mg.value = cl.value = ''; ready(); });
    const pre = new URLSearchParams(location.search).get('product'); if (pre && products.some(p => p.handle === pre)) sel.value = pre;
    setup();
  }
  // Wishlist page: render saved products as cards
  const wl = document.getElementById('wl-grid');
  if (wl) {
    let saved = []; try { saved = JSON.parse(localStorage.getItem('maylene-featured-wishlist') || '[]'); } catch {}
    fetch('/products').then(r => r.text()).then(t => {
      const doc = new DOMParser().parseFromString(t, 'text/html');
      const cards = saved.map(h => doc.querySelector(`.card[data-handle="${CSS.escape(h)}"]`)).filter(Boolean);
      cards.forEach(c => wl.append(document.importNode(c, true)));
      document.getElementById('wl-count').textContent = cards.length ? `${cards.length} saved ${cards.length === 1 ? 'product' : 'products'}` : '';
      document.getElementById('wl-empty').hidden = cards.length > 0;
      if (cards.length) { const s = document.createElement('script'); s.src = '/redesign/products.js?wl=' + Date.now(); document.body.append(s); }
    });
  }
})();
