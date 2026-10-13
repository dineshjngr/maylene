// Client-side search, filters and sorting for the product listing.
(() => {
  const grid = document.getElementById('plp-grid');
  if (!grid) return;
  const cards = [...grid.querySelectorAll('.card')];
  const q = document.getElementById('plp-q');
  const clear = document.getElementById('plp-clear');
  const chips = [...document.querySelectorAll('.chip[data-category]')];
  const sort = document.getElementById('plp-sort');
  const boxes = [...document.querySelectorAll('.plp__check input')];
  const count = document.getElementById('plp-count');
  const empty = document.getElementById('plp-empty');
  const filters = document.getElementById('plp-filters');
  const toggle = document.getElementById('plp-filters-toggle');
  let category = '';
  const norm = s => (s || '').toLowerCase().replace(/[‑–-]/g, '-').replace(/\s+/g, ' ').trim();
  function apply() {
    const term = norm(q.value);
    const areas = boxes.filter(b => b.name === 'area' && b.checked).map(b => b.value);
    const prices = boxes.filter(b => b.name === 'price' && b.checked).map(b => b.value.split('-').map(Number));
    let shown = 0;
    cards.forEach(card => {
      const d = card.dataset, price = Number(d.price);
      let ok = !category || d.category === category;
      if (ok && areas.length) ok = areas.includes(d.area);
      if (ok && prices.length) ok = prices.some(([lo, hi]) => price >= lo && price <= hi);
      if (ok && term) ok = norm(d.name + ' ' + d.area + ' ' + d.category + ' ' + card.querySelector('.card__description').textContent).includes(term);
      card.hidden = !ok; if (ok) shown++;
    });
    const by = sort.value;
    const sorted = [...cards].sort((a, b) => {
      if (by === 'price-asc') return a.dataset.price - b.dataset.price;
      if (by === 'price-desc') return b.dataset.price - a.dataset.price;
      if (by === 'name') return a.dataset.name.localeCompare(b.dataset.name);
      return a.dataset.order - b.dataset.order;
    });
    sorted.forEach(c => grid.append(c));
    count.textContent = `${shown} ${shown === 1 ? 'product' : 'products'}${term ? ` for “${q.value.trim()}”` : ''}`;
    empty.hidden = shown > 0;
    clear.hidden = !q.value;
    const active = boxes.filter(b => b.checked).length;
    toggle.textContent = ''; toggle.insertAdjacentHTML('beforeend', '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M7 12h10M10 18h4"/></svg>Filters' + (active ? ` (${active})` : ''));
    const url = new URL(location); term ? url.searchParams.set('q', q.value.trim()) : url.searchParams.delete('q'); category ? url.searchParams.set('category', category) : url.searchParams.delete('category');
    history.replaceState(null, '', url);
  }
  const reset = () => { boxes.forEach(b => b.checked = false); category = ''; chips.forEach(c => c.classList.toggle('is-active', !c.dataset.category)); q.value = ''; sort.value = 'featured'; apply(); };
  q.addEventListener('input', apply);
  document.getElementById('plp-search').addEventListener('submit', e => { e.preventDefault(); apply(); });
  clear.addEventListener('click', () => { q.value = ''; apply(); q.focus(); });
  chips.forEach(chip => chip.addEventListener('click', () => { category = chip.dataset.category; chips.forEach(c => c.classList.toggle('is-active', c === chip)); apply(); }));
  sort.addEventListener('change', apply);
  boxes.forEach(b => b.addEventListener('change', apply));
  document.getElementById('plp-reset').addEventListener('click', reset);
  document.getElementById('plp-empty-reset').addEventListener('click', reset);
  toggle.addEventListener('click', () => { const open = filters.classList.toggle('is-open'); toggle.setAttribute('aria-expanded', String(open)); });
  const params = new URLSearchParams(location.search);
  if (params.get('q')) q.value = params.get('q');
  const cat = params.get('category'); if (cat) { category = cat; chips.forEach(c => c.classList.toggle('is-active', c.dataset.category === cat)); }
  apply();
})();
