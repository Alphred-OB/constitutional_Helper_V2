
const chatBox = document.getElementById('chat-box');
const welcomeState = document.getElementById('welcome-state');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const languageSelect = document.getElementById('languageSelect');

const API_URL = window.location.origin;

function addMessage(role, content, context = []) {
    welcomeState.style.display = 'none';
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} message-in w-full`;
    
    if (role === 'user') {
        messageDiv.innerHTML = `
            <div class="max-w-[75%] bg-emerald-600 text-white rounded-[24px] rounded-tr-none px-7 py-4 shadow-xl shadow-emerald-600/10">
                <p class="text-[15px] leading-relaxed font-medium">${escapeHtml(content)}</p>
            </div>
        `;
        chatBox.appendChild(messageDiv);
    } else {
        const msgId = 'msg-' + Date.now();
        const msgDivId = 'div-' + msgId;
        messageDiv.id = msgDivId;
        
        const contextHtml = context.length > 0 ? `
            <div class="mt-8 pt-8 border-t border-zinc-100 dark:border-white/5 space-y-4">
                <p class="text-[9px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                    <i data-lucide="database" class="w-3 h-3"></i> Context Sources
                </p>
                <div class="flex flex-wrap gap-2">
                    ${context.map(c => `<span class="source-pill">${c.article || c.chapter}</span>`).join('')}
                </div>
            </div>
        ` : '';

        messageDiv.innerHTML = `
            <div class="flex gap-6 max-w-[95%] items-start w-full">
                <div class="w-10 h-10 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border)] flex-shrink-0 flex items-center justify-center shadow-sm">
                    <i data-lucide="bot" class="w-5 h-5 text-emerald-600"></i>
                </div>
                <div class="flex-1 space-y-4 min-w-0">
                    <div class="message-bubble rounded-[32px] rounded-tl-none px-10 py-8 shadow-2xl shadow-zinc-200/10 dark:shadow-none">
                        <div class="flex justify-between items-center mb-8">
                            <div class="flex items-center gap-3">
                                <span class="text-[10px] font-extrabold text-emerald-600 uppercase tracking-widest px-2 py-1 bg-emerald-50 dark:bg-emerald-500/10 rounded">Constitutional Analysis</span>
                                <div class="w-1.5 h-1.5 rounded-full bg-zinc-200"></div>
                                <span class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">v2.5</span>
                            </div>
                            <button onclick="playAudio('${msgId}')" class="audio-btn w-10 h-10 rounded-full flex items-center justify-center text-zinc-400 hover:text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-500/10 transition-all border border-transparent hover:border-emerald-200/50">
                                <i data-lucide="volume-2" class="w-5 h-5"></i>
                            </button>
                        </div>
                        <div id="${msgId}" class="prose prose-zinc prose-lg max-w-none text-[var(--text)]">
                            ${formatMarkdown(content)}
                        </div>
                        <div id="ctx-${msgId}">${contextHtml}</div>
                    </div>
                </div>
            </div>
        `;
        chatBox.appendChild(messageDiv);
        return { msgId, msgDivId };
    }
    scrollToBottom();
}

let currentAudio = null;
let currentPlayingId = null;

async function playAudio(msgId) {
    const btn = document.querySelector(`[onclick="playAudio('${msgId}')"]`);
    const icon = btn.querySelector('i');

    if (currentPlayingId === msgId && currentAudio) {
        if (!currentAudio.paused) {
            currentAudio.pause();
            icon.setAttribute('data-lucide', 'volume-2');
            lucide.createIcons();
            return;
        } else {
            currentAudio.play();
            icon.setAttribute('data-lucide', 'pause');
            lucide.createIcons();
            return;
        }
    }

    if (currentAudio) {
        currentAudio.pause();
        const oldBtn = document.querySelector(`[onclick="playAudio('${currentPlayingId}')"]`);
        if (oldBtn) {
            oldBtn.querySelector('i').setAttribute('data-lucide', 'volume-2');
        }
    }

    const text = document.getElementById(msgId).innerText;
    const lang = languageSelect.value;
    
    try {
        const response = await fetch(`${API_URL}/audio?text=${encodeURIComponent(text)}&language=${lang}`);
        const data = await response.json();
        
        if (data.audio_b64) {
            currentAudio = new Audio("data:audio/mp3;base64," + data.audio_b64);
            currentPlayingId = msgId;
            currentAudio.onplay = () => { icon.setAttribute('data-lucide', 'pause'); lucide.createIcons(); };
            currentAudio.onended = () => { icon.setAttribute('data-lucide', 'volume-2'); lucide.createIcons(); currentPlayingId = null; };
            currentAudio.play();
        }
    } catch (error) { console.error("Audio playback failed", error); }
}

function showThinking() {
    const thinkingDiv = document.createElement('div');
    thinkingDiv.id = 'thinking';
    thinkingDiv.className = 'flex justify-start message-in';
    thinkingDiv.innerHTML = `
        <div class="flex gap-6 max-w-[95%] items-start">
            <div class="w-10 h-10 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border)] flex-shrink-0 flex items-center justify-center shadow-sm">
                <i data-lucide="bot" class="w-5 h-5 text-emerald-600"></i>
            </div>
            <div class="bg-[var(--bg-secondary)] border border-[var(--border)] rounded-[32px] rounded-tl-none px-6 py-4 flex items-center gap-2 shadow-sm">
                <div class="flex gap-1">
                    <div class="typing-dot"></div>
                    <div class="typing-dot" style="animation-delay: 0.2s"></div>
                    <div class="typing-dot" style="animation-delay: 0.4s"></div>
                </div>
                <span class="text-[10px] text-zinc-400 font-bold uppercase tracking-widest ml-2">Thinking...</span>
            </div>
        </div>
    `;
    chatBox.appendChild(thinkingDiv);
    lucide.createIcons();
    scrollToBottom();
}

function removeThinking() {
    const thinking = document.getElementById('thinking');
    if (thinking) thinking.remove();
}

async function sendMessage() {
    const text = userInput.value.trim();
    if (!text) return;
    
    userInput.value = '';
    userInput.style.height = 'auto';
    addMessage('user', text);
    
    showThinking();
    
    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: text,
                language: languageSelect.value
            })
        });
        
        if (!response.ok) throw new Error('Network response was not ok');
        
        removeThinking();
        const { msgId } = addMessage('bot', '');
        const botTextDiv = document.getElementById(msgId);
        const botCtxDiv = document.getElementById(`ctx-${msgId}`);
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';
        let streamBuffer = '';
        let contextFound = false;
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) {
                // Final safety check if stream ended without delimiter
                if (!contextFound && streamBuffer.length > 0) {
                    fullContent = streamBuffer;
                    botTextDiv.innerHTML = formatMarkdown(fullContent);
                }
                break;
            }
            
            const chunk = decoder.decode(value, { stream: true });
            
            if (!contextFound) {
                streamBuffer += chunk;
                if (streamBuffer.includes('--CONTEXT_END--')) {
                    const parts = streamBuffer.split('--CONTEXT_END--');
                    try {
                        const jsonPart = parts[0].trim();
                        if (jsonPart.startsWith('{')) {
                            const contextData = JSON.parse(jsonPart);
                            if (contextData.context) {
                                botCtxDiv.innerHTML = `
                                    <div class="mt-8 pt-8 border-t border-zinc-100 dark:border-white/5 space-y-4">
                                        <p class="text-[9px] font-bold text-zinc-400 uppercase tracking-widest flex items-center gap-2">
                                            <i data-lucide="database" class="w-3 h-3"></i> Context Sources
                                        </p>
                                        <div class="flex flex-wrap gap-2">
                                            ${contextData.context.map(c => `<span class="source-pill">${c.article || c.chapter}</span>`).join('')}
                                        </div>
                                    </div>
                                `;
                            }
                        }
                    } catch (e) { console.error("Context parse error", e); }
                    
                    fullContent = parts[1] || '';
                    contextFound = true;
                    if (fullContent.trim()) {
                        botTextDiv.innerHTML = formatMarkdown(fullContent);
                    } else {
                        botTextDiv.innerHTML = '<span class="text-zinc-400 italic animate-pulse">Generating analysis...</span>';
                    }
                }
            } else {
                fullContent += chunk;
                botTextDiv.innerHTML = formatMarkdown(fullContent) || '<span class="text-zinc-400 italic animate-pulse">Generating analysis...</span>';
            }
            scrollToBottom();
        }
        
        lucide.createIcons();
    } catch (error) {
        removeThinking();
        addMessage('bot', 'Failed to connect to the server. Make sure the API is running.');
    }
}

function quickAsk(text) {
    userInput.value = text;
    sendMessage();
}

function scrollToBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}

function formatMarkdown(content) {
    // Safety check: If the content is raw JSON (from an old API or error), parse it
    if (content.trim().startsWith('{')) {
        try {
            const data = JSON.parse(content);
            if (data.answer) return formatMarkdown(data.answer);
            if (data.detail) return `<div class="p-4 bg-red-50 text-red-600 rounded-xl">${data.detail}</div>`;
        } catch (e) { /* Not valid JSON, continue */ }
    }

    // Fix for literal \n strings appearing in stream
    let sanitized = content.replace(/\\n/g, '\n');
    
    // Check if we have the structured headers
    const parts = sanitized.split(/### (ANALYSIS|REFERENCES)/i);
    
    if (parts.length > 1) {
        let html = '';
        for (let i = 1; i < parts.length; i += 2) {
            const header = parts[i].toUpperCase();
            const body = (parts[i + 1] || '').trim();
            
            if (header === 'ANALYSIS') {
                html += `
                    <div class="section-analysis">
                        <div class="section-header"><i data-lucide="brain-circuit" class="w-3 h-3"></i> Analysis</div>
                        <div class="prose prose-sm dark:prose-invert leading-relaxed">${marked.parse(body)}</div>
                    </div>
                `;
            } else if (header === 'REFERENCES') {
                html += `
                    <div class="section-references">
                        <div class="section-header"><i data-lucide="book-open" class="w-3 h-3"></i> Reference</div>
                        <div class="prose prose-sm dark:prose-invert space-y-2 leading-relaxed">${marked.parse(body)}</div>
                    </div>
                `;
            }
        }
        return html;
    }
    
    // Fallback to regular markdown
    return `<div class="prose prose-sm dark:prose-invert leading-relaxed">${marked.parse(sanitized)}</div>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

sendBtn.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
