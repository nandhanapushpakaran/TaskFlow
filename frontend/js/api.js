/**
 * TaskFlow API & Shared Utilities
 * Encapsulates network communication, theme switching, date helpers, and toast notifications.
 */

// Global Toast Container Element
let toastContainer = null;

/**
 * Perform an authenticated API request with standardized error handling.
 * @param {string} url - Relative API endpoint URL (e.g., '/api/tasks')
 * @param {object} options - Fetch options (method, headers, body)
 * @returns {Promise<{ ok: boolean, status: number, data: any }>}
 */
async function apiRequest(url, options = {}) {
  const defaultHeaders = {
    'Accept': 'application/json',
  };

  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...(options.headers || {})
    }
  };

  try {
    const response = await fetch(url, config);
    let data = null;

    try {
      data = await response.json();
    } catch (e) {
      // Empty or non-JSON body
      data = null;
    }

    // Handle session expiration or unauthorized API access
    if (response.status === 401) {
      const currentPath = window.location.pathname;
      if (!currentPath.endsWith('login.html') && !currentPath.endsWith('register.html')) {
        showToast('Your session has expired. Please log in again.', 'error');
        setTimeout(() => {
          window.location.href = '/login.html';
        }, 1200);
      }
    }

    return {
      ok: response.ok,
      status: response.status,
      data: data
    };
  } catch (networkError) {
    console.error('Network Error:', networkError);
    return {
      ok: false,
      status: 0,
      data: {
        error: 'network_error',
        message: 'Unable to connect to the server. Please verify your connection and try again.'
      }
    };
  }
}

/**
 * Display a modern, accessible toast notification.
 * @param {string} message - Toast message text
 * @param {'success'|'error'|'info'} type - Toast type
 * @param {number} duration - Auto-dismiss duration in milliseconds
 */
function showToast(message, type = 'info', duration = 3500) {
  if (!toastContainer) {
    toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.id = 'toastContainer';
      toastContainer.className = 'toast-container';
      toastContainer.setAttribute('aria-live', 'polite');
      toastContainer.setAttribute('aria-atomic', 'true');
      document.body.appendChild(toastContainer);
    }
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.setAttribute('role', 'status');

  const contentWrap = document.createElement('div');
  contentWrap.className = 'toast-content';

  const iconWrap = document.createElement('div');
  iconWrap.className = 'toast-icon';

  // SVG Icons based on type
  if (type === 'success') {
    iconWrap.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
  } else if (type === 'error') {
    iconWrap.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
  } else {
    iconWrap.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
  }

  const textSpan = document.createElement('span');
  textSpan.textContent = message;

  contentWrap.appendChild(iconWrap);
  contentWrap.appendChild(textSpan);

  const closeBtn = document.createElement('button');
  closeBtn.className = 'toast-close-btn';
  closeBtn.setAttribute('aria-label', 'Dismiss notification');
  closeBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;

  const dismiss = () => {
    toast.classList.add('toast-fade-out');
    setTimeout(() => {
      if (toast.parentElement) {
        toast.parentElement.removeChild(toast);
      }
    }, 250);
  };

  closeBtn.addEventListener('click', dismiss);
  toast.appendChild(contentWrap);
  toast.appendChild(closeBtn);
  toastContainer.appendChild(toast);

  if (duration > 0) {
    setTimeout(dismiss, duration);
  }
}

/**
 * Format date string into friendly localized human representation.
 * @param {string} dateStr - ISO date string (YYYY-MM-DD)
 * @returns {{ text: string, isOverdue: boolean, isToday: boolean }}
 */
function formatFriendlyDate(dateStr) {
  if (!dateStr) return { text: '', isOverdue: false, isToday: false };

  const parts = dateStr.split('-');
  if (parts.length < 3) return { text: dateStr, isOverdue: false, isToday: false };

  const year = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10) - 1;
  const day = parseInt(parts[2], 10);

  const targetDate = new Date(year, month, day);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  const msPerDay = 1000 * 60 * 60 * 24;
  const diffDays = Math.round((targetDate - today) / msPerDay);

  if (diffDays === 0) {
    return { text: 'Due today', isOverdue: false, isToday: true };
  } else if (diffDays === 1) {
    return { text: 'Due tomorrow', isOverdue: false, isToday: false };
  } else if (diffDays === -1) {
    return { text: 'Overdue by 1 day', isOverdue: true, isToday: false };
  } else if (diffDays < -1) {
    return { text: `Overdue by ${Math.abs(diffDays)} days`, isOverdue: true, isToday: false };
  } else {
    // Format Month Day, Year
    const options = { month: 'short', day: 'numeric' };
    if (year !== now.getFullYear()) {
      options.year = 'numeric';
    }
    const formatted = targetDate.toLocaleDateString(undefined, options);
    return { text: `Due ${formatted}`, isOverdue: false, isToday: false };
  }
}

/**
 * Initialize theme preference from localStorage or system setting.
 */
function initTheme() {
  const saved = localStorage.getItem('taskflow-theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark = saved ? saved === 'dark' : prefersDark;

  if (isDark) {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }

  updateThemeToggleButtons(isDark);
}

/**
 * Toggle between light and dark modes.
 */
function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const nextIsDark = current !== 'dark';

  if (nextIsDark) {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('taskflow-theme', 'dark');
  } else {
    document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('taskflow-theme', 'light');
  }

  updateThemeToggleButtons(nextIsDark);
}

function updateThemeToggleButtons(isDark) {
  const buttons = document.querySelectorAll('.theme-toggle-btn');
  buttons.forEach(btn => {
    btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
    btn.innerHTML = isDark
      ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`
      : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
  });
}

// Initialize theme immediately to prevent FOUC (flash of unstyled content)
initTheme();

// Auto-initialize theme and wire up event listeners on DOM load
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
});

// Global delegated click listener for theme toggle buttons on any page
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.theme-toggle-btn');
  if (btn) {
    e.preventDefault();
    toggleTheme();
  }
});
