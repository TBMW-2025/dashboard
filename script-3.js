// Dashboard interactivity

document.addEventListener('DOMContentLoaded', () => {
    console.log("Dashboard loaded");
    if (document.getElementById('map-container')) renderMap();
    if (document.getElementById('mainChart')) renderMainChart();
    if (document.getElementById('miniAreaChart')) renderMiniChart();
    setupThemeToggle();
    if (document.querySelector('.data-table-container')) setupStudentsTable();
});

function setupThemeToggle() {
    const themeToggleBtn = document.querySelector('.theme-toggle');
    const body = document.body;

    // Check for saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        body.classList.add('light-mode');
    }

    themeToggleBtn.addEventListener('click', () => {
        body.classList.toggle('light-mode');

        // Save preference
        if (body.classList.contains('light-mode')) {
            localStorage.setItem('theme', 'light');
        } else {
            localStorage.setItem('theme', 'dark');
        }
    });
}

function renderMainChart() {
    const ctx = document.getElementById('mainChart').getContext('2d');

    // Gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(249, 115, 22, 0.5)'); // accent-orange
    gradient.addColorStop(1, 'rgba(249, 115, 22, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
            datasets: [{
                label: 'Revenue',
                data: [35, 45, 30, 60, 45, 75, 55, 80, 65, 95],
                borderColor: '#f97316',
                backgroundColor: gradient,
                borderWidth: 3,
                pointBackgroundColor: '#fff',
                pointBorderColor: '#f97316',
                pointBorderWidth: 2,
                pointRadius: 4,
                fill: true,
                tension: 0.4 // Smooth curve
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { display: false, drawBorder: false },
                    ticks: { color: '#9ca3af' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)', drawBorder: false },
                    ticks: { color: '#9ca3af', stepSize: 20 }
                }
            }
        }
    });
}

function renderMiniChart() {
    const ctx = document.getElementById('miniAreaChart').getContext('2d');

    const gradient = ctx.createLinearGradient(0, 0, 0, 150);
    gradient.addColorStop(0, 'rgba(59, 130, 246, 0.5)'); // accent-blue
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['M', 'T', 'W', 'T', 'F', 'S', 'S'],
            datasets: [{
                data: [12, 19, 15, 25, 22, 30, 28],
                borderColor: '#3b82f6',
                backgroundColor: gradient,
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { display: false, min: 0 }
            },
            layout: { padding: 0 }
        }
    });
}

function renderMap() {
    const container = document.getElementById('map-container');
    const width = container.clientWidth;
    const height = container.clientHeight || 400; // default height if not rendered yet

    const svg = d3.select('#map-container')
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', `0 0 ${width} ${height}`)
        .style('display', 'block');

    const g = svg.append('g');

    // Add Zoom capabilities
    const zoom = d3.zoom()
        .scaleExtent([1, 8])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });

    svg.call(zoom);

    // Zoom buttons overlay
    const zoomControls = d3.select('#map-container')
        .append('div')
        .attr('class', 'zoom-controls');

    zoomControls.append('button')
        .text('+')
        .on('click', () => {
            svg.transition().duration(300).call(zoom.scaleBy, 1.5);
        });

    zoomControls.append('button')
        .text('-')
        .on('click', () => {
            svg.transition().duration(300).call(zoom.scaleBy, 0.75);
        });

    const projection = d3.geoMercator()
        .center([82.8, 23.5]) // Center of India
        .scale(width * 1.5) /* INCREASED SCALE FOR BIGGER MAP */
        .translate([width / 2, height / 2]);

    const path = d3.geoPath().projection(projection);

    d3.json('https://raw.githubusercontent.com/india-in-data/india-states-2019/master/india_states.geojson').then(data => {
        // Fit the projection strictly to the geometric bounds of the features
        projection.fitSize([width, height], data);

        g.selectAll('path')
            .data(data.features)
            .enter()
            .append('path')
            .attr('d', path)
            .attr('class', 'map-state')
            .on('mouseover', function (event, d) {
                d3.select(this).classed('highlighted', true);
            })
            .on('mouseout', function (event, d) {
                d3.select(this).classed('highlighted', false);
            });
    }).catch(error => {
        console.error("Error loading map data: ", error);
        container.innerHTML = "<p style='color: var(--text-primary); text-align: center;'>Error loading map data.</p>";
    });
}

function setupStudentsTable() {
    // Handle remove buttons
    const removeBtns = document.querySelectorAll('.btn-remove');
    removeBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const row = e.target.closest('tr');
            if (row) {
                row.remove();
            }
        });
    });

    // Handle placement status change
    const statusSelects = document.querySelectorAll('.status-select');
    statusSelects.forEach(select => {
        select.addEventListener('change', (e) => {
            if (e.target.value === 'Placed') {
                const row = e.target.closest('tr');
                if (row) {
                    // Small delay to let user see it changed before removing
                    setTimeout(() => {
                        row.remove();
                    }, 500);
                }
            }
        });
    });
}

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
    const btn = document.getElementById('twoFaBtn');
    if (btn) {
        if (btn.textContent === 'Enable') {
            btn.textContent = 'Disable';
            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-danger');
            alert('Two-Factor Authentication has been enabled');
        } else {
            btn.textContent = 'Enable';
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-secondary');
            alert('Two-Factor Authentication has been disabled');
        }
    } else {
        alert('Two-Factor Authentication setup would open here');
    }
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

document.addEventListener("DOMContentLoaded", function () {

    const modal = document.getElementById("addStudentModal");
    const openBtn = document.getElementById("openStudentModal") || document.querySelector(".table-actions .btn-add");
    const closeBtns = document.querySelectorAll(".close-modal");

    // OPEN MODAL
    if (openBtn && modal) {
        openBtn.addEventListener("click", function (e) {
            e.preventDefault();
            modal.style.display = "flex";
        });
    }

    // CLOSE BUTTON
    if (modal) {
        closeBtns.forEach(btn => {
            btn.addEventListener("click", function () {
                modal.style.display = "none";
            });
        });

        // CLICK OUTSIDE
        window.addEventListener("click", function (e) {
            if (e.target === modal) {
                modal.style.display = "none";
            }
        });

        // Form submit
        const form = modal.querySelector('.modal-form');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                alert('Student added successfully!');
                modal.style.display = 'none';
                form.reset();
            });
        }
    }

    // Notifications toggle
    const notifyBtns = document.querySelectorAll('.notification-toggle');
    notifyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const badge = btn.querySelector('.notification-badge');
            if (badge) {
                badge.style.display = 'none';
            }
            alert('No new notifications');
        });
    });

    // Local Student Search
    const localSearch = document.getElementById('localStudentSearch');
    if (localSearch) {
        localSearch.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const tableRows = document.querySelectorAll('.data-table tbody tr');

            tableRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
});