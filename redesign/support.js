(() => {
  const support = document.querySelector('.floating-support');
  const collection = document.querySelector('.featured-products, [data-support-anchor]');
  if (!support || !collection) return;
  let scheduled = false;
  const update = () => {
    scheduled = false;
    support.hidden = collection.getBoundingClientRect().top >= window.innerHeight;
  };
  const schedule = () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(update);
  };
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule);
  window.addEventListener('pageshow', update);
  update();
})();
