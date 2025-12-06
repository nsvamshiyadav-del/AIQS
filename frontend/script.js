// ==================== AUTH STATE ====================
let authToken = localStorage.getItem('authToken');
let currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');

// ==================== PAGE INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
  if (authToken && currentUser) {
    showDashboard();
    loadDashboardData();
  } else {
    showAuthPage();
  }
});

// ==================== AUTH UI CONTROLS ====================
function switchToLogin() {
  document.getElementById('login-section').style.display = 'block';
  document.getElementById('register-section').style.display = 'none';
  document.querySelectorAll('.tab-btn').forEach((btn, idx) => {
    btn.classList.toggle('active', idx === 0);
  });
}

function switchToRegister() {
  document.getElementById('login-section').style.display = 'none';
  document.getElementById('register-section').style.display = 'block';
  document.querySelectorAll('.tab-btn').forEach((btn, idx) => {
    btn.classList.toggle('active', idx === 1);
  });
}

function showAuthPage() {
  document.getElementById('auth-page').style.display = 'flex';
  document.getElementById('dashboard').style.display = 'none';
}

function showDashboard() {
  document.getElementById('auth-page').style.display = 'none';
  document.getElementById('dashboard').style.display = 'block';
  if (currentUser) {
    document.getElementById('user-display').textContent = `Welcome, ${currentUser.username}!`;
    document.getElementById('user-email').value = currentUser.email || '';
    document.getElementById('user-phone').value = currentUser.phone || '';
    document.getElementById('email-notifications').checked = currentUser.email_notifications !== false;
    document.getElementById('phone-notifications').checked = currentUser.phone_notifications !== false;
  }
}

// ==================== LOGIN/REGISTER HANDLERS ====================
async function handleLogin(event) {
  event.preventDefault();
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;
  const errorDiv = document.getElementById('login-error');
  errorDiv.style.display = 'none';

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });

    if (response.ok) {
      const data = await response.json();
      authToken = data.access_token;
      currentUser = data.user;
      localStorage.setItem('authToken', authToken);
      localStorage.setItem('currentUser', JSON.stringify(currentUser));
      showDashboard();
      loadDashboardData();
      document.getElementById('login-username').value = '';
      document.getElementById('login-password').value = '';
    } else {
      const error = await response.json();
      errorDiv.textContent = error.detail || 'Login failed';
      errorDiv.style.display = 'block';
    }
  } catch (err) {
    errorDiv.textContent = 'Error: ' + err.message;
    errorDiv.style.display = 'block';
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const full_name = document.getElementById('register-name').value.trim();
  const email = document.getElementById('register-email').value.trim();
  const username = document.getElementById('register-username').value.trim();
  const phone = document.getElementById('register-phone').value.trim();
  const password = document.getElementById('register-password').value;
  const errorDiv = document.getElementById('register-error');
  errorDiv.style.display = 'none';

  // Validation
  if (!full_name || !email || !username || !phone || !password) {
    errorDiv.textContent = 'All fields are required';
    errorDiv.style.display = 'block';
    return;
  }

  if (password.length < 8) {
    errorDiv.textContent = 'Password must be at least 8 characters long';
    errorDiv.style.display = 'block';
    return;
  }

  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name, email, username, phone, password })
    });

    if (response.ok) {
      const data = await response.json();
      authToken = data.access_token;
      currentUser = data.user;
      localStorage.setItem('authToken', authToken);
      localStorage.setItem('currentUser', JSON.stringify(currentUser));
      showDashboard();
      loadDashboardData();
      document.getElementById('register-name').value = '';
      document.getElementById('register-email').value = '';
      document.getElementById('register-username').value = '';
      document.getElementById('register-phone').value = '';
      document.getElementById('register-password').value = '';
    } else {
      const error = await response.json();
      errorDiv.textContent = error.detail || 'Registration failed';
      errorDiv.style.display = 'block';
    }
  } catch (err) {
    errorDiv.textContent = 'Error: ' + err.message;
    errorDiv.style.display = 'block';
  }
}

function handleLogout() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem('authToken');
  localStorage.removeItem('currentUser');
  showAuthPage();
  switchToLogin();
}

