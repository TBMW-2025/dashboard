/**
 * api.js — Placement Dashboard Data Layer (Pure Supabase Edition)
 * ─────────────────────────────────────────────────────────────────────────────
 * All functions use the Supabase JS client (window._sb) from supabase-client.js.
 * Function names are identical to the old Flask version so all HTML pages work
 * without changes.
 *
 * Excel import/export is handled client-side using SheetJS (loaded via CDN).
 * ─────────────────────────────────────────────────────────────────────────────
 */

// ─── Session Helpers ──────────────────────────────────────────────────────────
function getUser() {
    try { return JSON.parse(localStorage.getItem('pd_user') || 'null'); } catch { return null; }
}
function saveUser(user) { localStorage.setItem('pd_user', JSON.stringify(user)); }
function clearSession() {
    localStorage.removeItem('pd_user');
    localStorage.removeItem('pd_token');
}
function isLoggedIn() { return !!getUser(); }

// ─── AUTH ─────────────────────────────────────────────────────────────────────
async function sha256(str) {
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(str));
    return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
}

async function apiLogin(username, password) {
    const hash = await sha256(password);
    const { data, error } = await _sb.from('settings').select('*').limit(1).single();
    if (error) throw new Error('Cannot reach database. Check connection.');

    if (data.admin_username !== username) throw new Error('Invalid username or password.');
    if (data.admin_password_hash !== hash) throw new Error('Invalid username or password.');

    const user = {
        username: data.admin_username,
        email:    data.admin_email,
        mobile:   data.admin_mobile,
        role:     'admin',
        twoFaEnabled: data.two_factor_enabled
    };

    if (data.two_factor_enabled) {
        // 2FA flow: store pending user and redirect to MFA page
        localStorage.setItem('mfa_pending_user', JSON.stringify(user));
        return { requires_2fa: true };
    }

    // No 2FA — save session immediately
    saveUser(user);
    localStorage.setItem('pd_token', 'supabase_session_' + Date.now());
    return { success: true, user };
}

function apiLogout() {
    clearSession();
    window.location.href = 'index.html';
}

// MFA bypass for demo mode
async function skipMFA() {
    const pending = localStorage.getItem('mfa_pending_user');
    if (!pending) { window.location.href = 'index.html'; return; }
    const user = JSON.parse(pending);
    saveUser(user);
    localStorage.setItem('pd_token', 'supabase_session_' + Date.now());
    localStorage.removeItem('mfa_pending_user');
    window.location.href = 'dashboard.html';
}

async function apiVerifyOtp(userId, otp) {
    // For demo: accept any 6-digit OTP
    if (otp && otp.length >= 4) {
        const pending = localStorage.getItem('mfa_pending_user');
        if (!pending) throw new Error('No pending login session.');
        const user = JSON.parse(pending);
        saveUser(user);
        localStorage.setItem('pd_token', 'supabase_session_' + Date.now());
        localStorage.removeItem('mfa_pending_user');
        return { success: true, user };
    }
    throw new Error('Invalid OTP.');
}

// ─── HELPER: throw on Supabase error ─────────────────────────────────────────
function sbCheck(error, context) {
    if (error) throw new Error(`[${context}] ${error.message}`);
}

// ─── STUDENTS ─────────────────────────────────────────────────────────────────
async function getStudents() {
    const { data, error } = await _sb.from('students').select('*').order('student_name');
    sbCheck(error, 'getStudents');
    return data;
}

async function createStudent(payload) {
    // Accepts plain object or FormData
    const obj = payload instanceof FormData ? Object.fromEntries(payload.entries()) : payload;
    const { data, error } = await _sb.from('students').insert(obj).select().single();
    sbCheck(error, 'createStudent');
    return data;
}

async function updateStudent(id, payload) {
    const obj = payload instanceof FormData ? Object.fromEntries(payload.entries()) : payload;
    const { data, error } = await _sb.from('students').update(obj).eq('enrollment_number', id).select().single();
    sbCheck(error, 'updateStudent');
    return data;
}

