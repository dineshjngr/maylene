(() => {
  const buttons = [...document.querySelectorAll('[data-favorite]')];
  if (!buttons.length) return;
  const status = document.getElementById('favorites-status');
  let pending = false;
  const catalog = fetch('/redesign/favorites-data.json').then(response => {
    if (!response.ok) throw new Error('Catalog unavailable');
    return response.json();
  });
  // Same server-side cart transport and storage key as the original store.
  async function request(path, method = 'GET', body) {
    const response = await fetch('/api/cart', {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, method, ...(body ? { body } : {}) }),
      signal: AbortSignal.timeout(30000)
    });
    const result = await response.json();
    if (!response.ok) throw new Error('Cart request failed');
    return result;
  }
  buttons.forEach(button => button.addEventListener('click', async () => {
    if (pending) return;
    pending = true;
    buttons.forEach(item => { item.disabled = true; });
    const label = button.querySelector('span');
    const fallback = button.parentElement.querySelector('.favorite__fallback');
    label.textContent = 'Adding…';
    button.setAttribute('aria-busy', 'true');
    status.textContent = '';
    try {
      const data = await catalog;
      const product = data.products.find(item => item.handle === button.dataset.favorite);
      if (!product) throw new Error('Product unavailable');
      if (!product.variantId) {
        window.location.assign(`${product.url}#order-module`);
        return;
      }
      let cartId = localStorage.getItem('medusa-cart-id');
      if (cartId) {
        const result = await request(`/store/carts/${encodeURIComponent(cartId)}`);
        if (!result.cart || result.cart.completed_at) throw new Error('Cart unavailable');
      } else {
        const result = await request('/store/carts', 'POST', { region_id: data.regionId });
        cartId = result.cart?.id;
        if (!cartId) throw new Error('Cart unavailable');
        localStorage.setItem('medusa-cart-id', cartId);
      }
      const result = await request(`/store/carts/${encodeURIComponent(cartId)}/line-items`, 'POST', {
        variant_id: product.variantId, quantity: 1
      });
      if (!result.cart?.items?.some(item => item.variant_id === product.variantId)) {
        throw new Error('Item not confirmed');
      }
      label.textContent = 'Added to cart';
      status.textContent = `${product.name} added to your cart.`;
      fallback.textContent = 'View your cart →';
      fallback.href = '/cart';
      fallback.hidden = false;
      window.dispatchEvent(new CustomEvent('medusa-cart-sync', { detail: { cartId } }));
    } catch {
      label.textContent = 'Add to cart';
      status.textContent = 'The store cart is unavailable. Open the product page to select options and order.';
      fallback.hidden = false;
    } finally {
      pending = false;
      buttons.forEach(item => { item.disabled = false; });
      button.removeAttribute('aria-busy');
    }
  }));
})();