// ==================== PREFERENCES MANAGEMENT ====================
async function savePreferences() {
  const email = document.getElementById('user-email').value;
  const phone = document.getElementById('user-phone').value;
  const emailNotif = document.getElementById('email-notifications').checked;
  const phoneNotif = document.getElementById('phone-notifications').checked;
  const msgDiv = document.getElementById('pref-message');

  try {
    const response = await fetch('/api/auth/preferences', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        email,
        phone,
        email_notifications: emailNotif,
        phone_notifications: phoneNotif
      })
    });

    if (response.ok) {
      const updated = await response.json();
      currentUser = updated;
      localStorage.setItem('currentUser', JSON.stringify(currentUser));
      
      // Update UI fields with the saved values
      document.getElementById('user-email').value = currentUser.email || '';
      document.getElementById('user-phone').value = currentUser.phone || '';
      document.getElementById('email-notifications').checked = currentUser.email_notifications;
      document.getElementById('phone-notifications').checked = currentUser.phone_notifications;
      
      msgDiv.textContent = 'Preferences saved successfully!';
      msgDiv.style.display = 'block';
      msgDiv.style.color = '#22863a';
      msgDiv.style.background = '#f6ffed';
      setTimeout(() => msgDiv.style.display = 'none', 3000);
    } else {
      msgDiv.textContent = 'Failed to save preferences';
      msgDiv.style.display = 'block';
      msgDiv.style.color = '#e53e3e';
      msgDiv.style.background = '#fff5f5';
    }
  } catch (err) {
    msgDiv.textContent = 'Error: ' + err.message;
    msgDiv.style.display = 'block';
  }
}

// ==================== DASHBOARD DATA LOADING ====================
let pm25Chart, aqiChart, pollutantsChart;

async function loadDashboardData() {
  fetchLatestReading();
  fetchHistoryData();
  setInterval(fetchLatestReading, 30000); // Refresh every 30s
  setInterval(fetchHistoryData, 60000); // Refresh every 60s
}

async function fetchLatestReading() {
  try {
    const response = await fetch('/api/latest');
    if (response.ok) {
      const data = await response.json();
      document.getElementById('aqi-value').textContent = data.aqi?.toFixed(1) || '--';
      document.getElementById('aqi-category').textContent = data.aqi_category || '--';
      
      const details = `
        PM2.5: ${data.pm2_5?.toFixed(1) || '--'} µg/m³
        Temperature: ${data.temperature?.toFixed(1) || '--'}°C
        Humidity: ${data.humidity?.toFixed(0) || '--'}%
        Device: ${data.device_id || '--'}
      `;
      document.getElementById('aqi-details').textContent = details;
    }
  } catch (err) {
    console.error('Error fetching latest:', err);
  }
}

async function fetchHistoryData() {
  try {
    const response = await fetch('/api/history?minutes=1440');
    if (response.ok) {
      const data = await response.json();
      updateCharts(data);
      updateTable(data);
    }
  } catch (err) {
    console.error('Error fetching history:', err);
  }
}

