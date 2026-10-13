(() => {
  const root = document.querySelector('[data-product-page]');
  if (!root) return;
  const product = JSON.parse(root.dataset.productPage);
  const money = value => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(value);

  /* ----- Gallery: thumbnails drive a scroll-snap track that also swipes on touch ----- */
  const gallery = document.querySelector('[data-gallery]');
  if (gallery) {
    const track = gallery.querySelector('[data-track]');
    const slides = [...track.children];
    const thumbs = [...gallery.querySelectorAll('.pdp-gallery__thumb')];
    const dots = [...gallery.querySelectorAll('.pdp-gallery__dot')];
    let current = 0;
    const mark = index => {
      current = index;
      slides.forEach((slide, i) => slide.toggleAttribute('aria-hidden', i !== index));
      thumbs.forEach((thumb, i) => thumb.setAttribute('aria-pressed', String(i === index)));
      dots.forEach((dot, i) => dot.classList.toggle('is-active', i === index));
    };
    const go = index => {
      index = (index + slides.length) % slides.length;
      track.scrollTo({ left: slides[index].offsetLeft, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' });
      mark(index);
    };
    thumbs.forEach((thumb, i) => thumb.addEventListener('click', () => go(i)));
    track.addEventListener('keydown', event => {
      if (event.key === 'ArrowRight') { event.preventDefault(); go(current + 1); }
      if (event.key === 'ArrowLeft') { event.preventDefault(); go(current - 1); }
    });
    let ticking = false;
    track.addEventListener('scroll', () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        ticking = false;
        const index = Math.round(track.scrollLeft / track.clientWidth);
        if (index !== current && slides[index]) mark(index);
      });
    }, { passive: true });
  }

  /* ----- Quantity tiers update the button, the sticky bar and the price ----- */
  const addButton = document.querySelector('[data-add]');
  const totalLabel = addButton?.querySelector('[data-total]');
  const addLabel = addButton?.querySelector('[data-add-label]');
  const status = document.querySelector('[data-cart-status]');
  const bar = document.querySelector('[data-bar]');
  const barAdd = bar?.querySelector('[data-bar-add]');
  const radios = [...document.querySelectorAll('input[name="quantity"]')];
  const quantity = () => Number(radios.find(radio => radio.checked)?.value || 1);
  const unitLabel = n => `${n} ${n === 1 ? product.unit : product.units}`;
  const syncQuantity = () => {
    const n = quantity();
    const total = money(product.price * n);
    if (totalLabel) totalLabel.textContent = total;
    addButton?.setAttribute('aria-label', `Add ${unitLabel(n)} of ${product.name} to cart, ${total}`);
    if (bar) {
      bar.querySelector('[data-bar-qty]').textContent = unitLabel(n);
      bar.querySelector('[data-bar-total]').textContent = total;
      barAdd?.setAttribute('aria-label', `Add ${unitLabel(n)} of ${product.name} to cart, ${total}`);
    }
  };
  radios.forEach(radio => radio.addEventListener('change', syncQuantity));
  syncQuantity();

  /* ----- Add to cart through the shared basket in products.js ----- */
  const setStatus = (html, state = '') => {
    if (!status) return;
    status.dataset.state = state;
    status.innerHTML = html;
  };
  let inCart = 0;
  const idleLabel = () => (inCart ? 'Add more' : 'Add to cart');
  const add = async () => {
    if (!addButton || addButton.disabled || !window.mayleneCart) return;
    const n = quantity();
    addButton.disabled = true;
    if (barAdd) barAdd.disabled = true;
    addButton.setAttribute('aria-busy', 'true');
    addLabel.textContent = 'Adding…';
    try {
      const added = await window.mayleneCart.add(product.handle, n);
      if (added) setStatus(`${unitLabel(n)} added to your cart. <a href="/checkout">Checkout</a>`);
    } catch {
      setStatus('The store cart is unavailable right now. Please try again in a moment.', 'error');
    } finally {
      addButton.disabled = false;
      if (barAdd) barAdd.disabled = false;
      addButton.removeAttribute('aria-busy');
      addLabel.textContent = idleLabel();
    }
  };
  addButton?.addEventListener('click', add);
  barAdd?.addEventListener('click', add);

  // Show how many of this product the basket already holds.
  document.addEventListener('maylene:cart', event => {
    const items = event.detail.cart?.items || [];
    inCart = items.filter(item => item.variant_id === product.variantId).reduce((sum, item) => sum + item.quantity, 0);
    if (addLabel && !addButton.hasAttribute('aria-busy')) addLabel.textContent = idleLabel();
    if (inCart && !status?.textContent) setStatus(`${unitLabel(inCart)} already in your cart.`);
    if (!inCart && status.dataset.state !== 'error') setStatus('');
  });

  /* ----- Sticky buy bar once the main button scrolls out of view ----- */
  if (bar && addButton) {
    const footer = document.querySelector('.footer');
    const cart = document.getElementById('floating-cart');
    let scheduled = false;
    const update = () => {
      scheduled = false;
      const pastButton = addButton.getBoundingClientRect().bottom < 0;
      const footerVisible = footer ? footer.getBoundingClientRect().top < window.innerHeight : false;
      const show = pastButton && !footerVisible && (!cart || cart.hidden);
      if (bar.hidden === !show) return;
      bar.hidden = !show;
      bar.inert = !show;
      document.body.classList.toggle('pdp-bar-on', show);
    };
    const schedule = () => { if (!scheduled) { scheduled = true; requestAnimationFrame(update); } };
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    if (cart) new MutationObserver(schedule).observe(cart, { attributes: true, attributeFilter: ['hidden'] });
    update();
  }

  // Lab report links open the report panel and move focus there.
  document.querySelectorAll('a[href="#lab-reports"]').forEach(link => link.addEventListener('click', () => {
    requestAnimationFrame(() => document.getElementById('lab-reports')?.focus({ preventScroll: true }));
  }));
})();
