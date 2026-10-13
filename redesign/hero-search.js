// Typing suggestions in the hero search placeholder only; the typed value is never touched.
(() => {
  const input = document.querySelector('.hero__field input[type="search"]');
  if (!input) return;
  const fallback = input.placeholder;
  const suggestions = ['Retatrutide', 'Tirzepatide', 'BPC-157', 'TB-500', 'GHK-Cu', 'NAD+', 'Cagrilintide', 'MOTS-c', 'Somatropin', 'Melanotan II', 'Retatrutide 20mg pen', 'BPC-157 + TB-500 bundle', 'Weight-loss research', 'Healing peptides', 'Certificates of analysis'];
  const shuffle = () => { for (let i = suggestions.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [suggestions[i], suggestions[j]] = [suggestions[j], suggestions[i]]; } };
  shuffle();
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  let timer = 0, index = 0, length = 0, deleting = false, visible = true;
  const stop = () => { clearTimeout(timer); timer = 0; };
  const allowed = () => visible && !document.hidden && !motion.matches && document.activeElement !== input && !input.value;
  function step() {
    stop();
    if (!allowed()) return;
    const phrase = suggestions[index];
    length += deleting ? -1 : 1;
    input.placeholder = `Search ${phrase.slice(0, length)}${length === phrase.length ? '…' : ''}`;
    let delay = deleting ? 18 : 85;
    if (!deleting && length === phrase.length) { deleting = true; delay = 1800; }
    else if (deleting && length === 0) { deleting = false; index = (index + 1) % suggestions.length; if (index === 0) shuffle(); delay = 350; }
    timer = setTimeout(step, delay);
  }
  function sync() {
    stop();
    input.placeholder = fallback;
    index = 0; length = 0; deleting = false;
    if (allowed()) timer = setTimeout(step, 650);
  }
  ['focus', 'blur', 'input'].forEach(type => input.addEventListener(type, sync));
  document.addEventListener('visibilitychange', sync);
  motion.addEventListener('change', sync);
  if ('IntersectionObserver' in window) new IntersectionObserver(entries => { visible = entries[0].isIntersecting; sync(); }).observe(input);
  sync();
})();