function updateCharts(readings) {
  if (!readings || readings.length === 0) return;

  const labels = readings.map(r => new Date(r.timestamp).toLocaleTimeString());
  const pm25Data = readings.map(r => r.pm2_5);
  const aqiData = readings.map(r => r.aqi);
  const pollutantNames = ['PM2.5', 'PM10', 'CO', 'NO₂', 'O₃', 'SO₂'];
  const pollutantData = [
    (readings.reduce((sum, r) => sum + (r.pm2_5 || 0), 0) / readings.length).toFixed(1),
    (readings.reduce((sum, r) => sum + (r.pm10 || 0), 0) / readings.length).toFixed(1),
    (readings.reduce((sum, r) => sum + (r.co || 0), 0) / readings.length).toFixed(2),
    (readings.reduce((sum, r) => sum + (r.no2 || 0), 0) / readings.length).toFixed(1),
    (readings.reduce((sum, r) => sum + (r.o3 || 0), 0) / readings.length).toFixed(1),
    (readings.reduce((sum, r) => sum + (r.so2 || 0), 0) / readings.length).toFixed(1),
  ];

  // PM2.5 Trend
  const ctx1 = document.getElementById('pm25-chart');
  if (pm25Chart) pm25Chart.destroy();
  pm25Chart = new Chart(ctx1, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'PM2.5 (µg/m³)',
        data: pm25Data,
        borderColor: '#667eea',
        backgroundColor: 'rgba(102, 126, 234, 0.1)',
        tension: 0.3,
        fill: true
      }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });

  // AQI Distribution
  const ctx2 = document.getElementById('aqi-chart');
  if (aqiChart) aqiChart.destroy();
  aqiChart = new Chart(ctx2, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'AQI',
        data: aqiData,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.3,
        fill: true
      }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });

  // Pollutants Bar Chart
  const ctx3 = document.getElementById('pollutants-chart');
  if (pollutantsChart) pollutantsChart.destroy();
  pollutantsChart = new Chart(ctx3, {
    type: 'bar',
    data: {
      labels: pollutantNames,
      datasets: [{
        label: 'Average (24h)',
        data: pollutantData,
        backgroundColor: '#667eea'
      }]
    },
    options: { responsive: true, maintainAspectRatio: false, indexAxis: 'y' }
  });
}

function updateTable(readings) {
  const tbody = document.getElementById('history-table').querySelector('tbody');
  tbody.innerHTML = '';

  if (!readings || readings.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">No data available</td></tr>';
    return;
  }

  readings.slice(0, 20).forEach(r => {
    const row = tbody.insertRow();
    const time = new Date(r.timestamp).toLocaleString();
    
    const aqiBadgeClass = r.aqi < 50 ? 'aqi-good' : r.aqi < 100 ? 'aqi-moderate' : 'aqi-unhealthy';
    
    row.innerHTML = `
      <td>${time}</td>
      <td>${r.device_id}</td>
      <td><span class="aqi-badge ${aqiBadgeClass}">${r.aqi?.toFixed(1)}</span></td>
      <td>${r.pm2_5?.toFixed(1)}</td>
      <td>${r.pm10?.toFixed(1)}</td>
      <td>${r.no2?.toFixed(1)}</td>
      <td>${r.o3?.toFixed(1)}</td>
      <td>${r.temperature?.toFixed(1)}°C</td>
    `;
  });
}

function setAQIState(aqi) {
  document.body.classList.remove("aqi-good", "aqi-moderate", "aqi-bad");
  if (aqi <= 50) document.body.classList.add("aqi-good");
  else if (aqi <= 100) document.body.classList.add("aqi-moderate");
  else document.body.classList.add("aqi-bad");
}

async function fetchLatest() {
  try {
    const res = await fetch(`${API_PREFIX}/latest`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const aqi = (typeof data.aqi === 'number') ? data.aqi : 0;
    document.getElementById("aqi").textContent = aqi.toFixed(1);
    document.getElementById("category").textContent = data.aqi_category || "--";
    document.getElementById("risk").textContent = data.risk_level || "--";
    document.getElementById("device").textContent = data.device_id || "--";
    document.getElementById("time").textContent = data.timestamp ? new Date(data.timestamp).toLocaleTimeString() : "--";

    setAQIState(aqi);
    renderAQIGauge(aqi);
  } catch (err) {
    console.error('fetchLatest error', err);
    document.getElementById("aqi").textContent = "--";
    document.getElementById("category").textContent = "Error";
    document.getElementById("risk").textContent = "--";
    document.getElementById("time").textContent = "--";
  }
}

async function fetchNotifications() {
  try {
    const res = await fetch(`${API_PREFIX}/notifications?limit=5`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    
    if (data.latest) {
      // Show latest notification in banner
      const banner = document.getElementById('notification-banner');
      banner.textContent = data.latest.message;
      banner.style.display = 'block';
      
      // Also show in browser if available
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Air Quality Alert', {
          body: data.latest.message,
          icon: '/static/icon.png'
        });
      }
    }
    
    // Display notification list
    const notifList = document.getElementById('notifications-list');
    const card = document.getElementById('notifications-card');
    
    if (data.notifications && data.notifications.length > 0) {
      card.style.display = 'block';
      notifList.innerHTML = '';
      data.notifications.forEach(n => {
        const div = document.createElement('div');
        div.style.cssText = 'padding:8px;margin:6px 0;background:white;border-radius:4px;font-size:13px;border-left:3px solid #10b981';
        const time = new Date(n.timestamp).toLocaleString();
        div.innerHTML = `<strong>${time}</strong><br>${n.message}`;
        notifList.appendChild(div);
      });
    }
  } catch (err) {
    console.error('fetchNotifications error', err);
  }
}

