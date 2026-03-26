/**
 * auth-guard.js — Redirect unauthenticated users to login.
 * Load this as the FIRST script on any protected page.
 */
(function () {
    const token = localStorage.getItem('pd_token');
    // When served as root ('/'), the popped segment is '', so fall back to 'index.html' (login page)
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';

    // If no token and not already on the login page, redirect to login
    if (!token && currentPage !== 'index.html') {
        window.location.replace('index.html');
    }

    // Populate sidebar user info if DOM is ready or when DOMContentLoaded fires
    function populateUserInfo() {
        try {
            const user = JSON.parse(localStorage.getItem('pd_user') || '{}');
            const nameEl = document.querySelector('.user-name');
            const roleEl = document.querySelector('.user-role');
            const avatarEl = document.querySelector('.avatar');

            if (nameEl && user.username) {
                nameEl.textContent = user.username;
            }
            if (roleEl && user.role) {
                roleEl.textContent = user.role.charAt(0).toUpperCase() + user.role.slice(1);
            }
            if (avatarEl && user.username) {
                avatarEl.textContent = user.username.charAt(0).toUpperCase();
            }

            // Wire up user-profile click to logout → go to login page (index.html)
            const profileEl = document.querySelector('.user-profile');
            if (profileEl) {
                profileEl.style.cursor = 'pointer';
                profileEl.title = 'Click to logout';
                profileEl.onclick = function () {
                    if (confirm('Log out?')) {
                        localStorage.removeItem('pd_token');
                        localStorage.removeItem('pd_user');
                        window.location.href = 'index.html';
                    }
                };
            }
        } catch (e) {
            // silently ignore
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', populateUserInfo);
    } else {
        populateUserInfo();
    }
})();