async function deleteStudent(id) {
    const { error } = await _sb.from('students').delete().eq('enrollment_number', id);
    sbCheck(error, 'deleteStudent');
    return { success: true };
}

async function importStudents(fileOrFormData) {
    // Accepts a File object or FormData with a 'file' key
    const file = fileOrFormData instanceof File ? fileOrFormData
        : (fileOrFormData instanceof FormData ? fileOrFormData.get('file') : null);
    if (!file) throw new Error('No file provided for import.');
    const rows = await parseExcelFile(file, 'students');
    if (!rows.length) throw new Error('No valid rows found in file.');
    const { data, error } = await _sb.from('students').upsert(rows, { onConflict: 'enrollment_number' }).select();
    sbCheck(error, 'importStudents');
    return { imported: data.length, message: `Successfully imported ${data.length} students.` };
}

async function apiResetStudentPassword(enrollmentNumber, body) {
    // In the pure frontend version, student passwords are stored in their student record
    const { error } = await _sb.from('students')
        .update({ student_password: body.new_password })
        .eq('enrollment_number', enrollmentNumber);
    sbCheck(error, 'resetStudentPassword');
    return { message: 'Password reset successfully.' };
}

// ─── COMPANIES ────────────────────────────────────────────────────────────────
async function getCompanies() {
    const { data, error } = await _sb.from('companies').select('*').order('company_name');
    sbCheck(error, 'getCompanies');
    return data;
}

async function createCompany(payload) {
    const { data, error } = await _sb.from('companies').insert(payload).select().single();
    sbCheck(error, 'createCompany');
    return data;
}

async function updateCompany(id, payload) {
    const { data, error } = await _sb.from('companies').update(payload).eq('id', id).select().single();
    sbCheck(error, 'updateCompany');
    return data;
}

async function deleteCompany(id) {
    const { error } = await _sb.from('companies').delete().eq('id', id);
    sbCheck(error, 'deleteCompany');
    return { success: true };
}

async function importCompanies(fileOrFormData) {
    const file = fileOrFormData instanceof File ? fileOrFormData
        : (fileOrFormData instanceof FormData ? fileOrFormData.get('file') : null);
    if (!file) throw new Error('No file provided.');
    const rows = await parseExcelFile(file, 'companies');
    if (!rows.length) throw new Error('No valid rows found.');
    const { data, error } = await _sb.from('companies').upsert(rows, { onConflict: 'id' }).select();
    sbCheck(error, 'importCompanies');
    return { imported: data.length, message: `Imported ${data.length} companies.` };
}

// ─── PLACEMENTS ───────────────────────────────────────────────────────────────
async function getPlacements(programme = '') {
    let query = _sb.from('placements').select('*').order('student_name');
    if (programme) query = query.eq('programme', programme);
    const { data, error } = await query;
    sbCheck(error, 'getPlacements');
    return data;
}

async function createPlacement(payload) {
    const { data, error } = await _sb.from('placements').insert(payload).select().single();
    sbCheck(error, 'createPlacement');
    // Also update the student's placement_status
    if (payload.enrollment_number) {
        await _sb.from('students').update({ placement_status: 'Yes' })
            .eq('enrollment_number', payload.enrollment_number);
    }
    return data;
}

async function updatePlacement(id, payload) {
    const { data, error } = await _sb.from('placements').update(payload).eq('enrollment_number', id).select().single();
    sbCheck(error, 'updatePlacement');
    return data;
}

async function deletePlacement(id) {
    const { error } = await _sb.from('placements').delete().eq('enrollment_number', id);
    sbCheck(error, 'deletePlacement');
    // Reset student's placement_status back to 'No'
    await _sb.from('students').update({ placement_status: 'No' }).eq('enrollment_number', id);
    return { success: true };
}

