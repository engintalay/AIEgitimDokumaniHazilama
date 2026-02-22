document.addEventListener('DOMContentLoaded', () => {
    // Register Service Worker for PWA
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/sw.js').then(registration => {
                console.log('SW registered:', registration);
            }).catch(error => {
                console.log('SW registration failed:', error);
            });
        });
    }

    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const appStatus = document.getElementById('app-status');
    const dbCount = document.getElementById('db-count');
    const dbSources = document.getElementById('db-sources');
    const resetDbBtn = document.getElementById('reset-db-btn');
    const globalProgressContainer = document.getElementById('global-progress-container');
    const globalProgressBar = document.getElementById('global-progress-bar');
    const globalProgressText = document.getElementById('global-progress-text');
    const configModelType = document.getElementById('config-model-type');
    const configModelName = document.getElementById('config-model-name');
    const chatHistoryList = document.getElementById('chat-history-list');
    const newChatBtn = document.getElementById('new-chat-btn');
    const sidebar = document.querySelector('.sidebar');
    const settingsBtn = document.getElementById('settings-btn');
    const settingsModal = document.getElementById('settings-modal');
    const reportModal = document.getElementById('report-modal');
    const reportForm = document.getElementById('report-form');
    const reportImage = document.getElementById('report-image');
    const reportImgPreview = document.getElementById('report-img-preview');
    const reportFileLabel = document.getElementById('report-file-label');
    const closeSettings = document.getElementById('close-settings');
    const settingsForm = document.getElementById('settings-form');
    const saveSettingsBtn = document.getElementById('save-settings');
    const micBtn = document.getElementById('mic-btn');
    const activeDocIndicator = document.getElementById('active-doc-indicator');
    const activeDocName = document.getElementById('active-doc-name');
    const clearSourceBtn = document.getElementById('clear-source-btn');

    let selectedSources = [];
    let currentConfig = null;
    let currentChatId = null;

    // Initial load
    updateStats();
    fetchHistory();
    updateActiveDocUI();

    newChatBtn.onclick = startNewChat;

    clearSourceBtn.onclick = () => {
        selectedSources = [];
        updateActiveDocUI();
        updateStats(); // Refresh source list selection
    };

    function startNewChat() {
        currentChatId = null;
        selectedSources = []; // Clear selection for new chat
        console.log("Chat reset: selectedSources cleared.");
        chatWindow.innerHTML = `
            <div class="message bot-message">
                <div class="message-content">
                    Merhaba! Ben doküman asistanınız. Yeni bir sohbet başlattınız. Sorunuzu bekliyorum.
                </div>
            </div>
        `;
        document.querySelectorAll('.history-item').forEach(i => i.classList.remove('active'));
        updateActiveDocUI();
        updateStats(); // Refresh sidebar selection
    }

    async function fetchHistory() {
        try {
            const response = await fetch('/chats');
            const chats = await response.json();
            console.log("Fetched chats:", chats);
            renderHistory(chats);
        } catch (err) {
            console.error('History fetch failed:', err);
        }
    }

    function renderHistory(chats) {
        console.log("Rendering history list, count:", chats.length);
        chatHistoryList.innerHTML = '';
        chats.forEach(chat => {
            const div = document.createElement('div');
            div.className = `history-item ${currentChatId === chat.id ? 'active' : ''}`;
            div.innerHTML = `
                <span class="chat-title" title="${chat.title}">${chat.title.length > 25 ? chat.title.substring(0, 22) + '...' : chat.title}</span>
                <button class="delete-chat-btn" data-id="${chat.id}">✕</button>
            `;
            div.onclick = (e) => {
                if (e.target.classList.contains('delete-chat-btn')) return;
                loadChat(chat.id);
            };
            chatHistoryList.appendChild(div);
        });

        // Delete listeners
        document.querySelectorAll('.delete-chat-btn').forEach(btn => {
            btn.onclick = async (e) => {
                e.stopPropagation();
                const id = e.target.getAttribute('data-id');
                if (confirm('Bu sohbeti silmek istediğinize emin misiniz?')) {
                    await deleteChat(id);
                }
            };
        });
    }

    async function loadChat(chatId) {
        try {
            const response = await fetch(`/chats/${chatId}`);
            const data = await response.json();
            currentChatId = data.id;

            chatWindow.innerHTML = '';
            data.messages.forEach(msg => {
                addMessage(msg.role, msg.content, false, msg.sources, msg.id, msg.stats, msg.reference_details);
            });

            fetchHistory(); // Refresh to update active state
        } catch (err) {
            console.error('Chat load failed:', err);
        }
    }

    async function deleteChat(chatId) {
        try {
            await fetch(`/chats/${chatId}`, { method: 'DELETE' });
            if (currentChatId == chatId) startNewChat();
            fetchHistory();
        } catch (err) {
            console.error('Delete chat failed:', err);
        }
    }

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
    });

    // Handle Upload
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) handleUpload(files[0]);
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) handleUpload(fileInput.files[0]);
    });

    let isUploading = false;

    async function handleUpload(file) {
        if (isUploading) {
            console.warn('Upload already in progress, skipping...');
            return;
        }

        // Cloudflare Free Tier upload limit check (approx 100MB)
        // Skip this check if running on localhost/127.0.0.1
        const hostname = window.location.hostname;
        const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';

        const MAX_FILE_SIZE = 99 * 1024 * 1024; // 99 MB
        if (!isLocalhost && file.size > MAX_FILE_SIZE) {
            addMessage('bot', `❌ <b>Hata:</b> Seçilen dosya (${(file.size / (1024 * 1024)).toFixed(2)} MB) çok büyük. Lütfen 100MB'dan küçük bir dosya seçin.`);
            fileInput.value = '';
            return;
        }

        isUploading = true;

        const jobId = 'job_' + Math.random().toString(36).substr(2, 9);
        console.log(`Starting upload: ${file.name} (Job: ${jobId})`);

        appStatus.textContent = 'İşleniyor...';
        appStatus.classList.add('processing');
        dropZone.style.pointerEvents = 'none';
        dropZone.style.opacity = '0.5';

        // Show progress UI
        globalProgressContainer.style.display = 'flex';
        globalProgressBar.style.width = '0%';
        globalProgressText.textContent = '0%';

        const processingMsg = addMessage('bot', `⌛ <b>${file.name}</b> sunucuya gönderiliyor...<br><span class="spinner"></span> Lütfen bekleyin...`, true);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('job_id', jobId);

        let pollInterval;
        try {
            const xhr = new XMLHttpRequest();
            const uploadPromise = new Promise((resolve, reject) => {
                xhr.upload.onprogress = (e) => {
                    if (e.lengthComputable) {
                        const percent = Math.round((e.loaded / e.total) * 100);
                        globalProgressBar.style.width = percent + '%';
                        globalProgressText.textContent = percent + '%';
                        if (percent === 100) {
                            processingMsg.querySelector('.message-content').innerHTML = `⌛ <b>${file.name}</b> işleniyor, lütfen bekleyin...<br><span class="spinner"></span> Dosya okuma sırasına alındı...`;
                        }
                    }
                };
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) resolve(JSON.parse(xhr.responseText));
                    else reject(new Error(xhr.responseText || 'Sunucu hatası'));
                };
                xhr.onerror = () => reject(new Error('Bağlantı hatası'));
                xhr.open('POST', '/upload');
                xhr.send(formData);
            });

            // Start polling as well (for server-side progress)
            pollInterval = setInterval(async () => {
                try {
                    const pollResponse = await fetch(`/progress/${jobId}`);
                    const pollData = await pollResponse.json();
                    const p = pollData.progress;
                    const statusText = pollData.status;

                    if (p > 0 || statusText) { // Update if server-side processing has actually started
                        globalProgressBar.style.width = p + '%';
                        globalProgressText.textContent = p + '%';
                        const displayStatus = statusText || "Paragraflara ayrılıyor ve vektörleştiriliyor...";
                        processingMsg.querySelector('.message-content').innerHTML = `⌛ <b>${file.name}</b> işleniyor, lütfen bekleyin...<br><span class="spinner"></span> <span style="color:#2563eb; font-weight:500;">${displayStatus}</span> (${p}%)`;
                    }
                    if (parseInt(p) >= 100) clearInterval(pollInterval);
                } catch (err) {
                    console.error('Progress poll failed:', err);
                }
            }, 1000);

            const data = await uploadPromise;

            if (data.error) {
                removeMessage(processingMsg);
                alert(data.error);
                appStatus.textContent = 'Hata';
                appStatus.classList.remove('processing');
                appStatus.style.background = '#dc2626';
            } else {
                removeMessage(processingMsg);
                addFileToSidebar(file.name);
                appStatus.textContent = 'Tamamlandı';
                appStatus.classList.remove('processing');
                appStatus.style.background = '#059669';
                addMessage('bot', `✅ ${data.message}`);
                updateStats();
            }
        } catch (err) {
            removeMessage(processingMsg);
            console.error(err);
            appStatus.textContent = 'Bağlantı Hatası';
            appStatus.classList.remove('processing');
        } finally {
            dropZone.style.pointerEvents = 'auto';
            dropZone.style.opacity = '1';
            fileInput.value = '';
            isUploading = false;

            // Hide progress after a short delay
            setTimeout(() => {
                globalProgressContainer.style.display = 'none';
                clearInterval(pollInterval);
            }, 1000);
        }
    }

    function addFileToSidebar(name) {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `<span>${name}</span> <small>✅</small>`;
        fileList.appendChild(item);
    }

    function updateActiveDocUI() {
        if (selectedSources.length > 0) {
            activeDocName.textContent = selectedSources.join(', ');
            activeDocIndicator.style.display = 'flex';
        } else {
            activeDocIndicator.style.display = 'none';
        }
    }

    // Voice Support
    let recognition = null;
    let isRecording = false;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'tr-TR';

        recognition.onresult = (event) => {
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                }
            }
            if (finalTranscript) {
                userInput.value += (userInput.value ? ' ' : '') + finalTranscript;
                userInput.dispatchEvent(new Event('input')); // Trigger auto-resize
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error', event.error);
            const errors = {
                'not-allowed': 'Mikrofon izni reddedildi. Lütfen tarayıcı ayarlarından mikrofon erişimine izin verin.',
                'network': 'Ağ hatası. Sesli yazma için internet bağlantısı gerekiyor.',
                'no-speech': 'Ses algılanamadı. Lütfen tekrar deneyin.',
                'aborted': 'İşlem iptal edildi.'
            };
            alert('❌ Mikrofon Hatası: ' + (errors[event.error] || event.error));
            stopRecording();
        };

        recognition.onend = () => {
            if (isRecording) recognition.start(); // Keep recording until stopped
        };
    }

    micBtn.onclick = () => {
        if (!recognition) {
            alert('Tarayıcınız sesli yazma desteği sunmuyor.');
            return;
        }

        if (!window.isSecureContext && location.hostname !== 'localhost') {
            alert('❌ Güvenlik Hatası: Sesli yazma özelliği sadece güvenli bağlantılarda (HTTPS) çalışabilir. Lütfen HTTPS üzerinden bağlandığınızdan emin olun.');
            return;
        }

        if (isRecording) {
            stopRecording();
        } else {
            try {
                startRecording();
            } catch (err) {
                console.error('Recognition start failed:', err);
                alert('Mikrofon başlatılamadı. Lütfen izinlerinizi kontrol edin.');
                stopRecording();
            }
        }
    };

    function startRecording() {
        isRecording = true;
        micBtn.classList.add('recording');
        micBtn.textContent = '🛑';
        recognition.start();
    }

    function stopRecording() {
        isRecording = false;
        micBtn.classList.remove('recording');
        micBtn.textContent = '🎤';
        recognition.stop();
    }

    // Handle Chat
    let currentAbortController = null;

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    async function sendMessage() {
        const query = userInput.value.trim();
        if (!query) return;

        userInput.value = '';
        userInput.style.height = 'auto';

        addMessage('user', query + (selectedSources.length > 0 ? ` (Dosya: ${selectedSources.join(', ')})` : ''));

        const loadingMsg = addMessage('bot', `
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
                <span>Düşünüyorum...</span>
                <button class="action-btn stop-btn" style="color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem; background: rgba(239, 68, 68, 0.1);">🛑 Durdur</button>
            </div>
        `, true);

        // Attach abort handler
        currentAbortController = new AbortController();
        const stopBtn = loadingMsg.querySelector('.stop-btn');
        if (stopBtn) {
            stopBtn.onclick = () => {
                if (currentAbortController) {
                    currentAbortController.abort();
                    stopBtn.textContent = 'Durdu';
                    stopBtn.disabled = true;
                }
            };
        }

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, sources: selectedSources, chat_id: currentChatId }),
                signal: currentAbortController.signal
            });

            removeMessage(loadingMsg);

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let botMsgDiv = null;
            let fullText = "";
            let metadata = null;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    const jsonStr = line.replace('data: ', '').trim();
                    if (!jsonStr) continue;

                    try {
                        const data = JSON.parse(jsonStr);
                        if (data.type === 'metadata') {
                            metadata = data;
                            botMsgDiv = addMessage('bot', data.ref_prefix, false, [], null, null, data.reference_details);
                            fullText = data.ref_prefix;
                        } else if (data.type === 'content') {
                            if (!botMsgDiv) {
                                botMsgDiv = addMessage('bot', '', false);
                            }
                            fullText += data.text;
                            botMsgDiv.innerHTML = formatContent(fullText, metadata ? metadata.reference_details : []);
                            chatWindow.scrollTop = chatWindow.scrollHeight;
                        } else if (data.type === 'final') {
                            if (botMsgDiv) {
                                // Add stats and actions
                                const statsHtml = `
                                    <div class="message-stats">
                                        <span class="stat-item" title="Cevap Süresi">⏱️ ${data.stats.time}s</span>
                                        <span class="stat-item" title="Prompt Token">📥 ${data.stats.prompt_tokens}</span>
                                        <span class="stat-item" title="Cevap Token">📤 ${data.stats.completion_tokens}</span>
                                    </div>
                                `;
                                const actionHtml = `
                                    <div class="message-actions">
                                        <button class="action-btn report-btn" title="Hata Bildir">🚩</button>
                                        <button class="action-btn copy-btn" title="Metni Kopyala">📋</button>
                                    </div>
                                `;
                                botMsgDiv.innerHTML += statsHtml + actionHtml;
                                finalizeMessageActions(botMsgDiv, 'bot', fullText, data.message_id);

                                if (!currentChatId && data.chat_id) {
                                    currentChatId = data.chat_id;
                                    fetchHistory();
                                }
                            }
                        } else if (data.type === 'error') {
                            addMessage('bot', `❌ Hata: ${data.message}`);
                        }
                    } catch (e) {
                        console.error('SSE parse error:', e, jsonStr);
                    }
                }
            }
        } catch (err) {
            removeMessage(loadingMsg);
            if (err.name === 'AbortError') {
                console.log('Fetch aborted by user.');
                addMessage('bot', '🛑 <i>İşlem kullanıcı tarafından durduruldu.</i>');
            } else {
                console.error('Send message error:', err);
                addMessage('bot', '❌ Sunucuya erişilemedi. Lütfen internet bağlantınızı kontrol edin.');
            }
        } finally {
            currentAbortController = null;
        }
    }

    async function updateStats() {
        try {
            const response = await fetch('/stats');
            const data = await response.json();
            if (data.count !== undefined) {
                dbCount.textContent = data.count.toLocaleString();
            }
            if (data.sources) {
                renderSourceList(data.sources);
            }
        } catch (err) {
            console.error('Stats loading error:', err);
        }
    }

    function renderSourceList(sources) {
        dbSources.innerHTML = '';
        sources.forEach(source => {
            const div = document.createElement('div');
            div.className = `source-item ${selectedSources.includes(source.name) ? 'selected' : ''}`;

            const privacyIcon = source.is_public ? '🌐' : '🔒';
            const privacyTitle = source.is_public ? 'Herkes görebilir' : 'Sadece siz';

            let actionHtml = `
                <button onclick="window.openVectorModal('${source.name}')" class="view-vector-btn" title="Vektörleri Görüntüle / Ara" style="background: none; border: none; cursor: pointer; padding: 5px; font-size: inherit;">👁️</button>
            `;
            if (source.is_owner) {
                actionHtml += `
                    <button class="toggle-public-btn" data-source="${source.name}" data-public="${source.is_public}" title="${source.is_public ? 'Özel yap' : 'Paylaş'}">
                        ${privacyIcon}
                    </button>
                    <button class="delete-source-btn" data-source="${source.name}" title="Bu kaynağı sil">🗑️</button>
                `;
            } else {
                actionHtml += `<span class="shared-badge" title="Paylaşılan doküman">${privacyIcon}</span>`;
            }

            div.innerHTML = `
                <span title="${source.name}">${source.name.length > 20 ? source.name.substring(0, 17) + '...' : source.name}</span>
                <div class="source-actions">
                    ${actionHtml}
                </div>
            `;

            div.onclick = (e) => {
                if (e.target.closest('button') || e.target.closest('a')) return;

                const idx = selectedSources.indexOf(source.name);
                if (idx > -1) {
                    selectedSources.splice(idx, 1);
                    div.classList.remove('selected');
                } else {
                    selectedSources.push(source.name);
                    div.classList.add('selected');
                }
                updateActiveDocUI();
            };

            dbSources.appendChild(div);
        });

        // Add delete listeners
        document.querySelectorAll('.delete-source-btn').forEach(btn => {
            btn.onclick = async (e) => {
                const source = e.currentTarget.getAttribute('data-source');
                if (confirm(`'${source}' kaynağını ve ilgili tüm paragrafları silmek istediğinize emin misiniz?`)) {
                    await deleteSource(source);
                }
            };
        });

        // Add toggle listeners
        document.querySelectorAll('.toggle-public-btn').forEach(btn => {
            btn.onclick = async (e) => {
                const source = e.currentTarget.getAttribute('data-source');
                const isPublic = e.currentTarget.getAttribute('data-public') === 'true';
                await togglePublic(source, !isPublic);
            };
        });
    }

    async function togglePublic(source, isPublic) {
        try {
            const response = await fetch('/toggle_public', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source, is_public: isPublic })
            });
            const data = await response.json();
            if (data.error) alert(data.error);
            else {
                addMessage('bot', `🌐 ${data.message}`);
                updateStats();
            }
        } catch (err) {
            console.error(err);
        }
    }

    async function deleteSource(source) {
        try {
            const response = await fetch('/delete_source', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ source })
            });
            const data = await response.json();
            if (data.error) alert(data.error);
            else {
                if (selectedSources.includes(source)) {
                    selectedSources = selectedSources.filter(s => s !== source);
                }
                addMessage('bot', `🗑️ ${source} başarıyla silindi.`);
                updateStats();
            }
        } catch (err) {
            console.error(err);
        }
    }

    if (resetDbBtn) {
        resetDbBtn.onclick = async () => {
            if (confirm('TÜM veri tabanını sıfırlamak istediğinize emin misiniz? Bu işlem geri alınamaz.')) {
                try {
                    const response = await fetch('/reset_db', { method: 'POST' });
                    const data = await response.json();
                    if (data.error) alert(data.error);
                    else {
                        addMessage('bot', `🚨 ${data.message}`);
                        updateStats();
                    }
                } catch (err) {
                    console.error(err);
                }
            }
        };
    }

    function formatContent(text, referenceDetails = []) {
        let processedText = text;
        const thinkRegex = /<think>([\s\S]*?)(?:<\/think>|$)/gi;
        if (processedText.match(thinkRegex)) {
            processedText = processedText.replace(thinkRegex, (match, p1) => {
                return `<details class="think-block" open><summary>🧠 Düşünce Süreci</summary><div class="think-content">${p1.trim().replace(/\n/g, '<br>')}</div></details>`;
            });
        }

        let referenceHtml = '';
        if (referenceDetails && referenceDetails.length > 0) {
            const refs = referenceDetails.map((ref, idx) => `
                <div class="ref-item">
                    <div class="ref-header"><strong>Referans #${idx + 1}</strong> (${ref.source})</div>
                    <div class="ref-content">${ref.content.replace(/\n/g, '<br>')}</div>
                </div>
            `).join('');
            referenceHtml = `
                <details class="references-detail-block">
                    <summary>📚 Referans Detaylarını Göster</summary>
                    <div class="references-container">${refs}</div>
                </details>
            `;
        }

        processedText = processedText.replace(/\n/g, '<br>');
        return `
            <div class="message-content">${processedText}</div>
            ${referenceHtml}
        `;
    }

    function addMessage(role, text, isLoading = false, sources = [], messageId = null, stats = null, referenceDetails = []) {
        const div = document.createElement('div');
        div.className = `message ${role}-message`;

        if (isLoading) {
            div.innerHTML = `<div class="message-content">${text}</div>`;
            chatWindow.appendChild(div);
            return div;
        }

        let html = formatContent(text, referenceDetails);

        let statsHtml = '';
        if (role === 'bot' && stats) {
            statsHtml = `
                <div class="message-stats">
                    <span class="stat-item" title="Cevap Süresi">⏱️ ${stats.time}s</span>
                    <span class="stat-item" title="Prompt Token">📥 ${stats.prompt_tokens}</span>
                    <span class="stat-item" title="Cevap Token">📤 ${stats.completion_tokens}</span>
                </div>
            `;
        }

        let actionHtml = '';
        if (role === 'user') {
            actionHtml = `
                <div class="message-actions">
                    <button class="action-btn copy-btn" title="Kopyala">📋</button>
                    <button class="action-btn rerun-btn" title="Tekrar Çalıştır">🔄</button>
                </div>
            `;
        } else {
            actionHtml = `
                <div class="message-actions">
                    <button class="action-btn report-btn" title="Hata Bildir">🚩</button>
                    <button class="action-btn copy-btn" title="Metni Kopyala">📋</button>
                </div>
            `;
        }

        div.innerHTML = html + statsHtml + actionHtml;
        if (sources && sources.length > 0) {
            div.innerHTML += `<div class="sources">Kaynaklar: ${sources.join(', ')}</div>`;
        }

        chatWindow.appendChild(div);
        chatWindow.scrollTop = chatWindow.scrollHeight;
        finalizeMessageActions(div, role, text, messageId);
        return div;
    }

    function finalizeMessageActions(div, role, text, messageId) {
        if (role === 'user') {
            const cleanText = text.includes(' (Dosya:') ? text.split(' (Dosya:')[0] : text;
            const copyBtn = div.querySelector('.copy-btn');
            if (copyBtn) copyBtn.onclick = () => {
                userInput.value = cleanText;
                userInput.focus();
                userInput.dispatchEvent(new Event('input'));
            };
            const rerunBtn = div.querySelector('.rerun-btn');
            if (rerunBtn) rerunBtn.onclick = () => {
                userInput.value = cleanText;
                sendMessage();
            };
        } else {
            const copyBtn = div.querySelector('.copy-btn');
            if (copyBtn) copyBtn.onclick = () => {
                navigator.clipboard.writeText(text);
                const originalText = copyBtn.textContent;
                copyBtn.textContent = '✅';
                setTimeout(() => copyBtn.textContent = originalText, 1000);
            };
            const reportBtn = div.querySelector('.report-btn');
            if (reportBtn) reportBtn.onclick = () => openReportModal(messageId);
        }
    }

    // Reporting Logic
    window.openReportModal = (messageId) => {
        document.getElementById('report-message-id').value = messageId || '';
        document.getElementById('report-content').value = '';
        reportImage.value = '';
        reportImgPreview.style.display = 'none';
        reportFileLabel.querySelector('span').textContent = '📸 Görsel Ekle (Opsiyonel)';
        reportModal.classList.add('active');
    };

    window.closeReportModal = () => {
        reportModal.classList.remove('active');
    };

    reportImage.onchange = () => {
        const file = reportImage.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                reportImgPreview.src = e.target.result;
                reportImgPreview.style.display = 'block';
                reportFileLabel.querySelector('span').textContent = 'Görsel Seçildi: ' + file.name;
            };
            reader.readAsDataURL(file);
        }
    };

    reportForm.onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData();
        formData.append('content', document.getElementById('report-content').value);
        formData.append('message_id', document.getElementById('report-message-id').value);
        if (reportImage.files[0]) {
            formData.append('image', reportImage.files[0]);
        }

        try {
            const response = await fetch('/report', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (data.message) {
                alert(data.message);
                closeReportModal();
            } else alert('Hata: ' + data.error);
        } catch (err) {
            console.error('Report submission failed:', err);
            alert('Rapor gönderilemedi.');
        }
    };

    function removeMessage(el) {
        el.remove();
    }

    // Settings Functionality
    settingsBtn.onclick = async () => {
        await loadSettings();
        settingsModal.classList.add('active');
    };

    closeSettings.onclick = () => {
        settingsModal.classList.remove('active');
    };

    const refreshModelsBtn = document.getElementById('refresh-models-btn');
    if (refreshModelsBtn) {
        refreshModelsBtn.onclick = async () => {
            const originalText = refreshModelsBtn.innerHTML;
            refreshModelsBtn.innerHTML = '⌛ Yenileniyor...';
            refreshModelsBtn.disabled = true;

            await updateAvailableModels(configModelName.value);

            refreshModelsBtn.innerHTML = originalText;
            refreshModelsBtn.disabled = false;
        };
    }

    window.onclick = (e) => {
        if (e.target === settingsModal) settingsModal.classList.remove('active');
    };

    async function loadSettings() {
        try {
            const response = await fetch('/config');
            currentConfig = await response.json();

            // Fill form
            const m = currentConfig.model;
            configModelType.value = m.type;
            document.getElementById('config-endpoint').value = m.endpoint;
            document.getElementById('config-temp').value = m.temperature;
            document.getElementById('config-max-tokens').value = m.max_tokens;
            document.getElementById('config-log-level').value = currentConfig.logging.level;

            await updateAvailableModels(m.name);
        } catch (err) {
            console.error('Config fetch failed:', err);
        }
    }

    async function updateAvailableModels(selectedName) {
        configModelName.innerHTML = '<option value="">Yükleniyor...</option>';
        try {
            const response = await fetch('/available_models');
            const data = await response.json();

            configModelName.innerHTML = '';
            if (data.models && data.models.length > 0) {
                data.models.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.textContent = m;
                    if (m === selectedName) opt.selected = true;
                    configModelName.appendChild(opt);
                });
            } else {
                configModelName.innerHTML = '<option value="">Model bulunamadı</option>';
            }
        } catch (err) {
            console.error('Model fetch failed:', err);
            configModelName.innerHTML = '<option value="">Hata!</option>';
        }
    }

    configModelType.onchange = async () => {
        // Warning: This only shows current provider's models. 
        // If they change provider, endpoint should also be updated.
        // For now, simpler: user should update endpoint first.
    };

    saveSettingsBtn.onclick = async () => {
        if (!currentConfig) return;

        const formData = new FormData(settingsForm);

        // Update currentConfig object
        currentConfig.model.type = formData.get('type');
        currentConfig.model.name = formData.get('name');
        currentConfig.model.endpoint = document.getElementById('config-endpoint').value;
        currentConfig.model.temperature = parseFloat(document.getElementById('config-temp').value);
        currentConfig.model.max_tokens = parseInt(document.getElementById('config-max-tokens').value);
        currentConfig.logging.level = formData.get('log_level');

        try {
            const response = await fetch('/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentConfig)
            });
            const data = await response.json();
            if (data.error) alert(data.error);
            else {
                addMessage('bot', `⚙️ ${data.message}`);
                settingsModal.classList.remove('active');
            }
        } catch (err) {
            console.error('Save failed:', err);
            alert('Ayarlar kaydedilemedi.');
        }
    };
});

// --- API Error / Cache Handling Logic ---
window.openVectorModal = function (sourceName) {
    const modal = document.getElementById('vector-modal');
    const iframe = document.getElementById('vector-iframe');
    if (modal && iframe) {
        iframe.src = `/vector_explorer?source=${encodeURIComponent(sourceName)}&embed=true`;
        modal.classList.add('active');
    }
};

window.closeVectorModal = function () {
    const modal = document.getElementById('vector-modal');
    const iframe = document.getElementById('vector-iframe');
    if (modal && iframe) {
        iframe.src = '';
        modal.classList.remove('active');
    }
};
