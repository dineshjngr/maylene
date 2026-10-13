(() => {
  const forms = document.querySelectorAll('.footer__newsletter form, .nl__form');
  forms.forEach(form => {
    const input = form.querySelector('input[type="email"]');
    const button = form.querySelector('button[type="submit"]');
    const status = form.querySelector('.nl__status') || form.parentElement.querySelector('.footer__newsletter-status');
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (!input.value) { input.focus(); return; }
      button.disabled = true; status.dataset.state = ''; status.textContent = 'Subscribing…';
      try {
        const r = await fetch('/api/newsletter', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({email: input.value}), signal: AbortSignal.timeout(20000)});
        const data = await r.json().catch(() => ({}));
        if (r.ok) { status.dataset.state = 'success'; status.textContent = data.message || 'Thanks, you are subscribed.'; input.value = ''; }
        else { status.dataset.state = 'error'; status.textContent = data.error || 'Something went wrong. Please try again.'; }
      } catch { status.dataset.state = 'error'; status.textContent = 'Failed to subscribe. Please try again.'; }
      finally { button.disabled = false; }
    });
  });
})();