async function importPlacements(fileOrFormData) {
    const file = fileOrFormData instanceof File ? fileOrFormData
        : (fileOrFormData instanceof FormData ? fileOrFormData.get('file') : null);
    if (!file) throw new Error('No file provided.');
    const rows = await parseExcelFile(file, 'placements');
    if (!rows.length) throw new Error('No valid rows found in file. Check that your Excel headers match: Enrolment No., Company Name, Date, Salary (LPA), Status');
    // Use upsert to allow re-importing
    const { data, error } = await _sb.from('placements').upsert(rows, { onConflict: 'enrollment_number', ignoreDuplicates: false }).select();
    sbCheck(error, 'importPlacements');
    // Update student placement_status
    for (const p of data || []) {
        if (p.enrollment_number) {
            await _sb.from('students').update({ placement_status: 'Yes' })
                .eq('enrollment_number', p.enrollment_number);
        }
    }
    return { imported: (data || []).length, message: `Successfully imported ${(data || []).length} placement records.` };
}

// ─── INTERNSHIPS ──────────────────────────────────────────────────────────────
async function getInternships(programme = '') {
    let query = _sb.from('internships').select('*').order('created_at', { ascending: false });
    if (programme) query = query.eq('programme', programme);
    const { data, error } = await query;
    sbCheck(error, 'getInternships');

    // Fetch students to map names
    const { data: students, error: err2 } = await _sb.from('students').select('enrollment_number, student_name');
    if (!err2 && students) {
        const studentMap = {};
        for (let s of students) studentMap[s.enrollment_number] = s.student_name;
        return (data || []).map(i => ({ ...i, student_name: studentMap[i.enrollment_number] || '' }));
    }
    return data || [];
}

async function createInternship(payload) {
    const { data, error } = await _sb.from('internships').insert(payload).select().single();
    sbCheck(error, 'createInternship');
    return data;
}

async function updateInternship(id, payload) {
    const { data, error } = await _sb.from('internships').update(payload).eq('id', id).select().single();
    sbCheck(error, 'updateInternship');
    return data;
}

async function deleteInternship(id) {
    const { error } = await _sb.from('internships').delete().eq('id', id);
    sbCheck(error, 'deleteInternship');
    return { success: true };
}

async function importInternships(fileOrFormData) {
    const file = fileOrFormData instanceof File ? fileOrFormData
        : (fileOrFormData instanceof FormData ? fileOrFormData.get('file') : null);
    if (!file) throw new Error('No file provided.');
    const rows = await parseExcelFile(file, 'internships');
    if (!rows.length) throw new Error('No valid rows found in file. Check that your Excel headers match: Year, Enrolment No., Programme, Gender, Internship Place, Internship Place 02, Type of Organization');
    // Simple insert — internships have auto-generated IDs, no unique constraint to conflict on
    const { data, error } = await _sb.from('internships').insert(rows).select();
    sbCheck(error, 'importInternships');
    return { imported: (data || []).length, message: `Successfully imported ${(data || []).length} internship records.` };
}
// ─── FIELD VISITS ─────────────────────────────────────────────────────────────
async function getFieldVisits(programme = '') {
    let query = _sb.from('field_visits').select('*').order('created_at', { ascending: false });
    if (programme) query = query.eq('programme', programme);
    const { data, error } = await query;
    sbCheck(error, 'getFieldVisits');

    // Map student names
    const { data: students, error: err2 } = await _sb.from('students').select('enrollment_number, student_name');
    if (!err2 && students) {
        const studentMap = {};
        for (let s of students) studentMap[s.enrollment_number] = s.student_name;
        return (data || []).map(i => ({ ...i, student_name: studentMap[i.enrollment_number] || '' }));
    }
    return data || [];
}

async function createFieldVisit(payload) {
    const { data, error } = await _sb.from('field_visits').insert(payload).select().single();
    sbCheck(error, 'createFieldVisit');
    return data;
}

async function updateFieldVisit(id, payload) {
    const { data, error } = await _sb.from('field_visits').update(payload).eq('id', id).select().single();
    sbCheck(error, 'updateFieldVisit');
    return data;
}

async function deleteFieldVisit(id) {
    const { error } = await _sb.from('field_visits').delete().eq('id', id);
    sbCheck(error, 'deleteFieldVisit');
    return { success: true };
}

