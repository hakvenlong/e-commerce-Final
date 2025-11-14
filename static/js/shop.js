
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

document.querySelectorAll('.btn-add-cart').forEach(button => {
    button.addEventListener('click', function() {
        const product = {
            id: this.dataset.id,
            name: this.dataset.name,
            price: parseFloat(this.dataset.price),
            image: this.dataset.image,
            quantity: 1
        };
        fetch('/add-to-cart', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(product)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                showCustomAlert(data.message || `${product.name} added to cart!`, 'success');
            } else {
                showCustomAlert(data.message || 'Error adding product to cart.', 'danger');
            }
        })
        .catch(error => {
            console.error('Error adding to cart:', error);
            showCustomAlert(`Error adding product to cart: ${error.message}`, 'danger');
        });
    });
});