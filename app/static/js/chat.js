// === State ===
let currentConversationId = null;
let isLoading = false;
let authToken = localStorage.getItem('token');

// === Auth Check ===
if (!authToken) {
    window.location.href = '/login';
}

// === User Info ===
const user = JSON.parse(localStorage.getItem('user') || '{}');
document.getElementById('userInfo').innerHTML = `
    <div class="user-name">👤 ${user.name || 'User'}</div>
`;

// === API Helper ===
async function apiCall(url, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`,
        ...options.headers,
    };
    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return;
    }
    return response;
}

// === DOM Elements ===
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const chatMessages = document.getElementById('chatMessages');
const welcomeMessage = document.getElementById('welcomeMessage');
const typingIndicator = document.getElementById('typingIndicator');
const newChatBtn = document.getElementById('newChatBtn');
const conversationList = document.getElementById('conversationList');
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');
const sidebarOverlay = document.getElementById('sidebarOverlay');
const logoutBtn = document.getElementById('logoutBtn');

// === Init ===
document.addEventListener('DOMContentLoaded', () => {
    loadConversations();
    setupEventListeners();
});

function setupEventListeners() {
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('input', onInputChange);
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    newChatBtn.addEventListener('click', startNewChat);
    sidebarToggle.addEventListener('click', toggleSidebar);
    sidebarOverlay.addEventListener('click', toggleSidebar);
    logoutBtn.addEventListener('click', logout);
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

function onInputChange() {
    // Auto-resize textarea
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
    // Enable/disable send button
    sendBtn.disabled = !messageInput.value.trim() || isLoading;
}

// === Conversations ===

async function startNewChat() {
    try {
        const res = await apiCall('/api/chat/new', { method: 'POST' });
        if (!res) return;
        const data = await res.json();
        currentConversationId = data.conversation_id;
        clearChat();
        loadConversations();
        closeSidebar();
    } catch (err) {
        showError('Failed to create new conversation');
    }
}

async function loadConversations() {
    try {
        const res = await apiCall('/api/history');
        if (!res) return;
        const conversations = await res.json();
        renderConversationList(conversations);
    } catch (err) {
        console.error('Failed to load conversations:', err);
    }
}

function renderConversationList(conversations) {
    conversationList.innerHTML = '';
    conversations.forEach(conv => {
        const item = document.createElement('div');
        item.className = 'conversation-item' + (conv.id === currentConversationId ? ' active' : '');
        item.innerHTML = `
            <span class="title">${escapeHtml(conv.title)}</span>
            <button class="delete-btn" title="Delete">&times;</button>
        `;
        item.querySelector('.title').addEventListener('click', () => loadConversation(conv.id));
        item.querySelector('.delete-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            deleteConversation(conv.id);
        });
        conversationList.appendChild(item);
    });
}

async function loadConversation(id) {
    try {
        const res = await apiCall(`/api/history/${id}`);
        if (!res) return;
        const data = await res.json();
        currentConversationId = id;
        clearChat();
        data.messages.forEach(msg => {
            addMessage(msg.role, msg.content, msg.diagnosis_data);
        });
        loadConversations();
        closeSidebar();
    } catch (err) {
        showError('Failed to load conversation');
    }
}

async function deleteConversation(id) {
    try {
        await apiCall(`/api/history/${id}`, { method: 'DELETE' });
        if (currentConversationId === id) {
            currentConversationId = null;
            clearChat();
            showWelcome();
        }
        loadConversations();
    } catch (err) {
        showError('Failed to delete conversation');
    }
}

// === Messaging ===

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || isLoading) return;

    // Create conversation if needed
    if (!currentConversationId) {
        try {
            const res = await apiCall('/api/chat/new', { method: 'POST' });
            if (!res) return;
            const data = await res.json();
            currentConversationId = data.conversation_id;
        } catch (err) {
            showError('Failed to create conversation');
            return;
        }
    }

    hideWelcome();
    addMessage('user', text);
    messageInput.value = '';
    messageInput.style.height = 'auto';
    sendBtn.disabled = true;
    setLoading(true);

    try {
        const res = await apiCall('/api/chat', {
            method: 'POST',
            body: JSON.stringify({
                conversation_id: currentConversationId,
                message: text,
            }),
        });

        if (!res) return;
        
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || 'Request failed');
        }

        const data = await res.json();
        addMessage('assistant', data.message, data.diagnosis_data, data.follow_up_questions);
        loadConversations(); // Refresh sidebar (title may have changed)
    } catch (err) {
        showError(err.message || 'Failed to get response. Please try again.');
    } finally {
        setLoading(false);
    }
}

// === Rendering ===

function addMessage(role, content, diagnosisData = null, followUpQuestions = null) {
    const msgEl = document.createElement('div');
    msgEl.className = `message ${role}`;

    const avatar = role === 'user' ? '&#128100;' : '&#129658;';
    const renderedContent = renderMarkdown(content);

    let diagnosisHtml = '';
    if (diagnosisData) {
        diagnosisHtml = renderDiagnosisCard(diagnosisData);
    }

    let followUpHtml = '';
    if (followUpQuestions && followUpQuestions.length > 0) {
        followUpHtml = `
            <div class="follow-up-questions">
                <p class="follow-up-label">You might want to tell me:</p>
                ${followUpQuestions.map(q => `
                    <button class="follow-up-btn" onclick="useExample('${escapeHtml(q)}')">${escapeHtml(q)}</button>
                `).join('')}
            </div>
        `;
    }

    msgEl.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            ${renderedContent}
            ${diagnosisHtml}
            ${followUpHtml}
        </div>
    `;

    chatMessages.appendChild(msgEl);
    scrollToBottom();
}

