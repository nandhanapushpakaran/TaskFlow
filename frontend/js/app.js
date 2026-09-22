/**
 * TaskFlow Dashboard Application
 * State management, task CRUD operations, real-time filtering, search,
 * statistics updates, modal controls, and safe DOM rendering.
 */

// Application State
const state = {
  tasks: [],
  statusFilter: 'all',
  priorityFilter: 'all',
  search: '',
  sort: 'created_desc',
  editingTaskId: null,
  deletingTaskId: null,
  currentUser: null,
  isLoading: true
};

// Search debounce timer
let searchDebounceTimer = null;

document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
});

/**
 * Initialize Dashboard
 */
async function initDashboard() {
  initTheme();
  setupEventListeners();
  displayFriendlyCurrentDate();

  // Load user profile
  const user = await loadCurrentUser();
  if (user) {
    // Initial fetch of statistics and tasks
    await Promise.all([
      loadStats(),
      loadTasks()
    ]);
  }
}

/**
 * Fetch and populate authenticated user info.
 */
async function loadCurrentUser() {
  const res = await apiRequest('/api/auth/me');
  if (!res.ok || !res.data || !res.data.user) {
    window.location.href = '/login.html';
    return null;
  }

  const user = res.data.user;
  state.currentUser = user;

  // Update navbar user profile
  const userNameEl = document.getElementById('navUserName');
  const userAvatarEl = document.getElementById('navUserAvatar');
  const welcomeGreetingEl = document.getElementById('welcomeGreeting');

  if (userNameEl) userNameEl.textContent = user.name;
  if (userAvatarEl) {
    const initials = user.name
      .split(' ')
      .map(part => part.charAt(0))
      .slice(0, 2)
      .join('');
    userAvatarEl.textContent = initials || 'U';
  }

  // Personalized dynamic greeting
  if (welcomeGreetingEl) {
    const hour = new Date().getHours();
    let timeGreeting = 'Good morning';
    if (hour >= 12 && hour < 17) {
      timeGreeting = 'Good afternoon';
    } else if (hour >= 17) {
      timeGreeting = 'Good evening';
    }
    welcomeGreetingEl.textContent = `${timeGreeting}, ${user.name} 👋`;
  }

  return user;
}

/**
 * Set formatted today's date in welcome section.
 */
