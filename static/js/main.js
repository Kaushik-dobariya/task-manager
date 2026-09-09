/**
 * Personal Task Manager (TaskFlow)
 * Client-Side JavaScript: Theme Engine, Live Search & Filters, Inline Editors, Modal Controllers
 */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    const filterController = initLiveSearchAndFilters();
    initInlineInteractions(filterController);
    initTaskModals();
    initFlashAlerts();
});

/* -------------------------------------------------------------------------- */
/*  1. LIGHT / DARK MODE ENGINE                                                */
/* -------------------------------------------------------------------------- */
function initTheme() {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeIcon');
    const storageKey = 'taskflow_theme';

    // Retrieve saved theme or fallback to system preference
    const getPreferredTheme = () => {
        const savedTheme = localStorage.getItem(storageKey);
        if (savedTheme) {
            return savedTheme;
        }
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };

    const applyTheme = (theme) => {
        document.documentElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem(storageKey, theme);

        if (themeIcon) {
            if (theme === 'dark') {
                themeIcon.className = 'bi bi-sun-fill text-warning';
                themeToggleBtn.setAttribute('title', 'Switch to Light Mode');
            } else {
                themeIcon.className = 'bi bi-moon-stars-fill text-secondary';
                themeToggleBtn.setAttribute('title', 'Switch to Dark Mode');
            }
        }
    };

    // Initialize theme immediately
    applyTheme(getPreferredTheme());

    // Toggle on button click
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
        });
    }

    // Listen for OS system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem(storageKey)) {
            applyTheme(e.matches ? 'dark' : 'light');
        }
    });
}

