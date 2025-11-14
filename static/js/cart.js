function showCustomAlert(message, type = 'success') {
    const existingAlerts = document.querySelectorAll('.custom-alert');
    const alertDiv = document.createElement('div');
    alertDiv.className = `custom-alert alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = `${20 + (existingAlerts.length * 80)}px`;
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '1050';
    alertDiv.style.minWidth = '200px';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);
    setTimeout(() => {
        alertDiv.classList.remove('show');
        alertDiv.classList.add('fade');
        setTimeout(() => alertDiv.remove(), 300);
    }, 3000);
}

function updateCartCount() {
    fetch('/get-cart', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const cart = data.cart || [];
            const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
            document.getElementById('cart-count').textContent = totalItems;
        }
    })
    .catch(error => {
        console.error('Error updating cart count:', error);
    });
}

function updateCartDisplay() {
    const cartItemsContainer = document.getElementById('cart-items');
    const cartTable = document.getElementById('cart-table');
    const cartTotalElement = document.getElementById('cart-total');
    const emptyCartMessage = document.getElementById('empty-cart-message');
    const checkoutBtn = document.getElementById('checkout-btn');
    const checkAllCheckbox = document.getElementById('check-all');
    const placeholderImage = '/static/shop/placeholder.png';

    if (!cartItemsContainer || !cartTable || !cartTotalElement || !emptyCartMessage || !checkoutBtn || !checkAllCheckbox) {
        console.error('Required DOM elements not found');
        showCustomAlert('Error loading cart: Missing DOM elements.', 'danger');
        return;
    }

    fetch('/get-cart', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.status !== 'success') {
            throw new Error(data.message || 'Failed to fetch cart data');
        }
        const cart = data.cart || [];
        cartItemsContainer.innerHTML = '';

        if (cart.length === 0) {
            cartTable.style.display = 'none';
            emptyCartMessage.style.display = 'block';
            checkoutBtn.disabled = true;
            checkAllCheckbox.disabled = true;
            checkAllCheckbox.checked = false;
            cartTotalElement.textContent = '0.00';
            localStorage.setItem('selectedItems', JSON.stringify([]));
            updateCartCount();
            return;
        }

        cartTable.style.display = 'table';
        emptyCartMessage.style.display = 'none';
        checkAllCheckbox.disabled = false;

        let selectedItems = JSON.parse(localStorage.getItem('selectedItems') || '[]');
        cart.forEach(item => {
            if (!selectedItems.includes(item.id)) {
                selectedItems.push(item.id);
            }
        });
        localStorage.setItem('selectedItems', JSON.stringify(selectedItems));

        cart.forEach(item => {
            const isChecked = selectedItems.includes(item.id) ? 'checked' : '';
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    <input type="checkbox" class="cart-item-checkbox" data-id="${item.id}" ${isChecked} aria-label="Select ${item.name}">
                </td>
                <td>
                    <div class="d-flex align-items-center">
                        <img src="${item.image}" alt="${item.name}" style="width: 50px; height: 50px; object-fit: cover; margin-right: 10px;"
                             onerror="this.src='${placeholderImage}';">
                        <span>${item.name}</span>
                    </div>
                </td>
                <td>$${parseFloat(item.price).toFixed(2)}</td>
                <td>
                    <div class="quantity-controls d-flex justify-content-around">
                        <button class="btn btn-secondary btn-sm quantity-decrease" data-id="${item.id}" aria-label="Decrease quantity">-</button>
                        <input type="text" class="form-control quantity-input" value="${item.quantity}" min="1" data-id="${item.id}" style="width: 50px; text-align: center;" readonly>
                        <button class="btn btn-secondary btn-sm quantity-increase" data-id="${item.id}" aria-label="Increase quantity">+</button>
                    </div>
                </td>
                <td>$${(parseFloat(item.price) * item.quantity).toFixed(2)}</td>
                <td>
                    <button class="btn btn-danger btn-sm remove-item" data-id="${item.id}" data-name="${item.name}" aria-label="Remove ${item.name}">Remove</button>
                </td>
            `;
            cartItemsContainer.appendChild(row);
        });

        const updateSelectedTotal = () => {
            selectedItems = JSON.parse(localStorage.getItem('selectedItems') || '[]');
            const total = cart
                .filter(item => selectedItems.includes(item.id))
                .reduce((sum, item) => sum + parseFloat(item.price) * item.quantity, 0);
            cartTotalElement.textContent = total.toFixed(2);
            checkoutBtn.disabled = selectedItems.length === 0;
            checkAllCheckbox.checked = selectedItems.length === cart.length && cart.length > 0;
            document.getElementById('selected-items-input').value = selectedItems.join(',');
        };

        checkAllCheckbox.addEventListener('change', () => {
            const isChecked = checkAllCheckbox.checked;
            selectedItems = isChecked ? cart.map(item => item.id) : [];
            localStorage.setItem('selectedItems', JSON.stringify(selectedItems));
            document.querySelectorAll('.cart-item-checkbox').forEach(checkbox => {
                checkbox.checked = isChecked;
            });
            updateSelectedTotal();
        });

        document.querySelectorAll('.cart-item-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const productId = checkbox.dataset.id;
                if (checkbox.checked) {
                    if (!selectedItems.includes(productId)) {
                        selectedItems.push(productId);
                    }
                } else {
                    selectedItems = selectedItems.filter(id => id !== productId);
                    checkAllCheckbox.checked = false;
                }
                localStorage.setItem('selectedItems', JSON.stringify(selectedItems));
                updateSelectedTotal();
            });
        });

        document.querySelectorAll('.quantity-increase').forEach(button => {
            button.addEventListener('click', () => {
                const productId = button.dataset.id;
                const item = cart.find(item => item.id === productId);
                if (item) {
                    fetch('/update-cart-quantity', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: productId, quantity: item.quantity + 1 })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            showCustomAlert(data.message || 'Quantity increased!', 'success');
                            updateCartDisplay();
                        } else {
                            showCustomAlert(data.message || 'Error updating quantity.', 'danger');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showCustomAlert(`Error updating quantity: ${error.message}`, 'danger');
                    });
                }
            });
        });

        document.querySelectorAll('.quantity-decrease').forEach(button => {
            button.addEventListener('click', () => {
                const productId = button.dataset.id;
                const item = cart.find(item => item.id === productId);
                if (item && item.quantity > 1) {
                    fetch('/update-cart-quantity', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: productId, quantity: item.quantity - 1 })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            showCustomAlert(data.message || 'Quantity decreased!', 'success');
                            updateCartDisplay();
                        } else {
                            showCustomAlert(data.message || 'Error updating quantity.', 'danger');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showCustomAlert(`Error updating quantity: ${error.message}`, 'danger');
                    });
                } else if (item && item.quantity === 1) {
                    fetch('/remove-from-cart', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: productId })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            showCustomAlert(data.message || `${item.name} removed from cart!`, 'warning');
                            updateCartDisplay();
                        } else {
                            showCustomAlert(data.message || 'Error removing product from cart.', 'danger');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showCustomAlert(`Error removing product: ${error.message}`, 'danger');
                    });
                }
            });
        });

        document.querySelectorAll('.remove-item').forEach(button => {
            button.addEventListener('click', () => {
                const productId = button.dataset.id;
                const name = button.dataset.name;
                fetch('/remove-from-cart', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: productId })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showCustomAlert(data.message || `${name} removed from cart!`, 'warning');
                        updateCartDisplay();
                    } else {
                        showCustomAlert(data.message || 'Error removing product from cart.', 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showCustomAlert(`Error removing product: ${error.message}`, 'danger');
                });
            });
        });

        document.getElementById('checkout-form').addEventListener('submit', (e) => {
            selectedItems = JSON.parse(localStorage.getItem('selectedItems') || '[]');
            if (selectedItems.length === 0) {
                e.preventDefault();
                showCustomAlert('Please select at least one item to proceed to checkout.', 'warning');
            }
        });

        updateSelectedTotal();
        updateCartCount();
    }
}