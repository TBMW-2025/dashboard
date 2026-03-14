// ===================================================================
// PLACEMENT MONITOR DASHBOARD - MASTER JAVASCRIPT FILE
// Combined functionality for: Companies, Placements, Reports, Settings
// ===================================================================

// ===== COMMON FUNCTIONALITY FOR ALL PAGES =====

/**
 * Initialize search functionality for table rows
 */
function initSearch() {
    const searchBars = document.querySelectorAll('.search-bar');
    const tableRows = document.querySelectorAll('.table-row');

    if (searchBars.length > 0 && tableRows.length > 0) {
        searchBars.forEach(searchBar => {
            searchBar.addEventListener('input', function (e) {
                const searchTerm = e.target.value.toLowerCase();

                tableRows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(searchTerm) ? '' : 'none';
                });
            });
        });
    }
}

/**
 * Initialize add button functionality
 */
function initAddButton() {
    const addBtn = document.querySelector('.btn-add');
    if (addBtn) {
        addBtn.addEventListener('click', function () {
            const contentTitle = document.querySelector('.content-title');
            let pageType = 'Item';

            if (contentTitle) {
                if (contentTitle.textContent.includes('Companies')) {
                    pageType = 'Company';
                } else if (contentTitle.textContent.includes('Placements')) {
                    pageType = 'Placement';
                }
            }

            alert(`Add ${pageType} form would open here`);
        });
    }
}

/**
 * Initialize action button functionality
 */
function initActionButtons() {
    const actionBtns = document.querySelectorAll('.action-btn');
    actionBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            alert('Options menu would appear here');
        });
    });
}

// ===== REPORTS PAGE FUNCTIONALITY =====

/**
 * Initialize charts for Reports page using Chart.js
 */
function initializeCharts() {
    // 1. Placement Status Distribution (Pie Chart)
    const placementStatusCtx = document.getElementById('placementStatusChart');
    if (placementStatusCtx) {
        new Chart(placementStatusCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Placed', 'Unplaced', 'Higher Studies'],
                datasets: [{
                    data: [987, 258, 0],
                    backgroundColor: [
                        '#ff6b35',
                        '#ef4444',
                        '#6b7280'
                    ],
                    borderColor: '#1a1f3a',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#aaa',
                            padding: 15,
                            font: { size: 12 }
                        }
                    }
                }
            }
        });
    }

    // 2. Department-wise Placement (Bar Chart)
    const deptCtx = document.getElementById('deptPlacementChart');
    if (deptCtx) {
        new Chart(deptCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['CS', 'IT', 'ECE', 'ME', 'CE', 'Other'],
                datasets: [{
                    label: 'Students Placed',
                    data: [234, 212, 198, 165, 140, 105],
                    backgroundColor: '#ff6b35',
                    borderRadius: 5,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        labels: { color: '#aaa', font: { size: 11 } }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#888', font: { size: 11 } },
                        grid: { color: '#2a2f4a' }
                    },
                    y: {
                        ticks: { color: '#888', font: { size: 11 } },
                        grid: { color: 'transparent' }
                    }
                }
            }
        });
    }

    // 3. Monthly Placement Trend (Line Chart)
    const monthlyCtx = document.getElementById('monthlyTrendChart');
    if (monthlyCtx) {
        new Chart(monthlyCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Placements',
                    data: [45, 65, 82, 95, 110, 125, 142, 158, 172, 185, 198, 210],
                    borderColor: '#ff6b35',
                    backgroundColor: 'rgba(255, 107, 53, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#ff6b35',
                    pointBorderColor: '#1a1f3a',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#aaa', font: { size: 11 } }
                    }
                },
                scales: {
                    y: {
                        ticks: { color: '#888', font: { size: 11 } },
                        grid: { color: '#2a2f4a' },
                        beginAtZero: true
                    },
                    x: {
                        ticks: { color: '#888', font: { size: 11 } },
                        grid: { color: '#2a2f4a' }
                    }
                }
            }
        });
    }

    // 4. Salary Distribution (Bar Chart)
    const salaryCtx = document.getElementById('salaryDistributionChart');
    if (salaryCtx) {
        new Chart(salaryCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['7-9 LPA', '9-11 LPA', '11-13 LPA', '13-15 LPA', '15-20 LPA', '20+ LPA'],
                datasets: [{
                    label: 'Number of Students',
                    data: [145, 220, 325, 195, 85, 17],
                    backgroundColor: '#ff6b35',
                    borderRadius: 5,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#aaa', font: { size: 11 } }
                    }
                },
                scales: {
                    y: {
                        ticks: { color: '#888', font: { size: 11 } },
                        grid: { color: '#2a2f4a' },
                        beginAtZero: true
                    },
                    x: {
                        ticks: { color: '#888', font: { size: 11 } },
                        grid: { color: 'transparent' }
                    }
                }
            }
        });
    }
}

