// script.js - Integrated with Backend

// Backend API Configuration
const BACKEND_API_URL = 'http://localhost:7276';  // Change this to your backend URL

// Credentials fetched from backend (single source of truth: .env file)
// These will be populated on page load from /config endpoint
let BOLNA_EXECUTIONS_BASE = '';
let BOLNA_EXECUTION_DETAIL = '';
let AUTH_TOKEN = '';
let AGENT_ID = '';

const drivers = [
  { name: "Ajay", vehicleNumber: "BD 7326", phone: "+919876543210", destination: "Mumbai Warehouse" }
];

const elements = {
  callBtn: document.getElementById('callBtn'),
  endCallBtn: document.getElementById('endCallBtn'),
  callStatus: document.getElementById('callStatus'),
  callDuration: document.getElementById('callDuration'),
  durationText: document.querySelector('.duration-text'),
  avatarRing: document.getElementById('avatarRing'),
  loadingOverlay: document.getElementById('loadingOverlay'),
  statusMessage: document.getElementById('statusMessage'),
  muteBtn: document.getElementById('muteBtn'),
  speakerBtn: document.getElementById('speakerBtn'),
  addCallBtn: document.getElementById('addCallBtn'),
  driverList: document.getElementById('driverList'),
  contactName: document.getElementById('contactName'),
  contactNumber: document.getElementById('contactNumber'),
  avatarText: document.getElementById('avatarText'),
  executionId: document.getElementById('executionId'),
  fetchExecutionBtn: document.getElementById('fetchExecutionBtn'),
  executionDetail: document.getElementById('executionDetail'),
  loadExecutionsBtn: document.getElementById('loadExecutionsBtn'),
  executionsList: document.getElementById('executionsList'),
  executionsSummary: document.getElementById('executionsSummary'),
  prevPageBtn: document.getElementById('prevPageBtn'),
  nextPageBtn: document.getElementById('nextPageBtn'),
  pageIndicator: document.getElementById('pageIndicator'),
  agentIdDisplay: document.getElementById('agentIdDisplay')
};

let state = {
  callState: 'idle',
  callTimer: null,
  currentPage: 1,
  pageSize: 10,
  hasMore: false
};

// Track which execution IDs have already been saved (avoid duplicates)
const savedExecutionIds = new Set();

// UI Helpers
const updateCallStatus = (text) => elements.callStatus.textContent = text;

const showLoading = (show) => elements.loadingOverlay.classList.toggle('hidden', !show);

const showMessage = (msg, duration = 3000) => {
  elements.statusMessage.textContent = msg;
  elements.statusMessage.classList.remove('opacity-0');
  setTimeout(() => elements.statusMessage.classList.add('opacity-0'), duration);
};

const toggleRinging = (on) => elements.avatarRing.classList.toggle('hidden', !on);

const updateButtons = () => {
  elements.callBtn.classList.toggle('hidden', state.callState !== 'idle');
  elements.endCallBtn.classList.toggle('hidden', !['ringing', 'connected'].includes(state.callState));
  elements.callDuration.classList.toggle('hidden', state.callState !== 'connected');
  elements.prevPageBtn.disabled = state.currentPage <= 1;
  elements.nextPageBtn.disabled = !state.hasMore;
};

const startTimer = () => {
  const startTime = Date.now();
  state.callTimer = setInterval(() => {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const secs = String(elapsed % 60).padStart(2, '0');
    elements.durationText.textContent = `${mins}:${secs}`;
  }, 1000);
};

const stopTimer = () => clearInterval(state.callTimer);

// Render Drivers
const renderDrivers = () => {
  elements.driverList.innerHTML = '';
  drivers.forEach(driver => {
    const btn = document.createElement('button');
    btn.className = 'w-full flex items-center gap-4 p-4 rounded-lg border border-gray-300 hover:bg-blue-50 hover:border-blue-400 transition text-left';
    btn.innerHTML = `
      <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white font-bold text-xl">
        ${driver.name[0].toUpperCase()}
      </div>
      <div>
        <div class="font-semibold text-gray-900">${driver.name}</div>
        <div class="text-sm text-gray-600">${driver.vehicleNumber} • ${driver.phone}</div>
      </div>
    `;
    btn.onclick = () => startCall(driver);
    elements.driverList.appendChild(btn);
  });
};

// Call Initiation
const startCall = (driver) => {
  if (state.callState !== 'idle') {
    showMessage('A call is already in progress', 3000);
    return;
  }

  elements.contactName.textContent = driver.name;
  elements.contactNumber.textContent = driver.phone;
  elements.avatarText.textContent = driver.name[0].toUpperCase();

  // Pass driver object to backend
  initiateBolnaCall(driver);
};