function getAQIColor(aqi){
  // standard AQI categories with colors
  if (aqi <= 50) return '#10b981'; // Good (green)
  if (aqi <= 100) return '#f59e0b'; // Moderate/yellow
  if (aqi <= 150) return '#f97316'; // Unhealthy for Sensitive (orange)
  if (aqi <= 200) return '#ef4444'; // Unhealthy (red)
  if (aqi <= 300) return '#9f1239'; // Very Unhealthy (purple)
  return '#7c2d12'; // Hazardous (brown)
}

function renderAQIGauge(aqi){
  // draw doughnut gauge with Chart.js
  const canvas = document.getElementById('aqi-gauge');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const max = 500; // AQI cap for gauge
  const value = Math.max(0, Math.min(aqi || 0, max));
  const remainder = Math.max(0, max - value);
  const color = getAQIColor(value);

  if (chartGauge) chartGauge.destroy();

  chartGauge = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['AQI','Remaining'],
      datasets: [{ data: [value, remainder], backgroundColor: [color, '#e6eef8'], hoverBackgroundColor: [color, '#e6eef8'], borderWidth: 0 }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%'
    },
    plugins: [{
      id: 'centerText',
      beforeDraw: function(chart){
        const w = chart.width, h = chart.height;
        const ctx = chart.ctx;
        ctx.restore();
        const fontSize = (h / 6).toFixed(0);
        ctx.font = fontSize + 'px Arial';
        ctx.textBaseline = 'middle';
        const text = (value).toFixed(0);
        const textX = Math.round((w - ctx.measureText(text).width) / 2);
        const textY = h / 2 - 6;
        ctx.fillStyle = '#0f172a';
        ctx.fillText(text, textX, textY);

        // small label
        ctx.font = Math.max(10, fontSize/3) + 'px Arial';
        const sub = 'AQI';
        const subX = Math.round((w - ctx.measureText(sub).width) / 2);
        ctx.fillStyle = '#6b7280';
        ctx.fillText(sub, subX, textY + fontSize/1.4);
        ctx.save();
      }
    }]
  });
}

async function fetchHistory() {
  try {
    const res = await fetch(`${API_PREFIX}/history?minutes=60`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const labels = data.map(r => new Date(r.timestamp).toLocaleTimeString());
    const pm25 = data.map(r => r.pm2_5);

    const ctx = document.getElementById("chart").getContext("2d");

    if (chart) chart.destroy(); // re-draw

    chart = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          label: "PM2.5 (µg/m³)",
          data: pm25,
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37,99,235,0.08)',
          fill: true,
          tension: 0.2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { display: true, title: { display: true, text: "Time" } },
          y: { display: true, title: { display: true, text: "PM2.5 (µg/m³)" } }
        }
      }
    });
  } catch (err) {
    console.error('fetchHistory error', err);
    // show empty chart if error
    if (chart) { chart.destroy(); chart = null; }
  }
}

