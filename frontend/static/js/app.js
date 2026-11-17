/**
 * Ashwa Logistics — Client-Side Application Utilities
 * Supports both unified Django server and separated frontend/backend servers.
 */

// Auto-detect backend API host:
// If running directly from Django on port 8000 (or default port), use relative URLs.
// If running from separate frontend server (e.g. port 5500, 3000, 5173), target port 8000 on the same host.
if (typeof window !== 'undefined' && typeof window.BACKEND_URL === 'undefined') {
  window.BACKEND_URL = (window.location.port === '8000' || !window.location.port)
    ? ''
    : `${window.location.protocol}//${window.location.hostname || '127.0.0.1'}:8000`;
}
var BACKEND_URL = (typeof window !== 'undefined' && window.BACKEND_URL) || '';

function getApiUrl(endpoint) {
  if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
    return endpoint;
  }
  return BACKEND_URL + endpoint;
}

if (typeof window !== 'undefined' && typeof window.cachedCsrfToken === 'undefined') {
  window.cachedCsrfToken = null;
}
var cachedCsrfToken = (typeof window !== 'undefined' && window.cachedCsrfToken) || null;

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue || cachedCsrfToken;
}

async function ensureCsrfToken() {
  if (getCookie('csrftoken') || cachedCsrfToken) {
    return getCookie('csrftoken') || cachedCsrfToken;
  }
  try {
    const res = await fetch(getApiUrl('/api/csrf/'), { credentials: 'include' });
    const data = await res.json();
    if (data && data.csrfToken) {
      cachedCsrfToken = data.csrfToken;
      return cachedCsrfToken;
    }
  } catch (e) {}
  return '';
}

function getAuthHeaders() {
  const headers = {};

  const token = localStorage.getItem('token');

  if (token) {
    headers['X-Session-Token'] = token;
  }

  return headers;
}

async function apiGet(url) {
  const fullUrl = getApiUrl(url);
  const res = await fetch(fullUrl, {
    credentials: 'include',
    headers: {
      'Accept': 'application/json',
      ...getAuthHeaders()
    }
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || 'Request failed with status ' + res.status);
  }
  return data;
}

async function apiPost(url, payload = {}) {
  const fullUrl = getApiUrl(url);
  const csrfToken = await ensureCsrfToken();
  const res = await fetch(fullUrl, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-CSRFToken': csrfToken || '',
      ...getAuthHeaders()
    },
    body: JSON.stringify(payload)
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || 'Request failed with status ' + res.status);
  }
  return data;
}

async function getCurrentUser() {
  try {
    const res = await apiGet('/api/me/');
    if (res && res.authenticated && res.user) {
      localStorage.setItem('user', JSON.stringify(res.user));
      return res.user;
    } else {
      localStorage.removeItem('user');
      localStorage.removeItem('token');
      return null;
    }
  } catch (e) {
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    return null;
  }
}

// Unified customer navigation auth header renderer
async function renderAuth() {
  const authArea = document.getElementById('authArea');
  const profileBox = document.getElementById('profileBox');
  if (!authArea) return;

  const user = await getCurrentUser();
  if (user) {
    authArea.innerHTML = `
      <div class="profile-btn" onclick="toggleProfile()" title="View Account">👤</div>
    `;
    const pName = document.getElementById('pName');
    const pEmail = document.getElementById('pEmail');
    if (pName) pName.innerText = 'Name: ' + user.name;
    if (pEmail) pEmail.innerText = 'Email: ' + user.email;
    
    // Auto-fill form inputs if present
    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    if (nameInput && !nameInput.value) nameInput.value = user.name;
    if (emailInput && !emailInput.value) emailInput.value = user.email;
  } else {
    authArea.innerHTML = `
      <a href="/login/" id="loginBtn" data-public="true" class="login-btn">Login</a>
    `;
    if (profileBox) profileBox.style.display = 'none';
  }
}

function toggleProfile() {
  const box = document.getElementById('profileBox');
  if (box) {
    box.style.display = (box.style.display === 'block') ? 'none' : 'block';
  }
}

async function logout() {
  try {
    await apiPost('/api/logout/', {});
  } catch (e) {}
  localStorage.removeItem('user');
  const box = document.getElementById('profileBox');
  if (box) box.style.display = 'none';
  await renderAuth();
  alert('Logged out successfully!');
  if (window.location.pathname !== '/' && window.location.pathname !== '/contact/' && window.location.pathname !== '/enquiry/') {
    window.location.href = '/';
  }
}

// Close profile dropdown when clicking outside
document.addEventListener('click', function(e) {
  const box = document.getElementById('profileBox');
  const btn = document.querySelector('.profile-btn');
  if (box && box.style.display === 'block') {
    if (!box.contains(e.target) && (!btn || !btn.contains(e.target))) {
      box.style.display = 'none';
    }
  }
});

// Explicit global window bindings
if (typeof window !== 'undefined') {
  window.BACKEND_URL = BACKEND_URL;
  window.getApiUrl = getApiUrl;
  window.getCookie = getCookie;
  window.ensureCsrfToken = ensureCsrfToken;
  window.getAuthHeaders = getAuthHeaders;
  window.apiGet = apiGet;
  window.apiPost = apiPost;
  window.getCurrentUser = getCurrentUser;
  window.renderAuth = renderAuth;
  window.toggleProfile = toggleProfile;
  window.logout = logout;
}
