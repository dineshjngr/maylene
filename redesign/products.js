(() => {
  const storageKey = 'maylene-featured-wishlist';
  let saved = new Set();
  try {
    const stored = JSON.parse(localStorage.getItem(storageKey) || '[]');
    if (Array.isArray(stored)) saved = new Set(stored.filter(item => typeof item === 'string'));
  } catch {}

  const update = button => {
    const selected = saved.has(button.dataset.product);
    button.setAttribute('aria-pressed', String(selected));
    button.setAttribute('aria-label', selected
      ? `Remove ${button.dataset.name} from wishlist`
      : `Save ${button.dataset.name} to wishlist`);
  };

  document.querySelectorAll('.card__wishlist, [data-wishlist]').forEach(button => {
    update(button);
    button.addEventListener('click', () => {
      const product = button.dataset.product;
      if (saved.has(product)) saved.delete(product);
      else saved.add(product);
      try { localStorage.setItem(storageKey, JSON.stringify([...saved])); } catch {}
      update(button);
      const status = document.getElementById('wishlist-status');
      if (status) status.textContent = `${button.dataset.name} ${saved.has(product) ? 'saved to' : 'removed from'} wishlist.`;
    });
  });

  const popup = document.getElementById('floating-cart');
  const toggle = popup.querySelector('.floating-cart__toggle');
  const details = document.getElementById('floating-cart-details');
  const list = document.getElementById('floating-cart-items');
  const feedback = document.getElementById('cart-feedback');
  const cartLink = document.querySelector('.icons a[aria-label="Cart"]');
  const addButtons = [...document.querySelectorAll('.card__add')];
  const cardControls = new Map();
  addButtons.forEach(button => {
    const actions = document.createElement('div');
    actions.className = 'card__actions';
    button.before(actions);
    actions.append(button);
    const stepper = document.createElement('div');
    stepper.className = 'card__stepper';
    stepper.hidden = true;
    stepper.setAttribute('role', 'group');
    stepper.setAttribute('aria-label', `Quantity of ${button.dataset.name}`);
    const amount = document.createElement('output');
    amount.setAttribute('aria-live', 'polite');
    const minus = document.createElement('button');
    const plus = document.createElement('button');
    for (const [control, text, delta] of [[minus, '−', -1], [plus, '+', 1]]) {
      control.type = 'button';
      control.textContent = text;
      control.dataset.quantity = '';
      control.setAttribute('aria-label', `${delta < 0 ? 'Decrease' : 'Increase'} quantity of ${button.dataset.name}`);
      control.addEventListener('click', async () => {
        if (busy) return;
        const data = await dataPromise;
        const product = data.products.find(item => item.handle === button.dataset.product);
        const item = cart?.items?.find(item => item.variant_id === product?.variantId);
        if (item) await change(item, delta);
      });
    }
    stepper.append(minus, amount, plus);
    actions.append(stepper);
    cardControls.set(button, { actions, stepper, amount, minus, plus });
  });
  const dataPromise = fetch('/redesign/cart-products.json').then(r => { if (!r.ok) throw Error('Catalog unavailable'); return r.json(); });
  let cart = null, busy = false, pinned = false, hovering = false;
  const currency = () => cart?.currency_code || 'gbp';
  const money = value => new Intl.NumberFormat('en-GB', {style:'currency',currency:currency().toUpperCase()}).format(value || 0);
  const expand = () => {
    const open = pinned || hovering || popup.contains(document.activeElement) && document.activeElement !== toggle;
    popup.classList.toggle('floating-cart--expanded',open);
    toggle.setAttribute('aria-expanded',String(open));
    details.inert = !open;
  };
  toggle.addEventListener('click', () => { pinned = !pinned; expand(); });
  popup.addEventListener('pointerenter', event => { if (event.pointerType === 'mouse') { hovering=true; expand(); } });
  popup.addEventListener('pointerleave', () => { hovering=false; expand(); });
  popup.addEventListener('focusin', expand);
  popup.addEventListener('focusout', () => queueMicrotask(expand));
  const dismiss = () => { popup.hidden=true; pinned=false; hovering=false; expand(); };
  popup.querySelector('.floating-cart__close').addEventListener('click',dismiss);
  popup.addEventListener('keydown', event => { if (event.key==='Escape') { dismiss(); cartLink?.focus(); } });
  // The site's /api/cart wrapper signs basket access cookies; the preview server relays it to the live site.
  async function request(path, method='GET', body) {
    const r = await fetch('/api/cart', {method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify({path,method,...(body ? {body} : {})}),signal:AbortSignal.timeout(30000)});
    const data = await r.json().catch(() => ({}));
    if (!r.ok || !data.cart) throw Error('Cart unavailable');
    return data.cart;
  }
  function lock(value) {
    busy=value;
    addButtons.forEach(button => button.disabled=value);
    cardControls.forEach(({minus,plus}) => { minus.disabled=value; plus.disabled=value; });
    popup.querySelectorAll('[data-quantity]').forEach(button => button.disabled=value);
    popup.setAttribute('aria-busy',String(value));
  }
  async function render() {
    const data = await dataPromise;
    const items = cart?.items || [];
    const count = items.reduce((n,item)=>n+item.quantity,0);
    document.getElementById('floating-cart-title').textContent='Your cart';
    document.getElementById('floating-cart-count').textContent=`${items.length} ${items.length===1?'product':'products'} · ${count} ${count===1?'item':'items'}`;
    document.getElementById('floating-cart-total').textContent=money(cart.total ?? items.reduce((sum,item)=>sum+item.unit_price*item.quantity,0));
    if(cartLink) { cartLink.setAttribute('aria-label',`Cart, ${count} items`); const badge=cartLink.querySelector('.header__cart-count'); if(badge)badge.textContent=String(count); }
    addButtons.forEach(button => {
      const product=data.products.find(product=>product.handle===button.dataset.product);
      const quantity=items.filter(item=>item.variant_id===product?.variantId).reduce((sum,item)=>sum+item.quantity,0);
      const controls=cardControls.get(button);
      controls.stepper.hidden=quantity===0;
      controls.actions.classList.toggle('card__actions--active',quantity>0);
      controls.amount.textContent=String(quantity);
      controls.amount.setAttribute('aria-label',`Quantity ${quantity}`);
      button.querySelector('span').textContent=quantity>0?'Add more':'Add to cart';
      button.setAttribute('aria-label',`${quantity>0?'Add another':'Add'} ${button.dataset.name}${quantity>0?'':' to cart'}`);
    });
    document.dispatchEvent(new CustomEvent('maylene:cart', {detail:{cart, products:data.products}}));
    list.replaceChildren();
    items.forEach(item => {
      const product=data.products.find(p=>p.variantId===item.variant_id);
      const row=document.createElement('li');row.className='floating-cart__item';
      const image=document.createElement('img');image.src=product?.image || '/branding/maylene-wordmark-ocean-blue.svg';image.alt=product?.name || item.title;image.width=72;image.height=72;
      const info=document.createElement('div');info.className='floating-cart__product';
      const name=document.createElement('a');name.textContent=product?.name || item.title;name.href=product?.url || '/products';
      const variant=document.createElement('small');variant.textContent=`Variant: ${product?.variant || item.variant_title || 'Selected variant'}`;
      const quantity=document.createElement('div');quantity.className='floating-cart__quantity';
      for(const [label,delta] of [['−',-1],['+',1]]) {
        const button=document.createElement('button');button.type='button';button.textContent=label;button.dataset.quantity='';button.setAttribute('aria-label',`${delta<0?'Decrease':'Increase'} quantity of ${name.textContent}`);
        button.addEventListener('click',()=>change(item,delta));
        quantity.append(button);
        if(delta===-1){const amount=document.createElement('span');amount.textContent=String(item.quantity);amount.setAttribute('aria-label',`Quantity ${item.quantity}`);quantity.append(amount);}
      }
      info.append(name,variant,quantity);
      const price=document.createElement('strong');price.className='floating-cart__line-price';price.textContent=money(item.total ?? item.unit_price*item.quantity);
      row.append(image,info,price);list.append(row);
    });
    if(!count) dismiss();
  }
  async function change(item,delta) {
    if(busy)return;
    lock(true);
    try {
      cart=await request(`/store/carts/${encodeURIComponent(cart.id)}`);
      const current=cart.items.find(entry=>entry.id===item.id);
      if(!current) { await render(); return; }
      const path=`/store/carts/${encodeURIComponent(cart.id)}/line-items/${encodeURIComponent(current.id)}`;
      if(current.quantity+delta===0) {
        // DELETE returns a wrapper; retrieve the authoritative cart after removal.
        const r=await fetch('/api/cart',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify({path,method:'DELETE'}),signal:AbortSignal.timeout(30000)});
        if(!r.ok)throw Error('Remove failed');
        cart=await request(`/store/carts/${encodeURIComponent(cart.id)}`);
      } else {
        await request(path,'POST',{quantity:current.quantity+delta});
        cart=await request(`/store/carts/${encodeURIComponent(cart.id)}`);
      }
      await render();feedback.textContent='Cart quantity updated.';
    } catch {feedback.textContent='Unable to update the cart. Please try again.';}
    finally {lock(false);}
  }
  // Adds `quantity` of a catalogue product to the live basket and opens the cart popup.
  async function addToCart(handle, quantity=1) {
    await restored;
    const data=await dataPromise;const product=data.products.find(p=>p.handle===handle);
    if(!product?.variantId){window.location.assign((product?.url || '/products')+'#order-module');return null;}
    const existingId=cart?.id || localStorage.getItem('medusa-cart-id');
    cart=existingId ? await request(`/store/carts/${encodeURIComponent(existingId)}`) : await request('/store/carts','POST',{region_id:data.regionId});
    if(cart.completed_at)cart=await request('/store/carts','POST',{region_id:data.regionId});
    localStorage.setItem('medusa-cart-id',cart.id);
    const existing=cart.items?.find(item=>item.variant_id===product.variantId);
    if(existing) await request(`/store/carts/${encodeURIComponent(cart.id)}/line-items/${encodeURIComponent(existing.id)}`,'POST',{quantity:existing.quantity+quantity});
    else await request(`/store/carts/${encodeURIComponent(cart.id)}/line-items`,'POST',{variant_id:product.variantId,quantity});
    cart=await request(`/store/carts/${encodeURIComponent(cart.id)}`);
    if(!cart.items?.some(item=>item.variant_id===product.variantId))throw Error('Item not confirmed');
    await render();popup.hidden=false;pinned=false;hovering=false;expand();
    feedback.textContent=`${quantity>1?`${quantity} × `:''}${product.name} added to your cart.`;
    return product;
  }
  // Product pages call this for their main add-to-cart button.
  window.mayleneCart={
    add:async(handle,quantity=1)=>{ if(busy)return null; lock(true); try { return await addToCart(handle,quantity); } finally { lock(false); } },
    get busy(){ return busy; }
  };
  addButtons.forEach(button => button.addEventListener('click',async()=>{
    if(busy)return;
    lock(true);const label=button.querySelector('span');label.textContent='Adding…';
    try {
      await addToCart(button.dataset.product,1);
    } catch {
      feedback.textContent='The store cart is unavailable. Open the product page to order.';
      button.closest('.card').querySelector('.card__name a').focus();
    } finally {
      label.textContent=cardControls.get(button).stepper.hidden?'Add to cart':'Add more';
      lock(false);
    }
  }));
  cartLink?.addEventListener('click',async event=>{
    event.preventDefault();if(busy)return;
    lock(true);
    try { await restored; const id=cart?.id || localStorage.getItem('medusa-cart-id');if(!id){feedback.textContent='Your cart is empty.';return;}cart=await request(`/store/carts/${encodeURIComponent(id)}`);await render();if(cart.items?.length){popup.hidden=false;pinned=true;expand();toggle.focus();} }
    catch {feedback.textContent='Unable to load your cart. Please try again.';}
    finally {lock(false);}
  });
  // Restore the header badge for a cart created on an earlier visit.
  const restored=(async()=>{ const id=localStorage.getItem('medusa-cart-id'); if(!id) return; try { cart=await request(`/store/carts/${encodeURIComponent(id)}`); if(cart.completed_at){localStorage.removeItem('medusa-cart-id');cart=null;return;} await render(); popup.hidden=true; } catch {} })();
  // Consume a catalog failure even when no cart interaction has occurred.
  dataPromise.catch(()=>{});
})();
