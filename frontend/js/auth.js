/**
 * TaskFlow Authentication Controller
 * Handles user login, registration, password visibility toggles,
 * inline validation, and password strength evaluation.
 */

document.addEventListener('DOMContentLoaded', () => {
  initPasswordToggles();

  const loginForm = document.getElementById('loginForm');
  if (loginForm) {
    initLoginForm(loginForm);
  }

  const registerForm = document.getElementById('registerForm');
  if (registerForm) {
    initRegisterForm(registerForm);
  }
});

/**
 * Enable show/hide password buttons.
 */
function initPasswordToggles() {
  const toggleButtons = document.querySelectorAll('.toggle-password-btn');
  toggleButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (!input) return;

      const isPassword = input.getAttribute('type') === 'password';
      input.setAttribute('type', isPassword ? 'text' : 'password');

      btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
      btn.innerHTML = isPassword
        ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`
        : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
    });
  });
}

/**
 * Login Form Handler
 */
function initLoginForm(form) {
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const submitBtn = document.getElementById('submitBtn');
  const alertBox = document.getElementById('alertBox');

  const clearErrors = () => {
    alertBox.classList.add('hidden');
    alertBox.textContent = '';
    [emailInput, passwordInput].forEach(inp => {
      if (inp) inp.classList.remove('has-error');
    });
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    if (!email || !password) {
      showAlert(alertBox, 'Please enter both your email address and password.', 'danger');
      if (!email) emailInput.classList.add('has-error');
      if (!password) passwordInput.classList.add('has-error');
      return;
    }

    // Set loading state
    setButtonLoading(submitBtn, true, 'Signing in...');

    const res = await apiRequest('/api/auth/login', {
      method: 'POST',
      body: { email, password }
    });

    setButtonLoading(submitBtn, false, 'Sign in');

    if (res.ok) {
      showToast('Welcome back! Redirecting to dashboard...', 'success');
      setTimeout(() => {
        window.location.href = '/';
      }, 600);
    } else {
      const msg = (res.data && res.data.message) ? res.data.message : 'Invalid credentials. Please try again.';
      showAlert(alertBox, msg, 'danger');
      passwordInput.classList.add('has-error');
      passwordInput.focus();
    }
  });
}

/**
 * Register Form Handler with Live Strength & Validation
 */
function initRegisterForm(form) {
  const nameInput = document.getElementById('name');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const confirmPasswordInput = document.getElementById('confirm_password');
  const submitBtn = document.getElementById('submitBtn');
  const alertBox = document.getElementById('alertBox');

  const strengthBar = document.getElementById('strengthBar');
  const strengthText = document.getElementById('strengthText');

  // Real-time password strength meter
  passwordInput.addEventListener('input', () => {
    const val = passwordInput.value;
    const { score, label, color } = calculatePasswordStrength(val);

    if (val.length === 0) {
      strengthBar.style.width = '0%';
      strengthText.textContent = '';
    } else {
      strengthBar.style.width = `${score}%`;
      strengthBar.style.backgroundColor = color;
      strengthText.textContent = `Strength: ${label}`;
      strengthText.style.color = color;
    }
  });

  const clearErrors = () => {
    alertBox.classList.add('hidden');
    alertBox.textContent = '';
    form.querySelectorAll('.form-input').forEach(inp => inp.classList.remove('has-error'));
    form.querySelectorAll('.form-error-msg').forEach(el => el.textContent = '');
  };

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearErrors();

    const name = nameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    let hasLocalError = false;

    if (name.length < 2 || name.length > 80) {
      setFieldError('name', 'Name must be between 2 and 80 characters.');
      hasLocalError = true;
    }

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setFieldError('email', 'Please enter a valid email address.');
      hasLocalError = true;
    }

    if (password.length < 8) {
      setFieldError('password', 'Password must be at least 8 characters long.');
      hasLocalError = true;
    }

    if (password !== confirmPassword) {
      setFieldError('confirm_password', 'Passwords do not match.');
      hasLocalError = true;
    }

    if (hasLocalError) return;

    setButtonLoading(submitBtn, true, 'Creating account...');

    const res = await apiRequest('/api/auth/register', {
      method: 'POST',
      body: {
        name,
        email,
        password,
        confirm_password: confirmPassword
      }
    });

    setButtonLoading(submitBtn, false, 'Create account');

    if (res.ok) {
      showToast('Account created successfully! Loading dashboard...', 'success');
      setTimeout(() => {
        window.location.href = '/';
      }, 700);
    } else {
      if (res.data && res.data.fields) {
        Object.entries(res.data.fields).forEach(([field, msg]) => {
          setFieldError(field, msg);
        });
      }
      const genericMsg = (res.data && res.data.message) ? res.data.message : 'Unable to create account. Please check errors above.';
      showAlert(alertBox, genericMsg, 'danger');
    }
  });
}

function setFieldError(fieldName, message) {
  const input = document.getElementById(fieldName);
  const errorEl = document.getElementById(`${fieldName}Error`);
  if (input) input.classList.add('has-error');
  if (errorEl) errorEl.textContent = message;
}

function showAlert(alertEl, message, type = 'danger') {
  if (!alertEl) return;
  alertEl.className = `alert-box alert-${type}`;
  alertEl.textContent = message;
  alertEl.classList.remove('hidden');
}

function setButtonLoading(button, isLoading, text) {
  if (!button) return;
  button.disabled = isLoading;
  button.textContent = text;
}

/**
 * Calculate password strength score (0-100)
 */
function calculatePasswordStrength(password) {
  if (!password) return { score: 0, label: '', color: '' };

  let score = 0;
  if (password.length >= 8) score += 25;
  if (password.length >= 12) score += 15;
  if (/[0-9]/.test(password)) score += 20;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 20;
  if (/[^a-zA-Z0-9]/.test(password)) score += 20;

  if (score < 40) {
    return { score, label: 'Weak', color: '#ef4444' };
  } else if (score < 75) {
    return { score, label: 'Fair', color: '#f59e0b' };
  } else if (score < 90) {
    return { score, label: 'Strong', color: '#10b981' };
  } else {
    return { score: 100, label: 'Excellent', color: '#059669' };
  }
}
