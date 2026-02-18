document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const appStatus = document.getElementById('app-status');

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
        appStatus.textContent = 'Yükleniyor...';
        appStatus.style.background = '#d97706';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();

            if (data.error) {
                alert(data.error);
                appStatus.textContent = 'Hata';
                appStatus.style.background = '#dc2626';
            } else {
                addFileToSidebar(file.name);
                appStatus.textContent = 'İndekslendi';
                appStatus.style.background = '#059669';
                addMessage('bot', `📍 ${data.message}`);
            }
        } catch (err) {
            console.error(err);
            appStatus.textContent = 'Bağlantı Hatası';
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