// ===== SETTINGS PAGE FUNCTIONALITY =====

/**
 * Switch between different settings tabs
 */
function switchTab(tabName) {
    // Hide all content sections
    const contents = document.querySelectorAll('.settings-content');
    contents.forEach(content => content.classList.remove('active'));

    // Remove active class from all nav items
    const navItems = document.querySelectorAll('.settings-nav-item');
    navItems.forEach(item => item.classList.remove('active'));

    // Show selected content
    const selectedContent = document.getElementById(tabName);
    if (selectedContent) {
        selectedContent.classList.add('active');
    }

    // Add active class to clicked nav item
    if (event && event.target) {
        event.target.classList.add('active');
    }
}

/**
 * Update admin profile information
 */
function updateProfile() {
    const firstName = document.getElementById('firstName');
    const lastName = document.getElementById('lastName');
    const email = document.getElementById('email');
    const phone = document.getElementById('phone');

    if (!firstName || !lastName || !email || !phone) {
        alert('Please fill in all fields');
        return;
    }

    if (!firstName.value || !lastName.value || !email.value || !phone.value) {
        alert('Please fill in all fields');
        return;
    }

    const alertEl = document.getElementById('profileAlert');
    if (alertEl) {
        alertEl.textContent = '✓ Profile updated successfully!';
        alertEl.classList.add('show');

        setTimeout(() => {
            alertEl.classList.remove('show');
        }, 3000);
    }
}

/**
 * Reset admin profile form to default values
 */
function resetProfileForm() {
    const firstNameEl = document.getElementById('firstName');
    const lastNameEl = document.getElementById('lastName');
    const emailEl = document.getElementById('email');
    const phoneEl = document.getElementById('phone');

    if (firstNameEl) firstNameEl.value = 'Arsh';
    if (lastNameEl) lastNameEl.value = 'G';
    if (emailEl) emailEl.value = 'arsh.g@university.edu';
    if (phoneEl) phoneEl.value = '+91 9876543210';
}

/**
 * Check password strength and update visual indicator
 */