function renderDiagnosisCard(data) {
    const severityClass = `severity-${data.severity || 'mild'}`;
    const confidencePct = Math.round((data.confidence || 0) * 100);

    let symptomsHtml = '';
    if (data.symptoms_identified && data.symptoms_identified.length) {
        symptomsHtml = `
            <div class="diagnosis-section">
                <h4>Symptoms Found</h4>
                <ul>${data.symptoms_identified.map(s => `<li>${escapeHtml(s.replace(/_/g, ' '))}</li>`).join('')}</ul>
            </div>`;
    }

    let remediesHtml = '';
    if (data.remedies && data.remedies.length) {
        remediesHtml = `
            <div class="diagnosis-section">
                <h4>Remedies</h4>
                <ul>${data.remedies.map(r => `<li>${escapeHtml(r)}</li>`).join('')}</ul>
            </div>`;
    }

    let medsHtml = '';
    if (data.medications && data.medications.length) {
        medsHtml = `
            <div class="diagnosis-section">
                <h4>Medications</h4>
                <ul>${data.medications.map(m => `<li>${escapeHtml(m)}</li>`).join('')}</ul>
            </div>`;
    }

    let specialistHtml = '';
    if (data.specialist) {
        specialistHtml = `
            <div class="diagnosis-section">
                <h4>Specialist</h4>
                <p>${escapeHtml(data.specialist)}</p>
            </div>`;
    }

    // Severity-based suggestions
    let suggestionsHtml = '';
    if (data.suggestions) {
        const sug = data.suggestions;
        suggestionsHtml = `
            <div class="suggestions-card ${sug.type}">
                <div class="suggestions-header">
                    <span class="suggestions-icon">${sug.icon || '💡'}</span>
                    <span class="suggestions-title">${escapeHtml(sug.title)}</span>
                </div>
                <ul class="suggestions-list">
                    ${sug.items.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
                </ul>
                ${sug.note ? `<p class="suggestions-note">${escapeHtml(sug.note)}</p>` : ''}
            </div>`;
    }

    let topPredictions = '';
    if (data.top_3 && data.top_3.length) {
        const bars = data.top_3.map(d => {
            const pct = Math.round((d.confidence || 0) * 100);
            return `
                <div class="prediction-bar">
                    <span class="name">${escapeHtml(d.disease)}</span>
                    <div class="bar"><div class="bar-fill" style="width: ${pct}%"></div></div>
                    <span class="pct">${pct}%</span>
                </div>`;
        }).join('');
        topPredictions = `<div class="top-predictions"><h4>Top Predictions</h4>${bars}</div>`;
    }

    // Emergency warning
    let emergencyHtml = '';
    if (data.emergency_warning) {
        emergencyHtml = `
            <div class="emergency-warning">
                <span class="emergency-icon">🚨</span>
                <p>${escapeHtml(data.emergency_warning)}</p>
            </div>`;
    }

    return `
        <div class="diagnosis-card">
            ${emergencyHtml}
            <div class="diagnosis-header">
                <span class="diagnosis-disease">${escapeHtml(data.disease)}</span>
                <span class="confidence-badge">${confidencePct}% match</span>
                <span class="severity-badge ${severityClass}">${escapeHtml(data.severity || 'Unknown')}</span>
            </div>
            <div class="diagnosis-details">
                ${symptomsHtml}
                ${remediesHtml}
                ${medsHtml}
                ${specialistHtml}
            </div>
            ${suggestionsHtml}
            ${topPredictions}
        </div>`;
}

function renderMarkdown(text) {
    if (!text) return '';
    let html = escapeHtml(text);
    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
    // Bullet lists
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    // Numbered lists
    html = html.replace(/^\d+\.\s(.+)$/gm, '<li>$1</li>');
    // Paragraphs
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
    html = `<p>${html}</p>`;
    // Clean up empty paragraphs
    html = html.replace(/<p><\/p>/g, '');
    return html;
}

// === Helpers ===

function clearChat() {
    chatMessages.innerHTML = '';
}

function showWelcome() {
    if (!chatMessages.querySelector('.welcome-message')) {
        chatMessages.innerHTML = `
            <div class="welcome-message" id="welcomeMessage">
                <div class="welcome-icon">&#129658;</div>
                <h2>AI Healthcare Assistant</h2>
                <p>Describe your symptoms and I'll help you understand what might be going on.</p>
                <div class="example-prompts">
                    <button class="example-btn" onclick="useExample('I have a headache and fever')">
                        "I have a headache and fever"
                    </button>
                    <button class="example-btn" onclick="useExample('I feel itchy skin with rashes')">
                        "I feel itchy skin with rashes"
                    </button>
                    <button class="example-btn" onclick="useExample('I have joint pain and fatigue')">
                        "I have joint pain and fatigue"
                    </button>
                </div>
            </div>`;
    }
}

function hideWelcome() {
    const welcome = chatMessages.querySelector('.welcome-message');
    if (welcome) welcome.remove();
}

function setLoading(loading) {
    isLoading = loading;
    typingIndicator.style.display = loading ? 'flex' : 'none';
    sendBtn.disabled = loading || !messageInput.value.trim();
    if (loading) scrollToBottom();
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    const toast = document.createElement('div');
    toast.className = 'error-toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

function toggleSidebar() {
    sidebar.classList.toggle('open');
    sidebarOverlay.classList.toggle('active');
}

function closeSidebar() {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('active');
}

// Global function for example buttons
window.useExample = function(text) {
    messageInput.value = text;
    onInputChange();
    sendMessage();
};
