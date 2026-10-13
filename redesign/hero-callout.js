// Pins the product callout to the pen in the hero banner, whatever crop the viewport produces.
(() => {
  const hero = document.querySelector('.hero');
  const img = hero?.querySelector('.hero__bg');
  const callout = hero?.querySelector('.hero__callout');
  if (!hero || !img || !callout) return;
  const PEN = {x: 0.799, y: 0.285}; // fraction of the banner where the dot sits
  const pct = (v, size) => {
    const k = {left: 0, top: 0, center: 50, right: 100, bottom: 100};
    if (v in k) return k[v] / 100 * size;
    if (v.endsWith('%')) return parseFloat(v) / 100 * size;
    return parseFloat(v) || 0;
  };
  function place() {
    if (!img.naturalWidth || getComputedStyle(callout).display === 'none') return;
    const h = hero.getBoundingClientRect(), b = img.getBoundingClientRect();
    const cs = getComputedStyle(img);
    const iw = img.naturalWidth, ih = img.naturalHeight;
    const s = cs.objectFit === 'cover' ? Math.max(b.width / iw, b.height / ih) : Math.min(b.width / iw, b.height / ih);
    const rw = iw * s, rh = ih * s;
    const [px = 'center', py = 'center'] = cs.objectPosition.split(/\s+/);
    const ox = b.left - h.left + pct(px, b.width - rw);
    const oy = b.top - h.top + pct(py, b.height - rh);
    const x = ox + PEN.x * rw, y = oy + PEN.y * rh;
    const inside = x > 0 && x < h.width && y > 0 && y < h.height;
    callout.style.setProperty('--dot-x', x + 'px');
    callout.style.setProperty('--dot-y', y + 'px');
    // Beside the pen when there is room to its right, otherwise above it.
    const cardW = callout.querySelector('.hero__callout-card').offsetWidth || 250;
    const side = h.width - 14 - x >= cardW + 26;
    callout.classList.toggle('hero__callout--side', side);
    callout.style.setProperty('--card-right', Math.min(250, h.width - 14 - x) + 'px');
    callout.classList.toggle('hero__callout--ready', inside);
  }
  img.complete ? place() : img.addEventListener('load', place, {once: true});
  addEventListener('resize', place);
  if ('ResizeObserver' in window) new ResizeObserver(place).observe(hero);
})();