async function importFieldVisits(fileOrFormData) {
    const file = fileOrFormData instanceof File ? fileOrFormData
        : (fileOrFormData instanceof FormData ? fileOrFormData.get('file') : null);
    if (!file) throw new Error('No file provided.');
    const rows = await parseExcelFile(file, 'field_visits');
    if (!rows.length) throw new Error('No valid rows found in file.');
    const { data, error } = await _sb.from('field_visits').insert(rows).select();
    sbCheck(error, 'importFieldVisits');
    return { imported: (data || []).length, message: `Successfully imported ${(data || []).length} field visit records.` };
}

// ─── REPORTS (computed client-side from raw data) ─────────────────────────────
async function getStats(programme = '') {
    const [students, placements, companies, internships] = await Promise.all([
        getStudents(), getPlacements(programme), getCompanies(), getInternships(programme)
    ]);
    const filtered = programme ? students.filter(s => s.programme === programme) : students;
    const placed   = filtered.filter(s => s.placement_status === 'Yes').length;
    const rate     = filtered.length > 0 ? ((placed / filtered.length) * 100).toFixed(1) : 0;
    const avgSalary = placements.length > 0
        ? (placements.reduce((sum, p) => sum + (parseFloat(p.salary_lpa) || 0), 0) / placements.length).toFixed(2)
        : 0;
    return {
        total_students: filtered.length,
        placed_students: placed,
        placement_rate: parseFloat(rate),
        total_companies: companies.length,
        total_internships: internships.length,
        avg_salary: parseFloat(avgSalary)
    };
}

async function getDeptStats(programme = '') {
    const students = await getStudents();
    const filtered = programme ? students.filter(s => s.programme === programme) : students;
    const deptMap = {};
    filtered.forEach(s => {
        const d = s.programme || 'Unknown';
        if (!deptMap[d]) deptMap[d] = { total: 0, placed: 0 };
        deptMap[d].total++;
        if (s.placement_status === 'Yes') deptMap[d].placed++;
    });
    return Object.entries(deptMap).map(([dept, v]) => ({ department: dept, ...v }));
}

async function getYearlyTrend(programme = '') {
    const placements = await getPlacements(programme);
    const yearMap = {};
    placements.forEach(p => {
        const y = (p.placement_date || '').split('-')[0] || (p.created_at || '').split('-')[0] || 'Unknown';
        yearMap[y] = (yearMap[y] || 0) + 1;
    });
    return Object.entries(yearMap)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([year, count]) => ({ year, count }));
}

async function getStudentsYearly() {
    const students = await getStudents();
    const yearMap = {};
    students.forEach(s => {
        const y = (s.created_at || '').split('-')[0] || 'Unknown';
        yearMap[y] = (yearMap[y] || 0) + 1;
    });
    return Object.entries(yearMap).sort(([a], [b]) => a.localeCompare(b)).map(([year, count]) => ({ year, count }));
}

async function getSalaryDist() {
    const placements = await getPlacements();
    return placements.map(p => ({ salary_lpa: p.salary_lpa, company: p.company }));
}

// ─── ADMIN PROFILE ────────────────────────────────────────────────────────────
async function getAdminProfile() {
    const { data, error } = await _sb.from('settings').select('admin_username,admin_email,admin_mobile,two_factor_enabled').limit(1).single();
    sbCheck(error, 'getAdminProfile');
    return { username: data.admin_username, email: data.admin_email, mobile: data.admin_mobile, two_factor_enabled: data.two_factor_enabled };
}

async function updateAdminProfile(payload) {
    const updates = {};
    if (payload.email)  updates.admin_email  = payload.email;
    if (payload.mobile) updates.admin_mobile = payload.mobile;
    const { data, error } = await _sb.from('settings').update(updates).eq('id', 1).select().single();
    sbCheck(error, 'updateAdminProfile');
    const user = getUser() || {};
    if (payload.email)  user.email  = payload.email;
    if (payload.mobile) user.mobile = payload.mobile;
    saveUser(user);
    return data;
}

