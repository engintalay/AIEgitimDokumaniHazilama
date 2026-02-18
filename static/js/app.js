document.addEventListener('DOMContentLoaded', () => {
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
    const closeSettings = document.getElementById('close-settings');
    const settingsForm = document.getElementById('settings-form');
    const saveSettingsBtn = document.getElementById('save-settings');

    let selectedSource = null;
    let currentConfig = null;
    let currentChatId = null;

    // Initial load
    updateStats();
    fetchHistory();

    newChatBtn.onclick = startNewChat;

    function startNewChat() {
        currentChatId = null;
        chatWindow.innerHTML = `
            <div class="message bot-message">
                <div class="message-content">
                    Merhaba! Ben doküman asistanınız. Yeni bir sohbet başlattınız. Sorunuzu bekliyorum.
                </div>
            </div>
        `;
        document.querySelectorAll('.history-item').forEach(i => i.classList.remove('active'));
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
                addMessage(msg.role, msg.content, false, msg.sources);
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

    async function handleUpload(file) {
        const jobId = 'job_' + Math.random().toString(36).substr(2, 9);

        appStatus.textContent = 'İşleniyor...';
        appStatus.classList.add('processing');
        dropZone.style.pointerEvents = 'none';
        dropZone.style.opacity = '0.5';

        // Show progress UI
        globalProgressContainer.style.display = 'flex';
        globalProgressBar.style.width = '0%';
        globalProgressText.textContent = '0%';

        const evtSource = new EventSource(`/progress/${jobId}`);
        evtSource.onmessage = (e) => {
            const p = e.data;
            globalProgressBar.style.width = p + '%';
            globalProgressText.textContent = p + '%';
            if (parseInt(p) >= 100) evtSource.close();
        };

        const processingMsg = addMessage('bot', `⌛ <b>${file.name}</b> işleniyor, lütfen bekleyin...<br><span class="spinner"></span> Paragraflara ayrılıyor ve vektörleştiriliyor...`, true);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('job_id', jobId);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

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

            // Hide progress after a short delay
            setTimeout(() => {
                globalProgressContainer.style.display = 'none';
                evtSource.close();
            }, 1000);
        }
    }

    function addFileToSidebar(name) {
        const item = document.createElement('div');
        item.className = 'file-item';
        item.innerHTML = `<span>${name}</span> <small>✅</small>`;
        fileList.appendChild(item);
    }

    // Handle Chat
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

        addMessage('user', query + (selectedSource ? ` (Dosya: ${selectedSource})` : ''));

        const loadingMsg = addMessage('bot', 'Düşünüyorum...', true);

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, source: selectedSource, chat_id: currentChatId })
            });

            const data = await response.json();

            removeMessage(loadingMsg);

            if (data.error) {
                addMessage('bot', `❌ Hata: ${data.error}`);
            } else {
                addMessage('bot', data.answer, false, data.sources);
                if (!currentChatId && data.chat_id) {
                    currentChatId = data.chat_id;
                    fetchHistory();
                }
            }
        } catch (err) {
            removeMessage(loadingMsg);
            addMessage('bot', '❌ Sunucuya erişilemedi.');
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
            div.className = `source-item ${selectedSource === source.name ? 'selected' : ''}`;

            const privacyIcon = source.is_public ? '🌐' : '🔒';
            const privacyTitle = source.is_public ? 'Herkes görebilir' : 'Sadece siz';

            let actionHtml = '';
            if (source.is_owner) {
                actionHtml = `
                    <button class="toggle-public-btn" data-source="${source.name}" data-public="${source.is_public}" title="${source.is_public ? 'Özel yap' : 'Paylaş'}">
                        ${privacyIcon}
                    </button>
                    <button class="delete-source-btn" data-source="${source.name}" title="Bu kaynağı sil">🗑️</button>
                `;
            } else {
                actionHtml = `<span class="shared-badge" title="Paylaşılan doküman">${privacyIcon}</span>`;
            }

            div.innerHTML = `
                <span title="${source.name}">${source.name.length > 20 ? source.name.substring(0, 17) + '...' : source.name}</span>
                <div class="source-actions">
                    ${actionHtml}
                </div>
            `;

            div.onclick = (e) => {
                if (e.target.closest('button')) return;

                if (selectedSource === source.name) {
                    selectedSource = null;
                    div.classList.remove('selected');
                } else {
                    document.querySelectorAll('.source-item').forEach(i => i.classList.remove('selected'));
                    selectedSource = source.name;
                    div.classList.add('selected');
                }
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
                if (selectedSource === source) selectedSource = null;
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

    function addMessage(role, text, isLoading = false, sources = []) {
        const div = document.createElement('div');
        div.className = `message ${role}-message`;

        let actionHtml = '';
        if (role === 'user' && !isLoading) {
            actionHtml = `
                <div class="message-actions">
                    <button class="action-btn copy-btn" title="Kopyala">📋</button>
                    <button class="action-btn rerun-btn" title="Tekrar Çalıştır">🔄</button>
                </div>
            `;
        }

        let html = `<div class="message-content">${text.replace(/\n/g, '<br>')}</div>${actionHtml}`;

        if (sources && sources.length > 0) {
            html += `<div class="sources">Kaynaklar: ${sources.join(', ')}</div>`;
        }

        div.innerHTML = html;
        chatWindow.appendChild(div);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        // Add action listeners
        if (role === 'user' && !isLoading) {
            const cleanText = text.includes(' (Dosya:') ? text.split(' (Dosya:')[0] : text;
            div.querySelector('.copy-btn').onclick = () => {
                userInput.value = cleanText;
                userInput.focus();
                userInput.dispatchEvent(new Event('input')); // Trigger auto-resize
            };
            div.querySelector('.rerun-btn').onclick = () => {
                userInput.value = cleanText;
                sendMessage();
            };
        }

        return div;
    }

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