function checkPasswordStrength() {
    const passwordInput = document.getElementById('newPassword');
    if (!passwordInput) return;

    const password = passwordInput.value;
    const bars = document.querySelectorAll('#strengthIndicator .strength-bar');
    const text = document.getElementById('strengthText');

    let strength = 0;

    // Check password criteria
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[!@#$%^&*]/.test(password)) strength++;

    // Reset all bars
    bars.forEach(bar => bar.classList.remove('weak', 'medium', 'strong'));

    // Update strength indicator
    if (strength < 2) {
        if (text) {
            text.textContent = 'Password strength: Weak';
            text.classList.remove('medium', 'strong');
            text.classList.add('weak');
        }
        if (bars[0]) bars[0].classList.add('weak');
    } else if (strength < 4) {
        if (text) {
            text.textContent = 'Password strength: Medium';
            text.classList.remove('weak', 'strong');
            text.classList.add('medium');
        }
        if (bars[0]) bars[0].classList.add('medium');
        if (bars[1]) bars[1].classList.add('medium');
    } else {
        if (text) {
            text.textContent = 'Password strength: Strong';
            text.classList.remove('weak', 'medium');
            text.classList.add('strong');
        }
        if (bars[0]) bars[0].classList.add('strong');
        if (bars[1]) bars[1].classList.add('strong');
        if (bars[2]) bars[2].classList.add('strong');
    }
}

/**
 * Update admin password
 */
function updateAdminPassword() {
    const currentPassword = document.getElementById('currentPassword');
    const newPassword = document.getElementById('newPassword');
    const confirmPassword = document.getElementById('confirmPassword');

    if (!currentPassword || !newPassword || !confirmPassword) {
        alert('Please fill in all password fields');
        return;
    }

    const currentPwd = currentPassword.value;
    const newPwd = newPassword.value;
    const confirmPwd = confirmPassword.value;

    if (!currentPwd || !newPwd || !confirmPwd) {
        alert('Please fill in all password fields');
        return;
    }

    if (newPwd !== confirmPwd) {
        alert('New passwords do not match');
        return;
    }

    if (newPwd.length < 8) {
        alert('Password must be at least 8 characters long');
        return;
    }

    const alertEl = document.getElementById('passwordAlert');
    if (alertEl) {
        alertEl.textContent = '✓ Password changed successfully!';
        alertEl.classList.add('show');

        resetPasswordForm();

        setTimeout(() => {
            alertEl.classList.remove('show');
        }, 3000);
    }
}

/**
 * Reset password form to empty state
 */
function resetPasswordForm() {
    const currentPasswordEl = document.getElementById('currentPassword');
    const newPasswordEl = document.getElementById('newPassword');
    const confirmPasswordEl = document.getElementById('confirmPassword');
    const strengthText = document.getElementById('strengthText');

    if (currentPasswordEl) currentPasswordEl.value = '';
    if (newPasswordEl) newPasswordEl.value = '';
    if (confirmPasswordEl) confirmPasswordEl.value = '';
    if (strengthText) {
        strengthText.textContent = 'Password strength: Weak';
        strengthText.classList.remove('medium', 'strong');
        strengthText.classList.add('weak');
    }

    // Reset strength bars
    const bars = document.querySelectorAll('#strengthIndicator .strength-bar');
    bars.forEach(bar => {
        bar.classList.remove('weak', 'medium', 'strong');
    });
}

/**
 * Load student details when selected
 */
function loadStudentDetails() {
    const select = document.getElementById('studentSelect');
    const details = document.getElementById('studentDetails');

    if (!select || !select.value) {
        if (details) details.style.display = 'none';
        return;
    }

    if (details) details.style.display = 'block';

    const students = {
        'ENR2023001': { name: 'John Doe', email: 'john.doe@university.edu' },
        'ENR2023002': { name: 'Jane Smith', email: 'jane.smith@university.edu' },
        'ENR2023003': { name: 'Alex Jones', email: 'alex.jones@university.edu' },
        'ENR2023004': { name: 'Sam Wilson', email: 'sam.wilson@university.edu' },
        'ENR2023005': { name: 'Emily Brown', email: 'emily.brown@university.edu' }
    };

    const student = students[select.value];
    if (student) {
        const studentNameEl = document.getElementById('studentName');
        const studentEnrollmentEl = document.getElementById('studentEnrollment');
        const studentEmailEl = document.getElementById('studentEmail');

        if (studentNameEl) studentNameEl.textContent = student.name;
        if (studentEnrollmentEl) studentEnrollmentEl.textContent = select.value;
        if (studentEmailEl) studentEmailEl.textContent = student.email;
    }
}

/**
 * Reset student password
 */
function resetStudentPassword() {
    const student = document.getElementById('studentSelect');
    const tempPassword = document.getElementById('tempPassword');

    if (!student || !tempPassword) {
        alert('Please select a student and enter a temporary password');
        return;
    }

    if (!student.value || !tempPassword.value) {
        alert('Please select a student and enter a temporary password');
        return;
    }

    const studentNameEl = document.getElementById('studentName');
    const alert = document.getElementById('studentPasswordAlert');

    if (alert) {
        const studentName = studentNameEl ? studentNameEl.textContent : 'the student';
        alert.textContent = `✓ Password for ${studentName} has been reset!`;
        alert.classList.add('show');

        clearStudentForm();

        setTimeout(() => {
            alert.classList.remove('show');
        }, 3000);
    }
}

/**
 * Clear student password reset form
 */
function clearStudentForm() {
    const selectEl = document.getElementById('studentSelect');
    const passwordEl = document.getElementById('tempPassword');
    const detailsEl = document.getElementById('studentDetails');

    if (selectEl) selectEl.value = '';
    if (passwordEl) passwordEl.value = '';
    if (detailsEl) detailsEl.style.display = 'none';
}

/**
 * Update notification preferences
 */
function updateNotifications() {
    alert('Notification preferences saved');
}

/**
 * Enable two-factor authentication
 */
function enableTwoFA() {
    alert('Two-Factor Authentication setup would open here');
}

/**
 * Revoke an active session
 */
function revokeSession() {
    alert('Session revoked successfully');
}

/**
 * Open delete account confirmation
 */
function openDeleteAccount() {
    if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
        alert('Account deletion initiated');
    }
}

// ===================================================================
// DOM CONTENT LOADED - Initialize all functionality
// ===================================================================

document.addEventListener('DOMContentLoaded', function () {
    // Initialize common functionality
    initSearch();
    initAddButton();
    initActionButtons();

    // Initialize charts if on reports page
    if (document.getElementById('placementStatusChart')) {
        initializeCharts();
    }
});

// ===== SIDEBAR TOGGLE FUNCTIONALITY =====

/**
 * Initialize sidebar toggle button
 */
function initSidebarToggle() {
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');

    if (!toggleBtn || !sidebar) return;

    // Toggle button click
    toggleBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    });

    // Close sidebar when clicking on overlay
    if (overlay) {
        overlay.addEventListener('click', function () {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        });
    }

    // Close sidebar when clicking on a navigation link
    const navLinks = document.querySelectorAll('.sidebar-nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', function () {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        });
    });

    // Close sidebar when clicking outside
    document.addEventListener('click', function (e) {
        if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
        }
    });
}

// Add to DOM Content Loaded
document.addEventListener('DOMContentLoaded', function () {
    // Initialize all existing functions
    initSearch();
    initAddButton();
    initActionButtons();

    // Initialize sidebar toggle
    initSidebarToggle();
});