async function changeAdminPassword(payload) {
    const currentHash = await sha256(payload.current_password);
    const { data: settings, error: fetchErr } = await _sb.from('settings').select('admin_password_hash').limit(1).single();
    sbCheck(fetchErr, 'changeAdminPassword-fetch');
    if (settings.admin_password_hash !== currentHash) throw new Error('Current password is incorrect.');
    const newHash = await sha256(payload.new_password);
    const { error } = await _sb.from('settings').update({ admin_password_hash: newHash }).eq('id', 1);
    sbCheck(error, 'changeAdminPassword-update');
    return { message: 'Password changed successfully.' };
}

// ─── 2FA SETTINGS ─────────────────────────────────────────────────────────────
async function toggle2fa(enabled) {
    const { error } = await _sb.from('settings').update({ two_factor_enabled: enabled }).eq('id', 1);
    sbCheck(error, 'toggle2fa');
    return { enabled };
}

async function get2faStatus() {
    const { data, error } = await _sb.from('settings').select('two_factor_enabled').limit(1).single();
    sbCheck(error, 'get2faStatus');
    return { enabled: data.two_factor_enabled };
}

// ─── EXPORT TO EXCEL (client-side via SheetJS) ────────────────────────────────
async function exportData(type) {
    if (typeof XLSX === 'undefined') {
        alert('SheetJS library not loaded. Please check your internet connection.');
        return;
    }
    try {
        let rows = [];
        let sheetName = type;
        if (type === 'students')    { rows = await getStudents();    sheetName = 'Students'; }
        else if (type === 'placements')  { rows = await getPlacements();  sheetName = 'Placements'; }
        else if (type === 'companies')   { rows = await getCompanies();   sheetName = 'Companies'; }
        else if (type === 'internships') { rows = await getInternships(); sheetName = 'Internships'; }
        else if (type === 'field_visits') { rows = await getFieldVisits(); sheetName = 'FieldVisits'; }
        else throw new Error(`Unknown export type: ${type}`);

        if (!rows || !rows.length) { alert('No data to export.'); return; }

        // Remove internal fields
        const cleaned = rows.map(r => {
            const obj = { ...r };
            delete obj.created_at;
            return obj;
        });

        const ws = XLSX.utils.json_to_sheet(cleaned);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, sheetName);
        const filename = `${type}_export_${new Date().toISOString().slice(0,10)}.xlsx`;
        XLSX.writeFile(wb, filename);
    } catch (err) {
        alert('Export Error: ' + err.message);
    }
}

