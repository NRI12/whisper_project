// script.js
const API_URL = 'http://127.0.0.1:8000';
// Utility Functions
function showToast(message, isError = false) {
    const toast = document.getElementById('toast');
    const toastBody = toast.querySelector('.toast-body');
    toastBody.textContent = message;
    toast.classList.toggle('bg-danger', isError);
    toast.classList.toggle('text-white', isError);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

function showCard(cardId) {
    const cards = ['loginCard', 'registerCard', 'forgotCard', 'resetCard'];
    cards.forEach(card => {
        document.getElementById(card).classList.toggle('d-none', card !== cardId);
    });
}

// Navigation Functions
function showLogin() { showCard('loginCard'); }
function showRegister() { showCard('registerCard'); }
function showForgotPassword() { showCard('forgotCard'); }
function showResetPassword() { showCard('resetCard'); }

document.addEventListener('DOMContentLoaded', function() {
    const toggleIcons = document.querySelectorAll('.password-toggle');
    
    toggleIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            const passwordInput = this.parentNode.querySelector('input');
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                this.classList.remove('fa-eye');
                this.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                this.classList.remove('fa-eye-slash');
                this.classList.add('fa-eye');
            }
        });
    });
});

// Form Handling
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem('token', data.access_token);
            showToast('Đăng nhập thành công!');
            window.location.href = '/dashboard';
        } else {
            showToast(data.detail, true);
        }
    } catch (error) {
        showToast('Đã xảy ra lỗi khi đăng nhập', true);
    }
});

document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;

    if (password !== confirmPassword) {
        showToast('Mật khẩu không khớp', true);
        return;
    }

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Đăng ký thành công!');
            showLogin();
        } else {
            showToast(data.detail, true);
        }
    } catch (error) {
        showToast('Đã xảy ra lỗi khi đăng ký', true);
    }
});

document.getElementById('forgotForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('forgotEmail').value;

    try {
        const response = await fetch(`${API_URL}/reset-password/request`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Mã OTP đã được gửi đến email của bạn');
            document.getElementById('resetEmail').value = email;
            showResetPassword();
        } else {
            showToast(data.detail, true);
        }
    } catch (error) {
        showToast('Đã xảy ra lỗi khi gửi yêu cầu', true);
    }
});

document.getElementById('resetForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('resetEmail').value;
    const otp = document.getElementById('resetOTP').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmNewPassword = document.getElementById('confirmNewPassword').value;

    if (newPassword !== confirmNewPassword) {
        showToast('Mật khẩu không khớp', true);
        return;
    }

    try {
        const response = await fetch(`${API_URL}/reset-password/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                email,
                otp,
                new_password: newPassword
            })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Đặt lại mật khẩu thành công!');
            showLogin();
        } else {
            showToast(data.detail, true);
        }
    } catch (error) {
        showToast('Đã xảy ra lỗi khi đặt lại mật khẩu', true);
    }
});