function displayFriendlyCurrentDate() {
  const dateEl = document.getElementById('currentDateDisplay');
  if (dateEl) {
    const now = new Date();
    const options = { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' };
    dateEl.textContent = now.toLocaleDateString(undefined, options);
  }
}

/**
 * Fetch and render task counts and statistics.
 */
async function loadStats() {
  const res = await apiRequest('/api/tasks/stats');
  if (res.ok && res.data) {
    const { total, pending, completed, overdue } = res.data;
    const statTotalEl = document.getElementById('statTotal');
    const statPendingEl = document.getElementById('statPending');
    const statCompletedEl = document.getElementById('statCompleted');
    const statOverdueEl = document.getElementById('statOverdue');

    if (statTotalEl) statTotalEl.textContent = total;
    if (statPendingEl) statPendingEl.textContent = pending;
    if (statCompletedEl) statCompletedEl.textContent = completed;
    if (statOverdueEl) statOverdueEl.textContent = overdue;
  }
}

/**
 * Fetch tasks based on active filters, search, and sorting.
 */
async function loadTasks() {
  const params = new URLSearchParams();
  if (state.statusFilter !== 'all') params.append('status', state.statusFilter);
  if (state.priorityFilter !== 'all') params.append('priority', state.priorityFilter);
  if (state.search.trim()) params.append('search', state.search.trim());
  if (state.sort) params.append('sort', state.sort);

  if (state.isLoading) {
    renderSkeletons();
  }

  const res = await apiRequest(`/api/tasks?${params.toString()}`);
  state.isLoading = false;

  if (res.ok && res.data) {
    state.tasks = res.data.tasks || [];
    renderTasks();
  } else {
    showToast('Failed to load tasks. Please refresh.', 'error');
  }

  updateClearFiltersButton();
}

/**
 * Render task cards into the grid safely without innerHTML for untrusted strings.
 */
function renderTasks() {
  const container = document.getElementById('tasksGrid');
  const countBadge = document.getElementById('tasksCountPill');
  if (!container) return;

  container.innerHTML = '';

  if (countBadge) {
    countBadge.textContent = `${state.tasks.length} task${state.tasks.length === 1 ? '' : 's'}`;
  }

  if (state.tasks.length === 0) {
    renderEmptyState(container);
    return;
  }

  state.tasks.forEach(task => {
    const card = createTaskCardElement(task);
    container.appendChild(card);
  });
}

/**
 * Safely create a single Task Card DOM element.
 */
function createTaskCardElement(task) {
  const isCompleted = task.status === 'completed';

  const card = document.createElement('article');
  card.className = `task-card ${isCompleted ? 'is-completed' : ''}`;
  card.setAttribute('data-task-id', task.id);

  // Top Section (Checkbox + Body)
  const topSection = document.createElement('div');
  topSection.className = 'task-card-top';

  // Custom Checkbox
  const checkboxWrap = document.createElement('div');
  checkboxWrap.className = 'task-checkbox-wrap';

  const checkbox = document.createElement('input');
  checkbox.type = 'checkbox';
  checkbox.className = 'task-checkbox';
  checkbox.checked = isCompleted;
  checkbox.setAttribute('aria-label', `Mark "${task.title}" as ${isCompleted ? 'pending' : 'completed'}`);
  checkbox.addEventListener('change', () => toggleTask(task.id));

  checkboxWrap.appendChild(checkbox);

  // Body: Title + Description + Badges
  const body = document.createElement('div');
  body.className = 'task-body';

  const title = document.createElement('h3');
  title.className = 'task-title';
  title.textContent = task.title;

  body.appendChild(title);

  if (task.description && task.description.trim()) {
    const desc = document.createElement('p');
    desc.className = 'task-desc';
    desc.textContent = task.description;
    body.appendChild(desc);
  }

  // Badges container
  const badgesWrap = document.createElement('div');
  badgesWrap.className = 'task-badges';

  // Priority badge
  const priorityBadge = document.createElement('span');
  priorityBadge.className = `badge badge-priority-${task.priority}`;
  priorityBadge.textContent = task.priority;
  badgesWrap.appendChild(priorityBadge);

  // Status badge
  const statusBadge = document.createElement('span');
  statusBadge.className = `badge badge-status-${task.status}`;
  statusBadge.textContent = task.status;
  badgesWrap.appendChild(statusBadge);

  // Due Date & Overdue badge
  if (task.due_date) {
    const dateInfo = formatFriendlyDate(task.due_date);
    const dueBadge = document.createElement('span');

    if (!isCompleted && (task.is_overdue || dateInfo.isOverdue)) {
      dueBadge.className = 'badge badge-overdue';
      dueBadge.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg> ${dateInfo.text}`;
    } else {
      dueBadge.className = 'badge badge-due';
      dueBadge.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg> ${dateInfo.text}`;
    }
    badgesWrap.appendChild(dueBadge);
  }

  body.appendChild(badgesWrap);
  topSection.appendChild(checkboxWrap);
  topSection.appendChild(body);

  // Footer Actions
  const footer = document.createElement('div');
  footer.className = 'task-card-footer';

  const footerDate = document.createElement('div');
  footerDate.className = 'task-footer-date';
  if (isCompleted && task.completed_at) {
    const completedDate = new Date(task.completed_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    footerDate.textContent = `Completed ${completedDate}`;
  } else if (task.created_at) {
    const createdDate = new Date(task.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    footerDate.textContent = `Added ${createdDate}`;
  }

  const actions = document.createElement('div');
  actions.className = 'task-actions';

  // Edit Button
  const editBtn = document.createElement('button');
  editBtn.className = 'btn btn-secondary btn-sm';
  editBtn.setAttribute('aria-label', `Edit task: ${task.title}`);
  editBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg> Edit`;
  editBtn.addEventListener('click', () => openEditTaskModal(task));

  // Toggle Button (Complete / Reopen)
  const toggleBtn = document.createElement('button');
  toggleBtn.className = `btn btn-sm ${isCompleted ? 'btn-secondary' : 'btn-primary'}`;
  toggleBtn.setAttribute('aria-label', `${isCompleted ? 'Reopen' : 'Complete'} task: ${task.title}`);
  toggleBtn.innerHTML = isCompleted
    ? `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg> Reopen`
    : `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Complete`;
  toggleBtn.addEventListener('click', () => toggleTask(task.id));

  // Delete Button
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'btn btn-danger-outline btn-sm';
  deleteBtn.setAttribute('aria-label', `Delete task: ${task.title}`);
  deleteBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg> Delete`;
  deleteBtn.addEventListener('click', () => openDeleteConfirmModal(task.id, task.title));

  actions.appendChild(editBtn);
  actions.appendChild(toggleBtn);
  actions.appendChild(deleteBtn);

  footer.appendChild(footerDate);
  footer.appendChild(actions);

  card.appendChild(topSection);
  card.appendChild(footer);

  return card;
}

/**
 * Render empty state when 0 tasks are present.
 */
function renderEmptyState(container) {
  const isFiltering = state.statusFilter !== 'all' || state.priorityFilter !== 'all' || state.search.trim() !== '';

  const wrap = document.createElement('div');
  wrap.className = 'empty-state';

  if (isFiltering) {
    wrap.innerHTML = `
      <div class="empty-icon">🔍</div>
      <h3 class="empty-title">No tasks found</h3>
      <p class="empty-desc">We couldn't find any tasks matching your active filters or search keyword.</p>
    `;
    const clearBtn = document.createElement('button');
    clearBtn.className = 'btn btn-primary';
    clearBtn.textContent = 'Clear filters';
    clearBtn.addEventListener('click', clearFilters);
    wrap.appendChild(clearBtn);
  } else {
    wrap.innerHTML = `
      <div class="empty-icon">✨</div>
      <h3 class="empty-title">Your task list is empty</h3>
      <p class="empty-desc">You're all caught up! Create your first task to start organizing your projects and productivity.</p>
    `;
    const addBtn = document.createElement('button');
    addBtn.className = 'btn btn-primary';
    addBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg> Create your first task`;
    addBtn.addEventListener('click', openCreateTaskModal);
    wrap.appendChild(addBtn);
  }

  container.appendChild(wrap);
}

/**
 * Render loading skeleton cards.
 */
function renderSkeletons() {
  const container = document.getElementById('tasksGrid');
  if (!container) return;

  container.innerHTML = '';
  for (let i = 0; i < 3; i++) {
    const skel = document.createElement('div');
    skel.className = 'skeleton-card';
    skel.innerHTML = `
      <div class="skeleton-shimmer skeleton-title"></div>
      <div class="skeleton-shimmer skeleton-text"></div>
      <div class="skeleton-shimmer skeleton-text-sm"></div>
      <div class="skeleton-shimmer skeleton-badges"></div>
    `;
    container.appendChild(skel);
  }
}

/**
 * Toggle task completion status.
 */
async function toggleTask(taskId) {
  const res = await apiRequest(`/api/tasks/${taskId}/toggle`, {
    method: 'PATCH'
  });

  if (res.ok && res.data) {
    const updatedTask = res.data.task;
    showToast(res.data.message || 'Task updated.', 'success');

    // Update in local state
    const index = state.tasks.findIndex(t => t.id === taskId);
    if (index !== -1) {
      state.tasks[index] = updatedTask;
    }

    // Refresh display & stats
    renderTasks();
    loadStats();
  } else {
    showToast('Failed to update task status.', 'error');
  }
}

/**
 * Open Modal to Create a new task.
 */
function openCreateTaskModal() {
  state.editingTaskId = null;
  const modal = document.getElementById('taskModal');
  const titleEl = document.getElementById('modalTitle');
  const form = document.getElementById('taskForm');
  const submitBtn = document.getElementById('taskFormSubmitBtn');

  if (titleEl) titleEl.textContent = 'Create New Task';
  if (submitBtn) submitBtn.textContent = 'Create Task';
  if (form) form.reset();

  clearModalErrors();
  updateCharCounter(0);

  // Set default due date to tomorrow or empty
  const dueDateInput = document.getElementById('taskDueDate');
  if (dueDateInput) dueDateInput.value = '';

  const prioritySelect = document.getElementById('taskPriority');
  if (prioritySelect) prioritySelect.value = 'medium';

  showModal(modal);
  document.getElementById('taskTitle').focus();
}

/**
 * Open Modal to Edit an existing task.
 */
function openEditTaskModal(task) {
  state.editingTaskId = task.id;
  const modal = document.getElementById('taskModal');
  const titleEl = document.getElementById('modalTitle');
  const submitBtn = document.getElementById('taskFormSubmitBtn');

  if (titleEl) titleEl.textContent = 'Edit Task';
  if (submitBtn) submitBtn.textContent = 'Save Changes';

  clearModalErrors();

  const titleInput = document.getElementById('taskTitle');
  const descInput = document.getElementById('taskDescription');
  const prioritySelect = document.getElementById('taskPriority');
  const dueDateInput = document.getElementById('taskDueDate');

  if (titleInput) titleInput.value = task.title || '';
  if (descInput) {
    descInput.value = task.description || '';
    updateCharCounter(descInput.value.length);
  }
  if (prioritySelect) prioritySelect.value = task.priority || 'medium';
  if (dueDateInput) dueDateInput.value = task.due_date || '';

  showModal(modal);
  if (titleInput) titleInput.focus();
}

/**
 * Handle Task Form submission (Create or Edit).
 */
async function handleTaskFormSubmit(e) {
  e.preventDefault();
  clearModalErrors();

  const titleInput = document.getElementById('taskTitle');
  const descInput = document.getElementById('taskDescription');
  const prioritySelect = document.getElementById('taskPriority');
  const dueDateInput = document.getElementById('taskDueDate');
  const submitBtn = document.getElementById('taskFormSubmitBtn');

  const title = titleInput.value.trim();
  const description = descInput.value.trim();
  const priority = prioritySelect.value;
  const dueDate = dueDateInput.value || null;

  let hasError = false;
  if (!title || title.length > 120) {
    setModalFieldError('taskTitle', 'Title is required (1-120 characters).');
    hasError = true;
  }
  if (description.length > 1000) {
    setModalFieldError('taskDescription', 'Description must not exceed 1000 characters.');
    hasError = true;
  }

  if (hasError) return;

  const isEditing = state.editingTaskId !== null;
  const url = isEditing ? `/api/tasks/${state.editingTaskId}` : '/api/tasks';
  const method = isEditing ? 'PUT' : 'POST';

  submitBtn.disabled = true;
  submitBtn.textContent = isEditing ? 'Saving...' : 'Creating...';

  const res = await apiRequest(url, {
    method: method,
    body: {
      title,
      description,
      priority,
      due_date: dueDate
    }
  });

  submitBtn.disabled = false;
  submitBtn.textContent = isEditing ? 'Save Changes' : 'Create Task';

  if (res.ok && res.data) {
    hideModal(document.getElementById('taskModal'));
    showToast(res.data.message || (isEditing ? 'Task updated.' : 'Task created successfully.'), 'success');
    await Promise.all([
      loadTasks(),
      loadStats()
    ]);
  } else {
    if (res.data && res.data.fields) {
      Object.entries(res.data.fields).forEach(([f, msg]) => {
        if (f === 'title') setModalFieldError('taskTitle', msg);
        if (f === 'description') setModalFieldError('taskDescription', msg);
        if (f === 'priority') setModalFieldError('taskPriority', msg);
        if (f === 'due_date') setModalFieldError('taskDueDate', msg);
      });
    } else {
      showToast((res.data && res.data.message) ? res.data.message : 'Unable to save task.', 'error');
    }
  }
}

/**
 * Open Delete Confirmation Modal.
 */
function openDeleteConfirmModal(taskId, taskTitle) {
  state.deletingTaskId = taskId;
  const modal = document.getElementById('deleteConfirmModal');
  const titleDisplay = document.getElementById('deleteTaskTitleDisplay');
  if (titleDisplay) {
    titleDisplay.textContent = `"${taskTitle}"`;
  }
  showModal(modal);
}

/**
 * Confirm and execute task deletion.
 */
async function confirmDeleteTask() {
  if (!state.deletingTaskId) return;

  const deleteBtn = document.getElementById('confirmDeleteBtn');
  if (deleteBtn) {
    deleteBtn.disabled = true;
    deleteBtn.textContent = 'Deleting...';
  }

  const res = await apiRequest(`/api/tasks/${state.deletingTaskId}`, {
    method: 'DELETE'
  });

  if (deleteBtn) {
    deleteBtn.disabled = false;
    deleteBtn.textContent = 'Delete Task';
  }

  hideModal(document.getElementById('deleteConfirmModal'));

  if (res.ok) {
    showToast('Task deleted successfully.', 'success');
    state.deletingTaskId = null;
    await Promise.all([
      loadTasks(),
      loadStats()
    ]);
  } else {
    showToast('Failed to delete task. Please try again.', 'error');
  }
}

/**
 * Modal Visibility Helpers
 */
function showModal(modalEl) {
  if (!modalEl) return;
  modalEl.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function hideModal(modalEl) {
  if (!modalEl) return;
  modalEl.classList.add('hidden');
  document.body.style.overflow = '';
}

function clearModalErrors() {
  document.querySelectorAll('#taskModal .form-input').forEach(inp => inp.classList.remove('has-error'));
  document.querySelectorAll('#taskModal .form-error-msg').forEach(msg => msg.textContent = '');
}

function setModalFieldError(id, msg) {
  const inp = document.getElementById(id);
  const err = document.getElementById(`${id}Error`);
  if (inp) inp.classList.add('has-error');
  if (err) err.textContent = msg;
}

function updateCharCounter(count) {
  const counterEl = document.getElementById('charCounter');
  if (counterEl) {
    counterEl.textContent = `${count} / 1000`;
    counterEl.style.color = count > 1000 ? '#ef4444' : '';
  }
}

/**
 * Filter & Search Event Handlers
 */
function clearFilters() {
  state.statusFilter = 'all';
  state.priorityFilter = 'all';
  state.search = '';

  const searchInput = document.getElementById('taskSearchInput');
  const statusSelect = document.getElementById('statusFilterSelect');
  const prioritySelect = document.getElementById('priorityFilterSelect');

  if (searchInput) searchInput.value = '';
  if (statusSelect) statusSelect.value = 'all';
  if (prioritySelect) prioritySelect.value = 'all';

  const clearSearchBtn = document.getElementById('searchClearBtn');
  if (clearSearchBtn) clearSearchBtn.classList.remove('visible');

  loadTasks();
}

function updateClearFiltersButton() {
  const clearBtn = document.getElementById('clearFiltersBtn');
  if (!clearBtn) return;

  const isFiltering = state.statusFilter !== 'all' || state.priorityFilter !== 'all' || state.search.trim() !== '';
  if (isFiltering) {
    clearBtn.classList.add('visible');
  } else {
    clearBtn.classList.remove('visible');
  }
}

/**
 * Setup All Event Listeners on the Page
 */
function setupEventListeners() {
  // Logout button
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      logoutBtn.disabled = true;
      await apiRequest('/api/auth/logout', { method: 'POST' });
      window.location.href = '/login.html';
    });
  }

  // Add Task button
  const addTaskBtn = document.getElementById('addTaskBtn');
  if (addTaskBtn) {
    addTaskBtn.addEventListener('click', openCreateTaskModal);
  }

  // Task form submission
  const taskForm = document.getElementById('taskForm');
  if (taskForm) {
    taskForm.addEventListener('submit', handleTaskFormSubmit);
  }

  // Description character counter
  const descInput = document.getElementById('taskDescription');
  if (descInput) {
    descInput.addEventListener('input', () => {
      updateCharCounter(descInput.value.length);
    });
  }

  // Modal Close buttons
  document.querySelectorAll('.modal-close-trigger').forEach(btn => {
    btn.addEventListener('click', () => {
      hideModal(btn.closest('.modal-backdrop'));
    });
  });

  // Click outside modal backdrop to close
  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        hideModal(backdrop);
      }
    });
  });

  // ESC key closes modals
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop:not(.hidden)').forEach(modal => {
        hideModal(modal);
      });
    }
  });

  // Confirm delete button
  const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
  if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener('click', confirmDeleteTask);
  }

  // Search input (debounced)
  const searchInput = document.getElementById('taskSearchInput');
  const searchClearBtn = document.getElementById('searchClearBtn');

  if (searchInput) {
    searchInput.addEventListener('input', () => {
      const val = searchInput.value;
      if (searchClearBtn) {
        if (val.length > 0) {
          searchClearBtn.classList.add('visible');
        } else {
          searchClearBtn.classList.remove('visible');
        }
      }

      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        state.search = val;
        loadTasks();
      }, 300);
    });
  }

  if (searchClearBtn && searchInput) {
    searchClearBtn.addEventListener('click', () => {
      searchInput.value = '';
      searchClearBtn.classList.remove('visible');
      state.search = '';
      loadTasks();
      searchInput.focus();
    });
  }

  // Filter selects
  const statusSelect = document.getElementById('statusFilterSelect');
  if (statusSelect) {
    statusSelect.addEventListener('change', () => {
      state.statusFilter = statusSelect.value;
      loadTasks();
    });
  }

  const prioritySelect = document.getElementById('priorityFilterSelect');
  if (prioritySelect) {
    prioritySelect.addEventListener('change', () => {
      state.priorityFilter = prioritySelect.value;
      loadTasks();
    });
  }

  const sortSelect = document.getElementById('sortSelect');
  if (sortSelect) {
    sortSelect.addEventListener('change', () => {
      state.sort = sortSelect.value;
      loadTasks();
    });
  }

  // Clear filters button
  const clearFiltersBtn = document.getElementById('clearFiltersBtn');
  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener('click', clearFilters);
  }
}
