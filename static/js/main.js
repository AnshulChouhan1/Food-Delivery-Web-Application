// Main JavaScript for FoodExpress

document.addEventListener('DOMContentLoaded', function() {
    // Check if user is logged in
    checkAuthStatus();
    
    // Update cart count
    updateCartCount();
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Authentication functions
function checkAuthStatus() {
    const authSection = document.getElementById('auth-section');
    const loginLink = document.getElementById('login-link');
    
    // Check if user is logged in (you can implement session checking here)
    const isLoggedIn = sessionStorage.getItem('isLoggedIn') === 'true';
    const username = sessionStorage.getItem('username');
    const isAdmin = sessionStorage.getItem('isAdmin') === 'true';
    
    if (isLoggedIn && username) {
        authSection.innerHTML = `
            <div class="nav-item dropdown">
                <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown">
                    <i class="fas fa-user me-1"></i>${username}
                </a>
                <ul class="dropdown-menu">
                    ${isAdmin ? '<li><a class="dropdown-item" href="/admin"><i class="fas fa-cog me-2"></i>Admin Dashboard</a></li>' : ''}
                    <li><a class="dropdown-item" href="#" onclick="logout()"><i class="fas fa-sign-out-alt me-2"></i>Logout</a></li>
                </ul>
            </div>
        `;
    }
}

function login(username, password) {
    return fetch('/api/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            sessionStorage.setItem('isLoggedIn', 'true');
            sessionStorage.setItem('username', username);
            sessionStorage.setItem('isAdmin', data.is_admin);
            checkAuthStatus();
            showAlert('Login successful!', 'success');
            return true;
        } else {
            showAlert(data.message, 'danger');
            return false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred during login', 'danger');
        return false;
    });
}

function register(userData) {
    return fetch('/api/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Registration successful! Please login.', 'success');
            return true;
        } else {
            showAlert(data.message, 'danger');
            return false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred during registration', 'danger');
        return false;
    });
}

function logout() {
    fetch('/api/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        sessionStorage.clear();
        checkAuthStatus();
        showAlert('Logged out successfully!', 'success');
        window.location.href = '/';
    })
    .catch(error => {
        console.error('Error:', error);
        sessionStorage.clear();
        checkAuthStatus();
        window.location.href = '/';
    });
}

// Cart functions
function addToCart(productId, quantity = 1) {
    const isLoggedIn = sessionStorage.getItem('isLoggedIn') === 'true';
    
    if (!isLoggedIn) {
        showAlert('Please login to add items to cart', 'warning');
        return;
    }
    
    fetch('/api/add_to_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            updateCartCount();
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while adding to cart', 'danger');
    });
}

function updateCartItem(itemId, quantity) {
    fetch('/api/update_cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            item_id: itemId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload(); // Reload to update cart display
        } else {
            showAlert(data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while updating cart', 'danger');
    });
}

function removeFromCart(itemId) {
    updateCartItem(itemId, 0);
}

function updateCartCount() {
    // This is a simplified version - in a real app, you'd fetch the actual count
    const cartCountElement = document.getElementById('cart-count');
    if (cartCountElement) {
        // You can implement actual cart count fetching here
        cartCountElement.textContent = '0';
    }
}

// Utility functions
function showAlert(message, type) {
    const alertContainer = document.querySelector('.container.mt-5.pt-4');
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.insertBefore(alertDiv, alertContainer.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function formatPrice(price) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(price);
}

// Product filtering
function filterProducts(categoryId) {
    if (categoryId === 'all') {
        window.location.href = '/products';
    } else {
        window.location.href = `/products/${categoryId}`;
    }
}

// Form validation
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

// Loading states
function showLoading(element) {
    const originalText = element.textContent;
    element.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
    element.disabled = true;
    return originalText;
}

function hideLoading(element, originalText) {
    element.textContent = originalText;
    element.disabled = false;
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Add animation classes on scroll
function animateOnScroll() {
    const elements = document.querySelectorAll('.card, .hero-content');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
            }
        });
    });
    
    elements.forEach(element => {
        observer.observe(element);
    });
}

// Initialize animations
animateOnScroll();