async function fetchHistoryTable(minutes = 1440) {
  try {
    const res = await fetch(`${API_PREFIX}/history?minutes=${minutes}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    // store full history and apply filters/pagination
    fullHistory = Array.isArray(data) ? data : (data.value || []);
    // sort by timestamp ascending (oldest first)
    fullHistory.sort((a,b) => new Date(a.timestamp) - new Date(b.timestamp));
    currentPage = 1;
    applyFilterAndPaginate();
  } catch (err) {
    console.error('fetchHistoryTable error', err);
    fullHistory = [];
    renderHistoryTable([]);
  }
}

function computePollutantAverages(rows) {
  // compute average of pm2_5, pm10, co, no2, o3, so2
  const sums = { pm2_5:0, pm10:0, co:0, no2:0, o3:0, so2:0 };
  let count = 0;
  for (const r of rows) {
    if (r.pm2_5 != null) sums.pm2_5 += Number(r.pm2_5);
    if (r.pm10 != null) sums.pm10 += Number(r.pm10);
    if (r.co != null) sums.co += Number(r.co);
    if (r.no2 != null) sums.no2 += Number(r.no2);
    if (r.o3 != null) sums.o3 += Number(r.o3);
    if (r.so2 != null) sums.so2 += Number(r.so2);
    count++;
  }
  if (count === 0) return null;
  return {
    pm2_5: sums.pm2_5 / count,
    pm10: sums.pm10 / count,
    co: sums.co / count,
    no2: sums.no2 / count,
    o3: sums.o3 / count,
    so2: sums.so2 / count,
  };
}

function renderAQITrend(rows) {
  // use rows (already sorted oldest-first) and plot aqi vs time
  const cvs = document.getElementById('aqi-trend-chart');
  if (!cvs) return;
  const ctx = cvs.getContext('2d');
  const labels = rows.map(r => new Date(r.timestamp).toLocaleString());
  const data = rows.map(r => r.aqi != null ? Number(r.aqi) : null);

  if (chartAQI) chartAQI.destroy();
  chartAQI = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets: [{ label: 'AQI', data, borderColor: '#ef4444', backgroundColor: 'rgba(239,68,68,0.08)', tension: 0.2, fill: true }] },
    options: { responsive: true, maintainAspectRatio: false, scales: { x:{ display:true }, y:{ title:{ display:true, text:'AQI' } } } }
  });
}

function renderPollutantsBar(rows) {
  const cvs = document.getElementById('pollutants-bar');
  if (!cvs) return;
  const ctx = cvs.getContext('2d');
  const avg = computePollutantAverages(rows) || { pm2_5:0,pm10:0,co:0,no2:0,o3:0,so2:0 };
  const labels = ['PM2.5','PM10','CO','NO2','O3','SO2'];
  const values = [avg.pm2_5, avg.pm10, avg.co, avg.no2, avg.o3, avg.so2];

  if (chartPoll) chartPoll.destroy();
  chartPoll = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Average', data: values, backgroundColor: ['#2563eb','#1f2937','#f97316','#b91c1c','#10b981','#7c3aed'] }] },
    options: { responsive:true, maintainAspectRatio:false, scales:{ y:{ beginAtZero:true } } }
  });
}

function renderHistoryTable(rows) {
  const tbody = document.querySelector('#history-table tbody');
  tbody.innerHTML = '';
  if (!rows || rows.length === 0) {
    const tr = document.createElement('tr');
    const td = document.createElement('td');
    td.colSpan = 7;
    td.textContent = 'No data';
    td.style.color = '#6b7280';
    tr.appendChild(td);
    tbody.appendChild(tr);
    return;
  }

  // Apply pagination
  const start = (currentPage - 1) * pageSize;
  const pageRows = rows.slice(start, start + pageSize);

  pageRows.forEach((r, idx) => {
    const tr = document.createElement('tr');
    const globalIndex = start + idx + 1; // 1-based serial number for display
    const cells = [
      globalIndex,
      r.timestamp || '--',
      r.device_id || '--',
      (r.pm2_5 != null) ? r.pm2_5 : '--',
      (r.pm10 != null) ? r.pm10 : '--',
      (r.aqi != null) ? Number(r.aqi).toFixed(2) : '--',
      r.aqi_category || '--',
      r.risk_level || '--'
    ];
    cells.forEach(c => {
      const td = document.createElement('td');
      td.textContent = c;
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  renderPaginationControls(rows.length);

  if (autoScroll) {
    const tableWrap = document.querySelector('.table-wrap');
    if (tableWrap) tableWrap.scrollTop = tableWrap.scrollHeight;
  }
}

function exportTableToCSV(filename = 'airquality_history.csv') {
  const rows = [];
  const headers = Array.from(document.querySelectorAll('#history-table thead th')).map(h => h.textContent.trim());
  rows.push(headers.join(','));

  document.querySelectorAll('#history-table tbody tr').forEach(tr => {
    const cols = Array.from(tr.querySelectorAll('td')).map(td => '"' + (td.textContent || '').replace(/"/g, '""') + '"');
    if (cols.length) rows.push(cols.join(','));
  });

  const csv = rows.join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

async function refreshAll() {
  await Promise.all([fetchLatest(), fetchHistory(), fetchHistoryTable(), fetchNotifications()]);
}

document.addEventListener('DOMContentLoaded', () => {
  // Check if user is already logged in
  checkAuth().then(isLoggedIn => {
    // Show auth modal if not logged in
    if (!isLoggedIn) {
      openAuthModal();
    }
  });
  
  // Request notification permission
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
  
  // wire up buttons
  document.getElementById('refresh-table').addEventListener('click', () => fetchHistoryTable());
  document.getElementById('export-csv').addEventListener('click', () => exportTableToCSV());

  document.getElementById('filter-device').addEventListener('input', () => applyFilterAndPaginate());
  document.getElementById('filter-minutes').addEventListener('change', () => fetchHistoryTable(Number(document.getElementById('filter-minutes').value)));
  document.getElementById('page-size').addEventListener('change', (e) => { pageSize = Number(e.target.value); currentPage = 1; applyFilterAndPaginate(); });
  document.getElementById('auto-scroll').addEventListener('change', (e) => { autoScroll = e.target.checked; });
  // CSV upload wiring
  const uploadBtn = document.getElementById('upload-csv-btn');
  const fileInput = document.getElementById('csv-file');
  uploadBtn.addEventListener('click', async () => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) { alert('Please pick a CSV file first'); return; }
    await handleCSVFileUpload(file);
  });

  // pagination buttons (will be delegated)
  document.addEventListener('click', (e) => {
    if (e.target && e.target.matches('.page-prev')) { if (currentPage > 1) { currentPage--; applyFilterAndPaginate(); }}
    if (e.target && e.target.matches('.page-next')) { currentPage++; applyFilterAndPaginate(); }
  });

  // initial load
  refreshAll();
  setInterval(refreshAll, 30000);
  // Check notifications more frequently (every 5 minutes)
  setInterval(fetchNotifications, 300000);
});

function applyFilterAndPaginate() {
  const filter = document.getElementById('filter-device').value.trim().toLowerCase();
  let filtered = fullHistory;
  if (filter) filtered = fullHistory.filter(r => (r.device_id || '').toLowerCase().includes(filter));
  // keep the stored sort (fullHistory is oldest-first), but pagination will slice accordingly
  // filtered stays in same order (oldest-first)
  // ensure currentPage valid
  const maxPage = Math.max(1, Math.ceil(filtered.length / pageSize));
  if (currentPage > maxPage) currentPage = maxPage;
  renderHistoryTable(filtered);
  // update additional visualizations with the filtered set (show trend & averages for filtered rows)
  renderAQITrend(filtered);
  renderPollutantsBar(filtered);
}

function renderPaginationControls(totalItems) {
  const footer = document.querySelector('.table-footer');
  if (!footer) {
    const parent = document.getElementById('history-table-card');
    const f = document.createElement('div');
    f.className = 'table-footer';
    parent.appendChild(f);
  }
  const footerEl = document.querySelector('.table-footer');
  footerEl.innerHTML = '';

  const pagination = document.createElement('div');
  pagination.className = 'pagination';
  const prev = document.createElement('button'); prev.className = 'page-btn page-prev'; prev.textContent = 'Prev';
  const next = document.createElement('button'); next.className = 'page-btn page-next'; next.textContent = 'Next';
  pagination.appendChild(prev);
  pagination.appendChild(next);

  const info = document.createElement('div'); info.className = 'page-info';
  const maxPage = Math.max(1, Math.ceil(totalItems / pageSize));
  info.textContent = `Page ${currentPage} / ${maxPage} — ${totalItems} rows`;

  footerEl.appendChild(pagination);
  footerEl.appendChild(info);
}

// ---------- CSV upload handling ----------
function parseCSVText(text) {
  const lines = text.split(/\r?\n/).filter(l => l.trim() !== '');
  if (lines.length === 0) return { headers: [], rows: [] };
  const headerLine = lines.shift();
  // basic CSV split handling quoted fields
  const splitLine = (line) => {
    const re = /("([^"]|"")*"|[^,]+|)(?=,|$)/g;
    const matches = line.match(re) || [];
    return matches.map(s => s.replace(/^,|,$/g, '').trim().replace(/^"|"$/g, '').replace(/""/g, '"'));
  };
  const headers = splitLine(headerLine).map(h => h.trim());
  const rows = lines.map(line => {
    const vals = splitLine(line);
    const obj = {};
    for (let i = 0; i < headers.length; i++) {
      obj[headers[i]] = vals[i] !== undefined ? vals[i] : '';
    }
    return obj;
  });
  return { headers, rows };
}

function normalizeReadingObject(raw) {
  // map required fields (expects same names as backend ReadingIn)
  const fields = ["device_id","pm2_5","pm10","co","no2","o3","so2","temperature","humidity"];
  const out = {};
  for (const f of fields) {
    if (!(f in raw)) return { error: `Missing column: ${f}` };
    if (f === 'device_id') out[f] = String(raw[f]);
    else {
      const v = raw[f];
      if (v === '' || v === null || v === undefined) return { error: `Empty numeric value for ${f}` };
      const n = Number(String(v).trim());
      if (Number.isNaN(n)) return { error: `Invalid number for ${f}: ${v}` };
      out[f] = n;
    }
  }
  return { value: out };
}

async function handleCSVFileUpload(file) {
  const statusEl = document.getElementById('upload-status');
  statusEl.textContent = 'Reading file...';
  const text = await file.text();
  const { headers, rows } = parseCSVText(text);
  if (!headers.length) { statusEl.textContent = 'No headers found in CSV'; return; }

  const payload = [];
  let rowIndex = 0;
  for (const raw of rows) {
    rowIndex++;
    const { error, value } = normalizeReadingObject(raw);
    if (error) {
      statusEl.textContent = `Row ${rowIndex} skipped: ${error}`;
      continue;
    }
    payload.push(value);
  }

  if (!payload.length) { statusEl.textContent = 'No valid rows to upload'; return; }

  statusEl.textContent = `Uploading ${payload.length} rows...`;
  try {
    const res = await fetch(`${API_PREFIX}/ingest_bulk`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const txt = await res.text();
      statusEl.textContent = `Upload failed: ${res.status} ${txt}`;
      return;
    }
    const created = await res.json();
    statusEl.textContent = `Upload complete: ${created.length} rows inserted`;
    // refresh table
    await fetchHistoryTable();
  } catch (err) {
    console.error('upload error', err);
    statusEl.textContent = `Upload error: ${err.message}`;
  }
}

// --- Authentication Functions ---
function saveAuthToken(token) {
  authToken = token;
  localStorage.setItem('auth_token', token);
}

function getAuthToken() {
  return localStorage.getItem('auth_token');
}

function clearAuth() {
  authToken = null;
  currentUser = null;
  localStorage.removeItem('auth_token');
  updateAuthUI();
}

function updateAuthUI() {
  const authBtn = document.getElementById('auth-btn');
  const userDisplay = document.getElementById('user-display');
  
  if (currentUser) {
    authBtn.textContent = 'Logout';
    authBtn.onclick = () => { clearAuth(); location.reload(); };
    userDisplay.textContent = `👤 ${currentUser.username}`;
  } else {
    authBtn.textContent = 'Login';
    authBtn.onclick = () => openAuthModal();
    userDisplay.textContent = '';
  }
}

function getAuthHeaders() {
  const token = getAuthToken();
  if (token) {
    return { 'Authorization': `Bearer ${token}` };
  }
  return {};
}

// Check if already logged in on load
async function checkAuth() {
  const token = getAuthToken();
  if (token) {
    try {
      authToken = token;
      const res = await fetch(`${API_PREFIX}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        currentUser = await res.json();
        updateAuthUI();
        return true;
      }
    } catch (err) {
      console.error('Auth check error', err);
      clearAuth();
    }
  }
  return false;
}

