// Define showCustomAlert if not already defined
function showCustomAlert(message, className) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${className}`;
    alertDiv.textContent = message;
    document.body.prepend(alertDiv);
    setTimeout(() => alertDiv.remove(), 3000);
}

document.addEventListener('DOMContentLoaded', () => {
    let cartItems = [];
    let selectedItems = [];
    try {
        cartItems = JSON.parse(localStorage.getItem('cartItems') || '[]');
        selectedItems = JSON.parse(localStorage.getItem('selectedItems') || '[]');
    } catch (e) {
        console.error('Error parsing localStorage:', e);
    }

    const orderSummary = document.getElementById('order-summary');
    const subtotalElement = document.getElementById('subtotal');
    const orderTotalElement = document.getElementById('order-total');
    const emptyCartMessage = document.getElementById('empty-cart-message');
    const checkoutContent = document.getElementById('checkout-content');
    const placeOrderBtn = document.getElementById('place-order-btn');
    const shippingForm = document.getElementById('shipping-form');
    const paymentForm = document.getElementById('payment-form');

    if (!orderSummary || !subtotalElement || !orderTotalElement || !emptyCartMessage || !checkoutContent || !placeOrderBtn || !shippingForm || !paymentForm) {
        console.error('One or more DOM elements not found');
        return;
    }

    let hasShownFormFilledAlert = false;
    const itemsToCheckout = cartItems.filter(item => selectedItems.includes(item.id));

    if (itemsToCheckout.length === 0) {
        emptyCartMessage.style.display = 'block';
        checkoutContent.style.display = 'none';
        placeOrderBtn.disabled = true;
    } else {
        emptyCartMessage.style.display = 'none';
        checkoutContent.style.display = 'flex';
        let subtotal = 0;

        itemsToCheckout.forEach(item => {
            const itemTotal = item.price * item.quantity;
            subtotal += itemTotal;

            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.name}</td>
                <td>$${item.price.toFixed(2)}</td>
                <td>${item.quantity}</td>
                <td>$${itemTotal.toFixed(2)}</td>
            `;
            orderSummary.appendChild(row);
        });

        const shipping = 5.00;
        const total = subtotal + shipping;

        subtotalElement.textContent = subtotal.toFixed(2);
        orderTotalElement.textContent = total.toFixed(2);
    }

    function validateForms() {
        const shippingValid = shippingForm.checkValidity();
        const paymentValid = paymentForm.checkValidity();
        const formsValid = shippingValid && paymentValid && itemsToCheckout.length > 0;
        console.log('Shipping valid:', shippingValid, 'Payment valid:', paymentValid, 'Items:', itemsToCheckout.length);
        placeOrderBtn.disabled = !formsValid;

        if (formsValid && !hasShownFormFilledAlert) {
            showCustomAlert('All forms are filled! You can now place your order.', 'info my-2');
            hasShownFormFilledAlert = true;
        } else if (!formsValid) {
            hasShownFormFilledAlert = false;
        }
    }

    shippingForm.addEventListener('input', () => {
        console.log('Shipping form input detected');
        validateForms();
    });
    paymentForm.addEventListener('input', () => {
        console.log('Payment form input detected');
        validateForms();
    });

    document.getElementById('cardNumber').addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        value = value.replace(/(.{4})/g, '$1 ').trim();
        e.target.value = value.slice(0, 19);
    });

    document.getElementById('expiryDate').addEventListener('input', (e) => {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length >= 2) {
            value = value.slice(0, 2) + '/' + value.slice(2);
        }
        e.target.value = value.slice(0, 5);
    });

    placeOrderBtn.addEventListener('click', () => {
        if (shippingForm.checkValidity() && paymentForm.checkValidity()) {
            const remainingItems = cartItems.filter(item => !selectedItems.includes(item.id));
            localStorage.setItem('cartItems', JSON.stringify(remainingItems));
            localStorage.removeItem('selectedItems');
            showCustomAlert('Order placed successfully! Thank you for shopping with SMOS.', 'success my-2');
            hasShownFormFilledAlert = false;
            shippingForm.reset();
            paymentForm.reset();
            window.location.href = './index.html';
        }
    });

    validateForms();
    try {
        AOS.init({ duration: 800, once: true });
    } catch (e) {
        console.error('AOS initialization failed:', e);
    }
});