/* -------------------------------------------------------------------------- */
/*  2. LIVE SEARCH & COMBINED FILTERS (Status, Priority, Category)            */
/* -------------------------------------------------------------------------- */
function initLiveSearchAndFilters() {
    const searchInput = document.getElementById('taskSearchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const prioritySelect = document.getElementById('priorityFilterSelect');
    const categorySelect = document.getElementById('categoryFilterSelect');
    const filterButtons = document.querySelectorAll('#statusFilterGroup .filter-btn');
    const emptyState = document.getElementById('emptyState');
    const visibleTaskCount = document.getElementById('visibleTaskCount');

    let currentStatusFilter = 'All';

    // Filter execution logic
    function applyFilters() {
        const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
        const priorityFilter = prioritySelect ? prioritySelect.value : 'All';
        const categoryFilter = categorySelect ? categorySelect.value : 'All';
        const taskCards = document.querySelectorAll('.task-card');
        let visibleCount = 0;

        // Toggle clear search button visibility
        if (clearSearchBtn) {
            if (query.length > 0) {
                clearSearchBtn.classList.remove('d-none');
            } else {
                clearSearchBtn.classList.add('d-none');
            }
        }

        taskCards.forEach((card) => {
            const title = (card.getAttribute('data-title') || '').toLowerCase();
            const description = (card.getAttribute('data-description') || '').toLowerCase();
            const taskCategory = card.getAttribute('data-category') || 'General';
            const taskPriority = card.getAttribute('data-priority') || 'Medium';
            const taskStatus = card.getAttribute('data-status') || 'Pending';

            // Match conditions
            const matchesQuery = !query || title.includes(query) || description.includes(query);
            const matchesStatus = currentStatusFilter === 'All' || taskStatus === currentStatusFilter;
            const matchesPriority = priorityFilter === 'All' || taskPriority === priorityFilter;
            const matchesCategory = categoryFilter === 'All' || taskCategory === categoryFilter;

            if (matchesQuery && matchesStatus && matchesPriority && matchesCategory) {
                card.style.display = '';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        // Update count indicator
        if (visibleTaskCount) {
            visibleTaskCount.textContent = visibleCount;
        }

        // Toggle empty state placeholder
        if (emptyState) {
            if (visibleCount === 0) {
                emptyState.classList.remove('d-none');
            } else {
                emptyState.classList.add('d-none');
            }
        }
    }

    // Status filter button clicks
    filterButtons.forEach((btn) => {
        btn.addEventListener('click', () => {
            filterButtons.forEach((b) => b.classList.remove('active'));
            btn.classList.add('active');
            currentStatusFilter = btn.getAttribute('data-status') || 'All';
            applyFilters();
        });
    });

    // Search input typing
    if (searchInput) {
        searchInput.addEventListener('input', applyFilters);
    }

    // Clear search button
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', () => {
            if (searchInput) {
                searchInput.value = '';
                searchInput.focus();
                applyFilters();
            }
        });
    }

    // Priority filter change
    if (prioritySelect) {
        prioritySelect.addEventListener('change', applyFilters);
    }

    // Category filter change
    if (categorySelect) {
        categorySelect.addEventListener('change', applyFilters);
    }

    // Run initial filter check on load
    applyFilters();

    return { applyFilters };
}

/* -------------------------------------------------------------------------- */
/*  3. INLINE INTERACTIONS (Status Tag Toggle, Inline Desc, Inline Calendar)  */
/* -------------------------------------------------------------------------- */
function initInlineInteractions(filterController) {
    // 3a. Inline Status Tag & Checkbox Toggle
    document.addEventListener('click', async (e) => {
        const toggleBtn = e.target.closest('.status-badge-toggle, .status-toggle-btn');
        if (!toggleBtn) return;

        e.preventDefault();
        const taskId = toggleBtn.getAttribute('data-task-id');
        const card = document.getElementById(`task-${taskId}`);
        if (!card) return;

        try {
            const response = await fetch(`/tasks/${taskId}/toggle`, {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });

            if (!response.ok) throw new Error('Toggle request failed');
            const data = await response.json();

            if (data.success) {
                const newStatus = data.new_status;
                card.setAttribute('data-status', newStatus);

                // Update card completed styling
                const titleEl = card.querySelector('.task-title');
                const checkboxBtn = card.querySelector('.status-toggle-btn');
                const statusBadgeToggle = card.querySelector('.status-badge-toggle');

                if (newStatus === 'Completed') {
                    card.classList.add('task-completed', 'bg-body-tertiary', 'opacity-85');
                    card.classList.remove('bg-body');
                    if (titleEl) titleEl.classList.add('text-decoration-line-through', 'text-body-secondary');
                    
                    if (checkboxBtn) {
                        checkboxBtn.className = 'btn btn-sm status-toggle-btn rounded-circle p-0 d-flex align-items-center justify-content-center mt-1 btn-success text-white';
                        checkboxBtn.innerHTML = '<i class="bi bi-check-lg fs-5"></i>';
                        checkboxBtn.setAttribute('title', 'Click to mark as Pending');
                    }

                    if (statusBadgeToggle) {
                        statusBadgeToggle.innerHTML = `
                            <span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill small px-2 py-1 d-inline-flex align-items-center gap-1 status-badge-label">
                                <i class="bi bi-check2-circle"></i> Completed
                            </span>
                        `;
                    }
                } else {
                    card.classList.remove('task-completed', 'bg-body-tertiary', 'opacity-85');
                    card.classList.add('bg-body');
                    if (titleEl) titleEl.classList.remove('text-decoration-line-through', 'text-body-secondary');

                    if (checkboxBtn) {
                        checkboxBtn.className = 'btn btn-sm status-toggle-btn rounded-circle p-0 d-flex align-items-center justify-content-center mt-1 btn-outline-secondary';
                        checkboxBtn.innerHTML = '<i class="bi bi-circle fs-5"></i>';
                        checkboxBtn.setAttribute('title', 'Click to mark as Completed');
                    }

                    if (statusBadgeToggle) {
                        statusBadgeToggle.innerHTML = `
                            <span class="badge bg-secondary-subtle text-secondary-emphasis border border-secondary-subtle rounded-pill small px-2 py-1 d-inline-flex align-items-center gap-1 status-badge-label">
                                <i class="bi bi-hourglass-split"></i> Pending
                            </span>
                        `;
                    }
                }

                // Update metrics if returned
                if (data.total_tasks !== undefined) {
                    const elTotal = document.getElementById('statTotal');
                    const elPending = document.getElementById('statPending');
                    const elCompleted = document.getElementById('statCompleted');
                    if (elTotal) elTotal.textContent = data.total_tasks;
                    if (elPending) elPending.textContent = data.pending_tasks;
                    if (elCompleted) elCompleted.textContent = data.completed_tasks;

                    const fAll = document.querySelector('#filterAll .badge');
                    const fPending = document.querySelector('#filterPending .badge');
                    const fCompleted = document.querySelector('#filterCompleted .badge');
                    if (fAll) fAll.textContent = data.total_tasks;
                    if (fPending) fPending.textContent = data.pending_tasks;
                    if (fCompleted) fCompleted.textContent = data.completed_tasks;
                }

                // Re-apply filters so card is moved/hidden if currently filtering by Pending/Completed
                if (filterController && filterController.applyFilters) {
                    filterController.applyFilters();
                }
            }
        } catch (err) {
            console.error('Error toggling task:', err);
        }
    });

    // 3b. Inline Description Editing on Task Card
    document.addEventListener('click', async (e) => {
        // Open Edit Description Mode
        const trigger = e.target.closest('.edit-desc-trigger, .add-desc-trigger');
        if (trigger) {
            const container = trigger.closest('.task-desc-container');
            if (container) {
                const viewMode = container.querySelector('.desc-view-mode');
                const editMode = container.querySelector('.desc-edit-mode');
                const textarea = container.querySelector('.desc-textarea');
                if (viewMode && editMode) {
                    viewMode.classList.add('d-none');
                    editMode.classList.remove('d-none');
                    if (textarea) textarea.focus();
                }
            }
            return;
        }

        // Cancel Edit Description Mode
        const cancelBtn = e.target.closest('.cancel-desc-btn');
        if (cancelBtn) {
            const container = cancelBtn.closest('.task-desc-container');
            if (container) {
                const viewMode = container.querySelector('.desc-view-mode');
                const editMode = container.querySelector('.desc-edit-mode');
                const card = container.closest('.task-card');
                const originalDesc = card ? (card.getAttribute('data-description') || '') : '';
                const textarea = container.querySelector('.desc-textarea');
                if (textarea) textarea.value = originalDesc;

                if (viewMode && editMode) {
                    editMode.classList.add('d-none');
                    viewMode.classList.remove('d-none');
                }
            }
            return;
        }

        // Save Edit Description Mode
        const saveBtn = e.target.closest('.save-desc-btn');
        if (saveBtn) {
            const container = saveBtn.closest('.task-desc-container');
            if (!container) return;

            const taskId = container.getAttribute('data-task-id');
            const textarea = container.querySelector('.desc-textarea');
            const newDesc = textarea ? textarea.value.trim() : '';

            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

            try {
                const formData = new FormData();
                formData.append('description', newDesc);

                const response = await fetch(`/tasks/${taskId}/update-description`, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });

                const data = await response.json();
                if (data.success) {
                    const card = container.closest('.task-card');
                    if (card) card.setAttribute('data-description', newDesc);

                    const viewMode = container.querySelector('.desc-view-mode');
                    const editMode = container.querySelector('.desc-edit-mode');

                    if (viewMode) {
                        if (newDesc) {
                            viewMode.innerHTML = `
                                <p class="task-description text-body-secondary small mb-0 text-break desc-text">${escapeHtml(newDesc)}</p>
                                <button type="button" class="btn btn-sm btn-link p-0 text-body-tertiary edit-desc-trigger" title="Quick edit description on list">
                                    <i class="bi bi-pencil-fill" style="font-size: 0.72rem;"></i>
                                </button>
                            `;
                        } else {
                            viewMode.innerHTML = `
                                <button type="button" class="btn btn-sm btn-link p-0 text-primary text-decoration-none small d-inline-flex align-items-center gap-1 add-desc-trigger">
                                    <i class="bi bi-plus-circle"></i> Add description
                                </button>
                            `;
                        }
                        viewMode.classList.remove('d-none');
                    }
                    if (editMode) editMode.classList.add('d-none');
                }
            } catch (err) {
                console.error('Error updating description:', err);
            } finally {
                saveBtn.disabled = false;
                saveBtn.innerHTML = 'Save';
            }
        }
    });

    // 3c. Inline Due Date Calendar Picker (Today or future dates only)
    document.addEventListener('click', (e) => {
        const dateTrigger = e.target.closest('.inline-date-trigger');
        if (!dateTrigger) return;

        const container = dateTrigger.closest('.task-due-date-container');
        if (container) {
            const picker = container.querySelector('.inline-due-picker');
            if (picker) {
                if (typeof picker.showPicker === 'function') {
                    picker.showPicker();
                } else {
                    picker.focus();
                }
            }
        }
    });

    document.addEventListener('change', async (e) => {
        const picker = e.target.closest('.inline-due-picker');
        if (!picker) return;

        const container = picker.closest('.task-due-date-container');
        if (!container) return;

        const taskId = container.getAttribute('data-task-id');
        const card = container.closest('.task-card');
        const selectedDate = picker.value;

        try {
            const formData = new FormData();
            formData.append('due_date', selectedDate);

            const response = await fetch(`/tasks/${taskId}/update-due-date`, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });

            const data = await response.json();
            if (data.success) {
                if (card) card.setAttribute('data-due-date', data.due_date);

                const labelSpan = container.querySelector('.due-date-label');
                if (labelSpan) {
                    labelSpan.textContent = data.due_date ? `Due: ${data.due_date}` : 'Set Due Date';
                }

                // Check overdue badge
                const overdueBadge = container.querySelector('.overdue-badge');
                const todayStr = new Date().toISOString().split('T')[0];
                const taskStatus = card ? card.getAttribute('data-status') : 'Pending';

                if (taskStatus === 'Pending' && data.due_date && data.due_date < todayStr) {
                    if (!overdueBadge) {
                        const pill = container.querySelector('.due-date-pill');
                        if (pill) {
                            pill.classList.add('bg-danger-subtle', 'text-danger', 'border-danger-subtle');
                            pill.classList.remove('bg-body-secondary', 'text-body-secondary');
                            pill.insertAdjacentHTML('beforeend', '<span class="badge bg-danger text-white rounded-pill px-1 ms-1 overdue-badge">Overdue</span>');
                        }
                    }
                } else {
                    if (overdueBadge) overdueBadge.remove();
                    const pill = container.querySelector('.due-date-pill');
                    if (pill) {
                        pill.classList.remove('bg-danger-subtle', 'text-danger', 'border-danger-subtle');
                        pill.classList.add('bg-body-secondary', 'text-body-secondary');
                    }
                }
            } else if (data.error) {
                alert(data.error);
            }
        } catch (err) {
            console.error('Error updating due date:', err);
        }
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/* -------------------------------------------------------------------------- */
/*  4. MODAL POPULATION (EDIT & DELETE) & FORM RESET                          */
/* -------------------------------------------------------------------------- */
function initTaskModals() {
    const editModalEl = document.getElementById('editTaskModal');
    const deleteModalEl = document.getElementById('deleteTaskModal');

    const editModal = editModalEl ? new bootstrap.Modal(editModalEl) : null;
    const deleteModal = deleteModalEl ? new bootstrap.Modal(deleteModalEl) : null;

    // Handle Edit Task button clicks
    document.addEventListener('click', (e) => {
        const editBtn = e.target.closest('.edit-task-btn');
        if (editBtn) {
            const taskId = editBtn.getAttribute('data-task-id');
            const title = editBtn.getAttribute('data-title') || '';
            const description = editBtn.getAttribute('data-description') || '';
            const category = editBtn.getAttribute('data-category') || 'General';
            const dueDate = editBtn.getAttribute('data-due-date') || '';
            const priority = editBtn.getAttribute('data-priority') || 'Medium';
            const status = editBtn.getAttribute('data-status') || 'Pending';

            // Populate form elements
            const editForm = document.getElementById('editTaskForm');
            const editTitle = document.getElementById('editTitle');
            const editDescription = document.getElementById('editDescription');
            const editCategory = document.getElementById('editCategory');
            const editDueDate = document.getElementById('editDueDate');
            const editPriority = document.getElementById('editPriority');
            const editStatus = document.getElementById('editStatus');

            if (editForm) {
                editForm.action = `/tasks/${taskId}/edit`;
                editForm.classList.remove('was-validated');
            }
            if (editTitle) editTitle.value = title;
            if (editDescription) editDescription.value = description;
            if (editCategory) editCategory.value = category;
            if (editDueDate) editDueDate.value = dueDate;
            if (editPriority) editPriority.value = priority;
            if (editStatus) editStatus.value = status;

            if (editModal) editModal.show();
        }

        // Handle Delete Task button clicks
        const deleteBtn = e.target.closest('.delete-task-btn');
        if (deleteBtn) {
            const taskId = deleteBtn.getAttribute('data-task-id');
            const title = deleteBtn.getAttribute('data-title') || 'this task';

            const deleteForm = document.getElementById('deleteTaskForm');
            const deleteTaskTitle = document.getElementById('deleteTaskTitle');

            if (deleteForm) deleteForm.action = `/tasks/${taskId}/delete`;
            if (deleteTaskTitle) deleteTaskTitle.textContent = `"${title}"`;

            if (deleteModal) deleteModal.show();
        }
    });

    // Reset Add Task Modal when opened
    const addModalEl = document.getElementById('addTaskModal');
    if (addModalEl) {
        addModalEl.addEventListener('show.bs.modal', () => {
            const addForm = document.getElementById('addTaskForm');
            if (addForm) {
                addForm.reset();
                addForm.classList.remove('was-validated');
            }
        });
    }

    // Bootstrap 5 client-side form validation listener
    const validationForms = document.querySelectorAll('.needs-validation');
    validationForms.forEach((form) => {
        form.addEventListener('submit', (event) => {
            const titleInput = form.querySelector('input[name="title"]');
            if (titleInput) {
                titleInput.value = titleInput.value.trim();
            }

            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

/* -------------------------------------------------------------------------- */
/*  5. AUTO-DISMISS FLASH ALERTS                                               */
/* -------------------------------------------------------------------------- */
function initFlashAlerts() {
    const alerts = document.querySelectorAll('#flashContainer .alert');
    alerts.forEach((alertEl) => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 4000);
    });
}