const initiateBolnaCall = async (driver) => {
  state.callState = 'connecting';
  updateCallStatus('Connecting...');
  updateButtons();
  showLoading(true);

  try {
    const payload = {
      driver_name: driver.name || '',
      phone_number: driver.phone || '',
      vehicle_number: driver.vehicleNumber || '',
      destination: driver.destination || ''
    };
    console.log('Sending call request to backend:', payload);

    const res = await fetch(`${BACKEND_API_URL}/trigger-call`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    let data;
    try {
      data = await res.json();
    } catch (e) {
      const text = await res.text();
      console.error('Backend returned non-JSON response:', text);
      throw new Error(`Server returned ${res.status}: ${text.slice(0, 50)}...`);
    }

    if (!res.ok) {
      const errorDetail = typeof data.detail === 'object' ? JSON.stringify(data.detail) : (data.detail || 'Call failed');
      throw new Error(errorDetail);
    }

    showMessage(`Call initiated! Call ID: ${data.call_id}`, 6000);

    // Simulate call flow
    setTimeout(() => {
      state.callState = 'ringing';
      updateCallStatus('Ringing...');
      toggleRinging(true);
      updateButtons();
    }, 2000);

    setTimeout(() => {
      state.callState = 'connected';
      updateCallStatus('Connected');
      toggleRinging(false);
      startTimer();
      updateButtons();
      showMessage('Call connected!', 3000);
    }, 6000);

  } catch (err) {
    console.error('Initiate call error:', err);
    showMessage(`Call failed: ${err.message}`, 8000);
    resetToIdle();
  } finally {
    showLoading(false);
  }
};

const endCall = () => {
  if (!['ringing', 'connected'].includes(state.callState)) return;

  state.callState = 'ended';
  updateCallStatus('Call Ended');
  toggleRinging(false);
  stopTimer();
  updateButtons();
  showMessage('Call ended', 3000);

  setTimeout(resetToIdle, 2000);
};

const resetToIdle = () => {
  state.callState = 'idle';
  updateCallStatus('Ready to initiate call');
  elements.contactName.textContent = 'Select Driver';
  elements.contactNumber.textContent = 'Choose from list below';
  elements.avatarText.textContent = 'K';
  elements.durationText.textContent = '00:00';
  updateButtons();
};

// Full History Fetching (EXACTLY like your original working code)
const fetchExecutions = async ({ pageNumber, pageSize }) => {
  const res = await fetch(`${BOLNA_EXECUTIONS_BASE}/${AGENT_ID}/executions?page_number=${pageNumber}&page_size=${pageSize}`, {
    headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
  });
  if (!res.ok) throw new Error(`Error ${res.status}: ${await res.text()}`);
  return res.json();
};

const fetchExecutionById = async (executionId) => {
  const res = await fetch(`${BOLNA_EXECUTION_DETAIL}/${executionId}`, {
    headers: { 'Authorization': `Bearer ${AUTH_TOKEN}` }
  });
  if (!res.ok) throw new Error(`Error ${res.status}: ${await res.text()}`);
  return res.json();
};

// ── Save transcript JSON to backend ──────────────────────────────────
const saveTranscriptToBackend = async (exec) => {
  // Skip if already saved in this session
  if (savedExecutionIds.has(exec.id)) {
    console.log(`Already saved ${exec.id}, skipping`);
    return true;
  }

  try {
    // Match driver by comparing last 10 digits of phone number
    const toNumber = (exec.telephony_data?.to_number || '').replace(/\D/g, '');
    const toNumberSuffix = toNumber.slice(-10);
    const matchedDriver = drivers.find(d => {
      const dPhone = d.phone.replace(/\D/g, '').slice(-10);
      return dPhone === toNumberSuffix;
    }) || null;

    const payload = {
      execution_id: exec.id,
      status: exec.status,
      created_at: exec.created_at,
      conversation_time: exec.conversation_time ?? null,
      transcript: exec.transcript ?? null,
      extracted_data: exec.extracted_data ?? null,
      telephony_data: exec.telephony_data ?? null,
      cost_breakdown: exec.cost_breakdown ?? null,
      error_message: exec.error_message ?? null,
      // Pre-filled trip context
      driver_name: matchedDriver?.name ?? '',
      vehicle_number: matchedDriver?.vehicleNumber ?? '',
      source_location: '',  // Add source location per driver if available
      destination_location: matchedDriver?.destination ?? '',
    };

    console.log(`Saving transcript for ${exec.id}, matched driver:`, matchedDriver?.name || 'none');

    const res = await fetch(`${BACKEND_API_URL}/save-transcript`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(`Save failed: ${res.status}`);
    const result = await res.json();
    console.log(`Transcript saved for ${exec.id}:`, result.filename);
    savedExecutionIds.add(exec.id);
    return true;
  } catch (err) {
    console.error(`Failed to save transcript for ${exec.id}:`, err);
    return false;
  }
};

const renderExecutionDetail = (exec) => {
  elements.executionDetail.innerHTML = '';
  const card = document.createElement('div');
  card.className = 'bg-gray-800 border border-gray-700 rounded-xl p-6';

  const top = document.createElement('div');
  top.className = 'flex justify-between flex-wrap gap-4';
  top.innerHTML = `
    <div>
      <div class="font-bold text-white">Execution ID: ${exec.id}</div>
      <div class="text-sm text-gray-400 mt-1">
        Status: ${exec.status} • Duration: ${exec.conversation_time ?? 0}s • ${new Date(exec.created_at).toLocaleString()}
      </div>
      <div class="text-sm text-gray-400">To: ${exec.telephony_data?.to_number ?? ''} • From: ${exec.telephony_data?.from_number ?? ''}</div>
      ${exec.error_message ? `<div class="text-red-400 mt-2">Error: ${exec.error_message}</div>` : ''}
    </div>
    <div class="flex items-center gap-3">
      ${exec.telephony_data?.recording_url ? `<audio controls class="h-10"><source src="${exec.telephony_data.recording_url}" type="audio/wav"></audio>` : ''}
      <button class="save-json-btn px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition flex items-center gap-1" data-exec-id="${exec.id}">
        <i class="fas fa-save"></i> Save JSON
      </button>
    </div>
  `;
  card.appendChild(top);

  // Attach save handler
  const saveBtn = top.querySelector('.save-json-btn');
  saveBtn.onclick = async () => {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    const ok = await saveTranscriptToBackend(exec);
    saveBtn.innerHTML = ok
      ? '<i class="fas fa-check"></i> Saved'
      : '<i class="fas fa-times"></i> Failed';
    saveBtn.className = saveBtn.className.replace('bg-green-600 hover:bg-green-700', ok ? 'bg-gray-600' : 'bg-red-600');
    if (ok) showMessage('Transcript JSON saved!', 3000);
  };

  if (exec.transcript) {
    const details = document.createElement('details');
    details.className = 'mt-4';
    details.innerHTML = `<summary class="cursor-pointer text-blue-400 font-medium">Transcript</summary>
      <pre class="mt-2 bg-gray-900 p-4 rounded text-sm text-gray-300 whitespace-pre-wrap">${exec.transcript}</pre>`;
    card.appendChild(details);
  }

  if (exec.extracted_data && Object.keys(exec.extracted_data).length) {
    const details = document.createElement('details');
    details.className = 'mt-4';
    details.innerHTML = `<summary class="cursor-pointer text-blue-400 font-medium">Extracted Data</summary>
      <pre class="mt-2 bg-gray-900 p-4 rounded text-sm text-gray-300">${JSON.stringify(exec.extracted_data, null, 2)}</pre>`;
    card.appendChild(details);
  }

  if (exec.cost_breakdown) {
    const details = document.createElement('details');
    details.className = 'mt-4';
    details.innerHTML = `<summary class="cursor-pointer text-blue-400 font-medium">Cost Breakdown</summary>
      <pre class="mt-2 bg-gray-900 p-4 rounded text-sm text-gray-300">${JSON.stringify(exec.cost_breakdown, null, 2)}</pre>`;
    card.appendChild(details);
  }

  elements.executionDetail.appendChild(card);
};

const renderExecutions = (data) => {
  const items = data.data || [];
  elements.executionsSummary.textContent = `Total: ${data.total ?? items.length} | Showing: ${items.length}`;
  elements.executionsList.innerHTML = items.length === 0 ? '<div class="text-center text-gray-500 py-8">No calls found</div>' : '';

  items.forEach(exec => {
    const card = document.createElement('div');
    card.className = 'bg-gray-800 border border-gray-700 rounded-xl p-6 mb-4';

    const top = document.createElement('div');
    top.className = 'flex justify-between flex-wrap gap-4';
    top.innerHTML = `
      <div>
        <div class="font-bold text-white text-lg">${exec.telephony_data?.to_number || 'Unknown'}</div>
        <div class="text-sm text-gray-400 mt-1">${exec.status} • ${exec.telephony_data?.duration ?? 0}s • ${new Date(exec.created_at).toLocaleString()}</div>
      </div>
      <div class="flex items-center gap-3">
        ${exec.telephony_data?.recording_url ? `<audio controls class="h-10"><source src="${exec.telephony_data.recording_url}" type="audio/wav"></audio>` : ''}
        <button class="save-json-btn px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition flex items-center gap-1" data-exec-id="${exec.id}">
          <i class="fas fa-save"></i> Save JSON
        </button>
      </div>
    `;
    card.appendChild(top);

    // Attach save handler
    const saveBtn = top.querySelector('.save-json-btn');
    saveBtn.onclick = async () => {
      saveBtn.disabled = true;
      saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
      const ok = await saveTranscriptToBackend(exec);
      saveBtn.innerHTML = ok
        ? '<i class="fas fa-check"></i> Saved'
        : '<i class="fas fa-times"></i> Failed';
      saveBtn.className = saveBtn.className.replace('bg-green-600 hover:bg-green-700', ok ? 'bg-gray-600' : 'bg-red-600');
    };

    if (exec.transcript) {
      const details = document.createElement('details');
      details.className = 'mt-4';
      details.innerHTML = `<summary class="cursor-pointer text-blue-400 font-medium">Transcript</summary>
        <pre class="mt-2 bg-gray-900 p-4 rounded text-sm text-gray-300 whitespace-pre-wrap">${exec.transcript}</pre>`;
      card.appendChild(details);
    }

    if (exec.extracted_data && Object.keys(exec.extracted_data).length) {
      const details = document.createElement('details');
      details.className = 'mt-4';
      details.innerHTML = `<summary class="cursor-pointer text-blue-400 font-medium">Extracted Data</summary>
        <pre class="mt-2 bg-gray-900 p-4 rounded text-sm text-gray-300">${JSON.stringify(exec.extracted_data, null, 2)}</pre>`;
      card.appendChild(details);
    }

    elements.executionsList.appendChild(card);
  });
};

const loadHistory = async (page = 1) => {
  showLoading(true);
  try {
    const result = await fetchExecutions({ pageNumber: page, pageSize: state.pageSize });
    state.hasMore = Boolean(result.has_more);
    state.currentPage = page;
    renderExecutions(result);
    elements.pageIndicator.textContent = `Page ${state.currentPage}`;
    updateButtons();
  } catch (e) {
    showMessage(`Failed to load history: ${e.message}`, 6000);
  } finally {
    showLoading(false);
  }
};

const loadSingleExecution = async () => {
  const id = elements.executionId.value.trim();
  if (!id) return showMessage('Please enter an Execution ID', 3000);

  showLoading(true);
  try {
    const exec = await fetchExecutionById(id);
    renderExecutionDetail(exec);
    showMessage('Execution details loaded', 3000);
  } catch (e) {
    showMessage(`Failed: ${e.message}`, 6000);
  } finally {
    showLoading(false);
  }
};

// Fetch configuration from backend (single source of truth)
const loadConfig = async () => {
  try {
    const res = await fetch(`${BACKEND_API_URL}/config`);
    if (!res.ok) throw new Error('Failed to load config from backend');
    
    const config = await res.json();
    
    // Populate global variables from backend
    AUTH_TOKEN = config.bolna_api_key;
    AGENT_ID = config.agent_id;
    BOLNA_EXECUTIONS_BASE = config.bolna_executions_base;
    BOLNA_EXECUTION_DETAIL = config.bolna_execution_detail;
    
    // Update UI
    if (elements.agentIdDisplay) {
      elements.agentIdDisplay.textContent = `Agent ID: ${AGENT_ID.slice(0, 8)}...`;
    }
    
    console.log('Configuration loaded from backend:', { agent_id: AGENT_ID });
    return true;
  } catch (e) {
    console.error('Failed to load config from backend:', e);
    return false;
  }
};

// Initialization
document.addEventListener('DOMContentLoaded', async () => {
  // Load config from backend first
  showLoading(true);
  await loadConfig();
  showLoading(false);
  
  renderDrivers();
  updateButtons();

  elements.callBtn.onclick = () => showMessage('Click a driver from the list to call', 4000);
  elements.endCallBtn.onclick = endCall;

  elements.loadExecutionsBtn.onclick = () => loadHistory(1);
  elements.prevPageBtn.onclick = () => state.currentPage > 1 && loadHistory(state.currentPage - 1);
  elements.nextPageBtn.onclick = () => state.hasMore && loadHistory(state.currentPage + 1);
  elements.fetchExecutionBtn.onclick = loadSingleExecution;
});