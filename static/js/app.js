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

    let selectedSource = null;

    // Initial load
    updateStats();

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

        addMessage('user', query);

        const loadingMsg = addMessage('bot', 'Düşünüyorum...', true);

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            const data = await response.json();

            removeMessage(loadingMsg);

            if (data.error) {
                addMessage('bot', `❌ Hata: ${data.error}`);
            } else {
                addMessage('bot', data.answer, false, data.sources);
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
            div.className = `source-item ${selectedSource === source ? 'selected' : ''}`;
            div.innerHTML = `
                <span title="${source}">${source.length > 20 ? source.substring(0, 17) + '...' : source}</span>
                <button class="delete-source-btn" data-source="${source}" title="Bu kaynağı sil">🗑️</button>
            `;

            div.onclick = (e) => {
                if (e.target.classList.contains('delete-source-btn')) return;

                if (selectedSource === source) {
                    selectedSource = null;
                    div.classList.remove('selected');
                } else {
                    document.querySelectorAll('.source-item').forEach(i => i.classList.remove('selected'));
                    selectedSource = source;
                    div.classList.add('selected');
                }
            };

            dbSources.appendChild(div);
        });

        // Add delete listeners
        document.querySelectorAll('.delete-source-btn').forEach(btn => {
            btn.onclick = async (e) => {
                const source = e.target.getAttribute('data-source');
                if (confirm(`'${source}' kaynağını ve ilgili tüm paragrafları silmek istediğinize emin misiniz?`)) {
                    await deleteSource(source);
                }
            };
        });
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

    function addMessage(role, text, isLoading = false, sources = []) {
        const div = document.createElement('div');
        div.className = `message ${role}-message`;

        let html = `<div class="message-content">${text.replace(/\n/g, '<br>')}</div>`;

        if (sources && sources.length > 0) {
            html += `<div class="sources">Kaynaklar: ${sources.join(', ')}</div>`;
        }

        div.innerHTML = html;
        chatWindow.appendChild(div);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        return div;
    }

    function removeMessage(el) {
        el.remove();
    }
});
