(() => {
  const header = document.querySelector('.header');
  if (!header) return;
  const burger = header.querySelector('.burger');
  const groups = [...header.querySelectorAll('.nav__group')];
  const mobile = matchMedia('(max-width:900px)');
  const hover = matchMedia('(hover:hover) and (pointer:fine)');
  header.setAttribute('data-menu-ready', '');
  const closeGroups = except => groups.forEach(group => {
    if (group !== except) group.open = false;
  });
  const setMenu = open => {
    header.classList.toggle('header--menu-open', open);
    burger.setAttribute('aria-expanded', String(open));
    burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    if (!open) closeGroups();
  };
  burger.addEventListener('click', () => setMenu(burger.getAttribute('aria-expanded') !== 'true'));
  groups.forEach(group => {
    const summary = group.querySelector('summary');
    group.addEventListener('toggle', () => { if (group.open) closeGroups(group); });
    group.addEventListener('pointerenter', () => {
      if (!mobile.matches && hover.matches) { closeGroups(group); group.open = true; }
    });
    group.addEventListener('pointerleave', () => {
      if (!mobile.matches && hover.matches && !group.contains(document.activeElement)) group.open = false;
    });
    group.addEventListener('focusout', event => {
      if (!group.contains(event.relatedTarget)) group.open = false;
    });
    summary.addEventListener('keydown', event => {
      if (!['ArrowDown', 'ArrowUp'].includes(event.key)) return;
      event.preventDefault();
      closeGroups(group);
      group.open = true;
      const links = [...group.querySelectorAll('a')];
      (event.key === 'ArrowUp' ? links.at(-1) : links[0])?.focus();
    });
  });
  document.addEventListener('click', event => {
    if (!header.contains(event.target)) setMenu(false);
  });
  header.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const openGroup = groups.find(group => group.open);
    if (openGroup) { openGroup.open = false; openGroup.querySelector('summary').focus(); }
    else if (mobile.matches) { setMenu(false); burger.focus(); }
  });
  header.querySelector('.nav').addEventListener('click', event => {
    if (event.target.closest('a')) setMenu(false);
  });
  mobile.addEventListener('change', () => setMenu(false));
  const account = header.querySelector('.header__account');
  if (account) {
    account.addEventListener('pointerenter', () => { if (hover.matches) account.open = true; });
    account.addEventListener('pointerleave', () => { if (hover.matches && !account.contains(document.activeElement)) account.open = false; });
    account.addEventListener('focusout', event => { if (!account.contains(event.relatedTarget)) account.open = false; });
    account.addEventListener('keydown', event => {
      if (event.key === 'Escape') { account.open = false; account.querySelector('summary').focus(); event.stopPropagation(); }
      if (event.target === account.querySelector('summary') && ['ArrowDown', 'ArrowUp'].includes(event.key)) {
        event.preventDefault(); account.open = true;
        const links = [...account.querySelectorAll('a')];
        (event.key === 'ArrowUp' ? links.at(-1) : links[0])?.focus();
      }
    });
    document.addEventListener('click', event => { if (!account.contains(event.target)) account.open = false; });
  }
})();
