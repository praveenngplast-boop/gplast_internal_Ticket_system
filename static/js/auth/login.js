document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.getElementById('id_password');
    const toggleBtn = document.getElementById('passwordToggleBtn');
    const toggleIcon = document.getElementById('passwordToggleIcon');

    if (toggleBtn && passwordInput && toggleIcon) {
        toggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';
            toggleIcon.className = isPassword ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
            passwordInput.focus();
        });
    }

    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    let isSubmitting = false;

    if (loginForm && loginBtn) {
        loginForm.addEventListener('submit', function(e) {
            if (isSubmitting) {
                e.preventDefault();
                return false;
            }
            
            const username = document.getElementById('id_username');
            const password = document.getElementById('id_password');
            
            if (!username.value.trim() || !password.value.trim()) {
                return true;
            }
            
            isSubmitting = true;
            loginBtn.disabled = true;
            loginBtn.classList.add('loading');
            
            return true;
        });
        
        const errorAlerts = document.querySelectorAll('.alert-login');
        if (errorAlerts.length > 0) {
            loginBtn.disabled = false;
            loginBtn.classList.remove('loading');
            isSubmitting = false;
        }
        
        const errorObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length > 0) {
                    const hasError = document.querySelector('.alert-login');
                    if (hasError && isSubmitting) {
                        loginBtn.disabled = false;
                        loginBtn.classList.remove('loading');
                        isSubmitting = false;
                    }
                }
            });
        });
        
        errorObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    }

    const usernameInput = document.getElementById('id_username');
    if (usernameInput && !usernameInput.value) {
        usernameInput.focus();
    }

    const loginThemeToggle = document.getElementById('loginThemeToggle');
    const loginThemeIcon = document.getElementById('loginThemeIcon');
    const html = document.documentElement;

    const savedTheme = localStorage.getItem('theme') || 'light';
    applyLoginTheme(savedTheme);

    function applyLoginTheme(theme) {
        if (theme === 'dark') {
            html.setAttribute('data-theme', 'dark');
            if (loginThemeIcon) loginThemeIcon.className = 'fas fa-sun';
        } else {
            html.removeAttribute('data-theme');
            if (loginThemeIcon) loginThemeIcon.className = 'fas fa-moon';
        }
        localStorage.setItem('theme', theme);
    }

    function toggleLoginTheme() {
        const current = html.getAttribute('data-theme');
        const newTheme = current === 'dark' ? 'light' : 'dark';
        applyLoginTheme(newTheme);
        
        if (loginThemeToggle) {
            loginThemeToggle.style.transform = 'scale(0.8) rotate(180deg)';
            setTimeout(function() { 
                if (loginThemeToggle) loginThemeToggle.style.transform = ''; 
            }, 300);
        }
    }

    if (loginThemeToggle) {
        loginThemeToggle.addEventListener('click', toggleLoginTheme);
    }

    const themeObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'data-theme') {
                const theme = html.getAttribute('data-theme');
                if (loginThemeIcon) {
                    loginThemeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
                }
            }
        });
    });

    themeObserver.observe(html, {
        attributes: true,
        attributeFilter: ['data-theme']
    });
});