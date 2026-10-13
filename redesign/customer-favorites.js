(() => {
  const section = document.getElementById('customer-favorites');
  if (!section) return;
  const cards = [...section.querySelectorAll('[data-favorite-product]')];
  const storageKey = 'medusa-cart-id';
  const ukRegion = 'reg_01M48X2PHWNXD1NSM7R83Y6XNG';
  const currency = new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' });
  let cartId = null;
  let queue = Promise.resolve();
  try { cartId = localStorage.getItem(storageKey); } catch {}
  if (cartId && !/^cart_[A-Za-z0-9_-]+$/.test(cartId)) cartId = null;

  // Match the original storefront's guest-cart transport and storage contract.
  const cartRequest = async (path, method = 'GET', body) => {
    const response = await fetch('/api/cart', {
      method: 'POST', credentials: 'same-origin', cache: 'no-store',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, method, ...(body === undefined ? {} : { body }) }),
      signal: AbortSignal.timeout(30000)
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const error = new Error(data?.message || 'Your basket could not be updated. Please try again.');
      error.status = response.status;
      throw error;
    }
    return data;
  };

  const rememberCart = id => {
    cartId = id;
    try { localStorage.setItem(storageKey, id); } catch {}
    try {
      const channel = new BroadcastChannel('medusa-cart-sync');
      channel.postMessage({ type: 'cart-updated', cartId: id });
      channel.close();
    } catch {}
  };

  const ensureCart = async () => {
    if (cartId) {
      try {
        const { cart } = await cartRequest(`/store/carts/${cartId}`);
        if (cart?.id && !cart.completed_at && !['complete', 'completed'].includes(cart.status)) return cart.id;
        cartId = null;
      } catch (error) {
        // Expired or completed baskets need a fresh guest basket. Other failures
        // remain errors; they never produce a simulated success state.
        if (error.status === 404) cartId = null;
        else throw error;
      }
    }
    const { cart } = await cartRequest('/store/carts', 'POST', { region_id: ukRegion });
    if (!cart?.id) throw new Error('Your basket could not be created. Please try again.');
    rememberCart(cart.id);
    return cart.id;
  };

  const showError = card => {
    const feedback = card.querySelector('.favorites__feedback');
    feedback.replaceChildren(document.createTextNode('Unable to add. '));
    const link = document.createElement('a');
    link.href = card.dataset.productUrl;
    link.textContent = 'Open product';
    feedback.append(link);
  };

  cards.forEach(card => {
    const button = card.querySelector('.favorites__add');
    const label = button.querySelector('span');
    button.addEventListener('click', async () => {
      if (button.disabled) return;
      if (card.dataset.requiresOptions === 'true') {
        window.location.assign(card.dataset.productUrl);
        return;
      }
      button.disabled = true;
      button.setAttribute('aria-busy', 'true');
      label.textContent = 'Adding…';
      card.querySelector('.favorites__feedback').textContent = '';
      const operation = queue.then(async () => {
        const id = await ensureCart();
        const { cart } = await cartRequest(`/store/carts/${id}/line-items`, 'POST', {
          variant_id: card.dataset.variantId, quantity: 1
        });
        if (!cart?.id || !cart.items?.some(item => item.variant_id === card.dataset.variantId)) {
          throw new Error('The basket update could not be confirmed.');
        }
        rememberCart(cart.id);
      });
      queue = operation.catch(() => {});
      try {
        await operation;
        label.textContent = 'Added to cart';
        card.querySelector('.favorites__feedback').textContent = 'Added to your basket.';
      } catch {
        label.textContent = 'Add to cart';
        showError(card);
      } finally {
        button.disabled = false;
        button.removeAttribute('aria-busy');
      }
    });
  });

  // Refresh the server-rendered catalog prices and variants without blocking
  // image loading or changing the selected product order.
  const refreshCatalog = async () => {
    try {
      const response = await fetch(`/api/catalogue?resource=products&limit=100&region_id=${ukRegion}`, {
        credentials: 'omit', cache: 'no-store', signal: AbortSignal.timeout(15000)
      });
      if (!response.ok) return;
      const data = await response.json();
      if (!Array.isArray(data.products)) return;
      cards.forEach(card => {
        const product = data.products.find(item => item.handle === card.dataset.favoriteProduct);
        if (!product) return;
        const variant = product.variants?.find(item => item.id === card.dataset.variantId);
        if (!variant) { card.dataset.requiresOptions = 'true'; return; }
        const price = variant.calculated_price;
        if (price?.currency_code !== 'gbp' || !Number.isFinite(price.calculated_amount)) return;
        card.dataset.requiresOptions = String(product.variants.length !== 1);
        card.querySelector('.favorites__name a').textContent = product.title;
        card.querySelector('.favorites__current').textContent = currency.format(price.calculated_amount);
        const priceRow = card.querySelector('.favorites__price');
        priceRow.querySelector('.favorites__original')?.remove();
        if (Number.isFinite(price.original_amount) && price.original_amount > price.calculated_amount) {
          const original = document.createElement('s');
          original.className = 'favorites__original';
          original.textContent = currency.format(price.original_amount);
          priceRow.prepend(original);
        }
        if (variant.manage_inventory && !variant.allow_backorder && variant.inventory_quantity <= 0) {
          const button = card.querySelector('.favorites__add');
          button.disabled = true;
          button.setAttribute('aria-disabled', 'true');
          button.querySelector('span').textContent = 'Out of stock';
        }
      });
    } catch {
      // The initial content contains verified catalog prices, so browsing remains
      // available when a live refresh fails. The cart always checks the backend.
    }
  };
  refreshCatalog();
})();