// ─── EXCEL PARSER (client-side via SheetJS) ───────────────────────────────────
async function parseExcelFile(file, type) {
    return new Promise((resolve, reject) => {
        if (typeof XLSX === 'undefined') {
            reject(new Error('SheetJS (xlsx) library not loaded.'));
            return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const wb = XLSX.read(e.target.result, { type: 'array' });
                const ws = wb.Sheets[wb.SheetNames[0]];
                const raw = XLSX.utils.sheet_to_json(ws, { defval: '' });

                let rows = [];
                // Helper: get first matching value from a row using multiple possible header names
                function col(r, ...keys) {
                    for (const k of keys) {
                        if (r[k] !== undefined && r[k] !== '') return String(r[k]).trim();
                    }
                    return '';
                }

                if (type === 'students') {
                    rows = raw.map(r => ({
                        enrollment_number:     col(r, 'Enrollment Number', 'Enrolment Number', 'Enrollment No.', 'Enrolment No.', 'Enrollment', 'enrollment_number'),
                        student_name:          col(r, 'Student Name', 'Name', 'student_name'),
                        student_email_id:      col(r, 'Email ID', 'Email Id', 'Email', 'student_email_id'),
                        mobile_number:         col(r, 'Mobile Number', 'Mobile', 'Phone', 'mobile_number'),
                        programme:             col(r, 'Programme', 'Program', 'programme'),
                        higher_education_plan: col(r, 'Higher Education Plan', 'Higher Education', 'higher_education_plan') || 'No',
                        placement_status:      col(r, 'Placement Status', 'placement_status') || 'No',
                    })).filter(r => r.enrollment_number && r.student_name);

                } else if (type === 'companies') {
                    rows = raw.map(r => ({
                        company_name:   col(r, 'Company Name', 'Company', 'company_name'),
                        role:           col(r, 'Role', 'role'),
                        contact_person: col(r, 'Contact Person', 'Contact Name', 'contact_person'),
                        contact:        col(r, 'Contact', 'Phone', 'Mobile', 'contact'),
                    })).filter(r => r.company_name);

                } else if (type === 'placements') {
                    rows = raw.map(r => ({
                        enrollment_number: col(r, 'Enrollment Number', 'Enrolment Number', 'Enrollment No.', 'Enrolment No.', 'enrollment_number'),
                        student_name:      col(r, 'Student Name', 'Name', 'student_name'),
                        company:           col(r, 'Company Name', 'Company', 'company'),
                        salary_lpa:        parseFloat(col(r, 'Salary (LPA)', 'Salary LPA', 'Salary', 'salary_lpa', 'Package (LPA)', 'Package')) || null,
                        location:          col(r, 'Location', 'Place', 'location'),
                        role:              col(r, 'Role', 'Job Role', 'role'),
                        designation:       col(r, 'Designation', 'designation'),
                        placement_date:    col(r, 'Placement Date', 'Date', 'placement_date'),
                        status:            col(r, 'Status', 'status') || 'Placed',
                    })).filter(r => r.enrollment_number);

                } else if (type === 'internships') {
                    rows = raw.map(r => ({
                        enrollment_number:   col(r, 'Enrolment No.', 'Enrollment No.', 'Enrollment Number', 'Enrolment Number', 'enrollment_number'),
                        year:                col(r, 'Year', 'year'),
                        programme:           col(r, 'Programme', 'Program', 'programme'),
                        gender:              col(r, 'Gender', 'gender'),
                        internship_place:    col(r, 'Internship Place', 'internship_place'),
                        internship_place_02: col(r, 'Internship Place 02', 'Internship Place 2', 'internship_place_02'),
                        organization_type:   col(r, 'Type of Organization', 'Organization Type', 'organization_type'),
                    })).filter(r => r.enrollment_number);
                } else if (type === 'field_visits') {
                    rows = raw.map(r => ({
                        enrollment_number:   col(r, 'Enrolment No.', 'Enrollment No.', 'Enrollment Number', 'Enrolment Number', 'enrollment_number'),
                        visit_date:          col(r, 'Date', 'Visit Date', 'visit_date'),
                        programme:           col(r, 'Programme', 'Program', 'programme'),
                        organization_name:   col(r, 'Organization Name', 'Organization', 'Company', 'organization_name'),
                        location:            col(r, 'Location', 'Place', 'location'),
                        faculty_coordinator: col(r, 'Faculty Coordinator', 'Faculty', 'Coordinator', 'faculty_coordinator')
                    })).filter(r => r.enrollment_number);
                }
                resolve(rows);
            } catch (err) {
                reject(new Error('Failed to parse Excel file: ' + err.message));
            }
        };
        reader.onerror = () => reject(new Error('Failed to read file.'));
        reader.readAsArrayBuffer(file);
    });
}

// ─── LOAD ADMIN PROFILE IN SETTINGS ──────────────────────────────────────────
async function loadAdminProfileData() {
    try {
        const profile = await getAdminProfile();
        const emailEl   = document.getElementById('email');
        const phoneEl   = document.getElementById('phone');
        const usernameEl = document.getElementById('username') || document.getElementById('adminUsername');
        if (emailEl)    emailEl.value   = profile.email   || '';
        if (phoneEl)    phoneEl.value   = profile.mobile  || '';
        if (usernameEl) usernameEl.value = profile.username || 'admin';
        // Populate sidebar
        const user = getUser() || {};
        user.email  = profile.email;
        user.mobile = profile.mobile;
        saveUser(user);
    } catch (e) {
        console.error('Failed to load admin profile', e);
    }
}
