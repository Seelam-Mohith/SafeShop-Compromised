// Shopping cart functionality using localStorage
const CART_KEY = 'shopsafe_cart';

function getCart() {
    try {
        const cart = localStorage.getItem(CART_KEY);
        return cart ? JSON.parse(cart) : [];
    } catch (e) {
        return [];
    }
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

function addToCart(productId, quantity) {
    const cart = getCart();
    const qty = parseInt(quantity) || 1;
    const existing = cart.find(item => item.id == productId);
    if (existing) {
        existing.quantity += qty;
    } else {
        cart.push({ id: parseInt(productId), quantity: qty });
    }
    saveCart(cart);
    alert('Product added to cart');
}

function updateCartQuantity(productId, quantity) {
    const cart = getCart();
    const qty = parseInt(quantity);
    if (isNaN(qty) || qty <= 0) {
        removeFromCart(productId);
        return;
    }
    const item = cart.find(item => item.id == productId);
    if (item) {
        item.quantity = qty;
        saveCart(cart);
    }
}

function removeFromCart(productId) {
    let cart = getCart();
    cart = cart.filter(item => item.id != productId);
    saveCart(cart);
    window.location.reload();
}

// Initialize add to cart buttons
document.addEventListener('DOMContentLoaded', function() {
    const addToCartBtns = document.querySelectorAll('.add-to-cart-btn');
    addToCartBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            const qtyInput = document.getElementById('quantity');
            const qty = qtyInput ? qtyInput.value : 1;
            addToCart(productId, qty);
        });
    });
});
