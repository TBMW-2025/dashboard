/**
 * api.js — Shared API utility for Placement Dashboard
 * All fetch() calls to the Flask backend go through here.
 */

const API_BASE = 'http://127.0.0.1:5001';

// ─── Token Helpers ────────────────────────────────────────────────────────────
function getToken() {
    return localStorage.getItem('pd_token');
}

function saveToken(token) {
    localStorage.setItem('pd_token', token);
}

function clearToken() {
    localStorage.removeItem('pd_token');
    localStorage.removeItem('pd_user');
}

function saveUser(user) {
    localStorage.setItem('pd_user', JSON.stringify(user));
}

function getUser() {
    try {
        return JSON.parse(localStorage.getItem('pd_user'));
    } catch {
        return null;
    }
}

// ─── Core fetch wrapper ───────────────────────────────────────────────────────
async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...(options.headers || {})
    };

    if (!headers['Content-Type'] && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        clearToken();
        window.location.href = 'index.html';
        return null;
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.error || `API error ${response.status}`);
    }

    return data;
}

// ─── AUTH ─────────────────────────────────────────────────────────────────────
async function apiLogin(username, password) {
    const data = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    const json = await data.json();
    if (!data.ok) throw new Error(json.error || 'Login failed');

    // 2FA flow — store OTP hints for mfa.html
    if (json.requires_2fa) {
        localStorage.setItem('mfa_user_id', json.user_id);
        if (json.email_hint)  localStorage.setItem('mfa_email_hint',  json.email_hint);
        if (json.mobile_hint) localStorage.setItem('mfa_mobile_hint', json.mobile_hint);
    } else {
        saveToken(json.token);
        saveUser(json.user);
    }
    return json;
}

async function apiVerifyOtp(userId, otp) {
    const data = await fetch(`${API_BASE}/api/auth/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, otp: otp })
    });
    const json = await data.json();
    if (!data.ok) throw new Error(json.error || 'OTP verification failed');
    saveToken(json.token);
    saveUser(json.user);
    return json;
}

async function skipMFA() {
    try {
        const userId = localStorage.getItem('mfa_user_id');
        if (!userId) {
            alert('No pending login session found. Please login again.');
            window.location.href = 'index.html';
            return;
        }

        const data = await fetch(`${API_BASE}/api/auth/demo-bypass`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });

        const json = await data.json();
        if (!data.ok) throw new Error(json.error || 'Demo bypass failed');

        saveToken(json.access_token);
        saveUser(json.user);
        window.location.href = 'dashboard.html';
    } catch (e) {
        alert('Bypass failed: ' + e.message);
    }
}

function apiLogout() {
    clearToken();
    window.location.href = 'index.html';
}

// ─── STUDENTS ─────────────────────────────────────────────────────────────────
const getStudents    = ()       => apiFetch('/api/students');
const createStudent  = (data)   => apiFetch('/api/students', { method: 'POST', body: data instanceof FormData ? data : JSON.stringify(data) });
const updateStudent  = (id, d)  => apiFetch(`/api/students/${id}`, { method: 'PUT', body: d instanceof FormData ? d : JSON.stringify(d) });
const deleteStudent  = (id)     => apiFetch(`/api/students/${id}`, { method: 'DELETE' });
const importStudents = (formData) => apiFetch('/api/students/import', { method: 'POST', body: formData });
const apiResetStudentPassword = (id, body) => apiFetch(`/api/students/${id}/reset-password`, { method: 'POST', body: JSON.stringify(body) });

// ─── COMPANIES ────────────────────────────────────────────────────────────────
const getCompanies   = ()       => apiFetch('/api/companies');
const createCompany  = (data)   => apiFetch('/api/companies', { method: 'POST', body: JSON.stringify(data) });
const updateCompany  = (id, d)  => apiFetch(`/api/companies/${id}`, { method: 'PUT', body: JSON.stringify(d) });
const deleteCompany  = (id)     => apiFetch(`/api/companies/${id}`, { method: 'DELETE' });
const importCompanies = (formData) => apiFetch('/api/companies/import', { method: 'POST', body: formData });

// ─── PLACEMENTS ───────────────────────────────────────────────────────────────
const getPlacements  = (prog='') => apiFetch(prog ? `/api/placements?programme=${encodeURIComponent(prog)}` : '/api/placements');
const createPlacement= (data)   => apiFetch('/api/placements', { method: 'POST', body: JSON.stringify(data) });
const updatePlacement= (id, d)  => apiFetch(`/api/placements/${id}`, { method: 'PUT', body: JSON.stringify(d) });
const deletePlacement= (id)     => apiFetch(`/api/placements/${id}`, { method: 'DELETE' });
const importPlacements = (formData) => apiFetch('/api/placements/import', { method: 'POST', body: formData });

// ─── INTERNSHIPS ──────────────────────────────────────────────────────────────
const getInternships   = (prog='') => apiFetch(prog ? `/api/internships?programme=${encodeURIComponent(prog)}` : '/api/internships');
const createInternship = (data)   => apiFetch('/api/internships', { method: 'POST', body: JSON.stringify(data) });
const updateInternship = (id, d)  => apiFetch(`/api/internships/${id}`, { method: 'PUT', body: JSON.stringify(d) });
const deleteInternship = (id)     => apiFetch(`/api/internships/${id}`, { method: 'DELETE' });
const importInternships = (formData) => apiFetch('/api/internships/import', { method: 'POST', body: formData });

// ─── REPORTS ──────────────────────────────────────────────────────────────────
const getStats          = (prog='') => apiFetch(prog ? `/api/reports/stats?programme=${encodeURIComponent(prog)}` : '/api/reports/stats');
const getDeptStats      = (prog='') => apiFetch(prog ? `/api/reports/department?programme=${encodeURIComponent(prog)}` : '/api/reports/department');
const getYearlyTrend    = (prog='') => apiFetch(prog ? `/api/reports/yearly?programme=${encodeURIComponent(prog)}` : '/api/reports/yearly');
const getStudentsYearly = ()  => apiFetch('/api/reports/students-yearly');
const getSalaryDist     = ()  => apiFetch('/api/reports/salary');

const toggle2fa = (enabled) => apiFetch('/api/auth/settings/2fa', { method: 'POST', body: JSON.stringify({enabled}) });
const get2faStatus = () => apiFetch('/api/auth/settings/2fa');

// ─── ADMIN PROFILE ───────────────────────────────────────────────────────────
const getAdminProfile = () => apiFetch('/api/auth/profile');
const updateAdminProfile = (data) => apiFetch('/api/auth/profile', { method: 'PUT', body: JSON.stringify(data) });
const changeAdminPassword = (data) => apiFetch('/api/auth/change-password', { method: 'POST', body: JSON.stringify(data) });

// ─── EXPORT TO EXCEL ────────────────────────────────────────────────────────
async function exportData(type) {
    const token = getToken();
    const headers = token ? { 'Authorization': `Bearer ${token}` } : {};

    try {
        const response = await fetch(`${API_BASE}/api/export/${type}`, {
            method: 'GET',
            headers
        });

        if (response.status === 401) {
            clearToken();
            window.location.href = 'dashboard.html';
            return;
        }

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || `Export failed: ${response.status}`);
        }

        let filename = `${type}_export_.xlsx`;
        const disposition = response.headers.get('Content-Disposition');
        if (disposition && disposition.includes('filename=')) {
            const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
            if (filenameMatch && filenameMatch.length === 2) filename = filenameMatch[1];
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    } catch (error) {
        alert("Export Error: " + error.message);
    }
}
