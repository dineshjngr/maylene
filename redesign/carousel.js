// Featured products carousel: native scroll-snap track with arrow buttons.
(() => {
  document.querySelectorAll('[data-carousel]').forEach(root => {
    const track = root.querySelector('.carousel__track');
    const section = root.closest('section');
    const prev = section.querySelector('[data-carousel-prev]');
    const next = section.querySelector('[data-carousel-next]');
    if (!track || !prev || !next) return;
    const step = () => { const card = track.querySelector('.card'); const gap = parseFloat(getComputedStyle(track).columnGap || getComputedStyle(track).gap) || 0; return card ? card.getBoundingClientRect().width + gap : track.clientWidth; };
    const behavior = () => matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth';
    const page = () => Math.max(1, Math.round(track.clientWidth / step())) * step();
    const update = () => {
      const max = track.scrollWidth - track.clientWidth - 1;
      prev.disabled = track.scrollLeft <= 8;
      next.disabled = track.scrollLeft >= max;
      root.classList.toggle('carousel--start', prev.disabled);
      root.classList.toggle('carousel--end', next.disabled);
    };
    const go = dir => { track.scrollBy({left: dir * page(), behavior: behavior()}); setTimeout(update, 60); setTimeout(update, 500); };
    prev.addEventListener('click', () => go(-1));
    next.addEventListener('click', () => go(1));
    track.addEventListener('scroll', update, {passive: true});
    track.addEventListener('scrollend', update);
    track.addEventListener('keydown', e => { if (e.key === 'ArrowRight') { e.preventDefault(); next.click(); } if (e.key === 'ArrowLeft') { e.preventDefault(); prev.click(); } });
    addEventListener('resize', update);
    update();
  });
})();
