"""
AirCasta - DropCast Web Client Template
Apple-style glassmorphism interface optimized for Mobile Safari on iOS.
Zero external CDNs or internet dependencies — works 100% locally.
"""

AIRDROP_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="DropCast">
    <title>DropCast</title>
    <style>
        :root {
            --bg-color: #090a0c;
            --card-bg: rgba(22, 24, 29, 0.75);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent: #0a84ff;
            --accent-hover: #0071e3;
            --success: #30d158;
            --text-primary: #f5f5f7;
            --text-secondary: #86868b;
            --radius-lg: 20px;
            --radius-md: 14px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, sans-serif;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-primary);
            min-height: 100vh;
            padding: env(safe-area-inset-top, 20px) 16px env(safe-area-inset-bottom, 24px) 16px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .container {
            width: 100%;
            max-width: 480px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        /* Header & Radar Pulse */
        .header {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 24px 0 12px 0;
            text-align: center;
        }

        .radar-box {
            position: relative;
            width: 72px;
            height: 72px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 12px;
        }

        .radar-ring {
            position: absolute;
            width: 100%;
            height: 100%;
            border-radius: 50%;
            border: 2px solid rgba(10, 132, 255, 0.4);
            animation: pulse 2.4s infinite cubic-bezier(0.215, 0.61, 0.355, 1);
        }

        .radar-ring:nth-child(2) {
            animation-delay: 0.8s;
        }

        .radar-icon {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #0a84ff, #0056b3);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2;
            box-shadow: 0 4px 16px rgba(10, 132, 255, 0.35);
        }

        .radar-icon svg {
            width: 24px;
            height: 24px;
            fill: #ffffff;
        }

        @keyframes pulse {
            0% { transform: scale(0.6); opacity: 0.8; }
            100% { transform: scale(1.6); opacity: 0; }
        }

        .title {
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.4px;
            color: #ffffff;
        }

        .device-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 4px 12px;
            margin-top: 6px;
            font-size: 13px;
            color: var(--text-secondary);
        }

        .dot-green {
            width: 8px;
            height: 8px;
            background-color: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 8px rgba(48, 209, 88, 0.6);
        }

        /* Glass Cards */
        .card {
            background: var(--card-bg);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid var(--card-border);
            border-radius: var(--radius-lg);
            padding: 18px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .card-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Big Apple Buttons */
        .btn-action {
            display: flex;
            align-items: center;
            gap: 14px;
            width: 100%;
            padding: 16px 18px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: var(--radius-md);
            color: #ffffff;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            text-align: left;
            transition: all 0.15s ease;
        }

        .btn-action:active {
            transform: scale(0.98);
            background: rgba(255, 255, 255, 0.1);
        }

        .btn-action.primary {
            background: linear-gradient(180deg, #0a84ff, #0071e3);
            border: none;
            box-shadow: 0 4px 14px rgba(10, 132, 255, 0.3);
        }

        .btn-action.primary:active {
            background: #0060c2;
        }

        .btn-icon {
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.15);
        }

        .btn-icon svg {
            width: 18px;
            height: 18px;
            fill: #ffffff;
        }

        .btn-info {
            display: flex;
            flex-direction: column;
            flex: 1;
        }

        .btn-sub {
            font-size: 12px;
            font-weight: 400;
            opacity: 0.8;
            margin-top: 1px;
        }

        /* Upload Progress Area */
        .progress-box {
            display: none;
            flex-direction: column;
            gap: 10px;
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--card-border);
            border-radius: var(--radius-md);
            padding: 14px;
        }

        .progress-header {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
        }

        .progress-bar-bg {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
        }

        .progress-bar-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #0a84ff, #30d158);
            border-radius: 4px;
            transition: width 0.15s ease;
        }

        .progress-stats {
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: var(--text-secondary);
        }

        /* Success Banner */
        .success-box {
            display: none;
            align-items: center;
            gap: 10px;
            background: rgba(48, 209, 88, 0.12);
            border: 1px solid rgba(48, 209, 88, 0.3);
            border-radius: var(--radius-md);
            padding: 12px 16px;
            font-size: 14px;
            color: #30d158;
            font-weight: 500;
        }

        /* Downloads List (PC -> iPhone) */
        .download-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: var(--radius-md);
            padding: 12px 14px;
            gap: 12px;
        }

        .item-icon {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            background: #1c1d22;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .item-icon svg {
            width: 20px;
            height: 20px;
            fill: #a1a1aa;
        }

        .item-details {
            display: flex;
            flex-direction: column;
            overflow: hidden;
            flex: 1;
        }

        .item-name {
            font-size: 14px;
            font-weight: 600;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .item-size {
            font-size: 12px;
            color: var(--text-secondary);
        }

        .btn-download {
            padding: 8px 14px;
            background: rgba(10, 132, 255, 0.15);
            border: 1px solid rgba(10, 132, 255, 0.3);
            border-radius: 16px;
            color: #0a84ff;
            font-size: 13px;
            font-weight: 600;
            text-decoration: none;
            display: inline-block;
            white-space: nowrap;
        }

        .btn-download:active {
            background: #0a84ff;
            color: #ffffff;
        }

        .empty-hint {
            text-align: center;
            font-size: 13px;
            color: var(--text-secondary);
            padding: 12px 0;
        }

        /* Clipboard section */
        .clip-row {
            display: flex;
            gap: 8px;
        }

        .clip-input {
            flex: 1;
            background: rgba(0, 0, 0, 0.35);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 10px 12px;
            color: #ffffff;
            font-size: 13px;
            outline: none;
        }

        .clip-input:focus {
            border-color: var(--accent);
        }

        .btn-clip {
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 10px 14px;
            color: #ffffff;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
        }

        .btn-clip:active {
            background: var(--accent);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="radar-box">
                <div class="radar-ring"></div>
                <div class="radar-ring"></div>
                <div class="radar-icon">
                    <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14.5v-9l6 4.5-6 4.5z"/></svg>
                </div>
            </div>
            <div class="title">DropCast</div>
            <div class="device-badge">
                <span class="dot-green"></span>
                <span>__PC_NAME__</span>
            </div>
        </div>

        <!-- 1. Send to PC -->
        <div class="card">
            <div class="card-title">Отправить на компьютер</div>
            
            <input type="file" id="photoInput" multiple accept="image/*,video/*" style="display: none;">
            <button class="btn-action primary" onclick="document.getElementById('photoInput').click()">
                <div class="btn-icon">
                    <svg viewBox="0 0 24 24"><path d="M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z"/></svg>
                </div>
                <div class="btn-info">
                    <span>Медиатека (Фото и Видео)</span>
                    <span class="btn-sub">Оригинальное качество без сжатия</span>
                </div>
            </button>

            <input type="file" id="fileInput" multiple accept="*/*" style="display: none;">
            <button class="btn-action" onclick="document.getElementById('fileInput').click()">
                <div class="btn-icon">
                    <svg viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
                </div>
                <div class="btn-info">
                    <span>Любые файлы</span>
                    <span class="btn-sub">Документы, архивы, музыка из Файлов</span>
                </div>
            </button>

            <!-- Progress Box -->
            <div id="progressBox" class="progress-box">
                <div class="progress-header">
                    <span id="progressTitle" style="font-weight: 600;">Отправка...</span>
                    <span id="progressPercent" style="color: var(--accent); font-weight: 700;">0%</span>
                </div>
                <div class="progress-bar-bg">
                    <div id="progressBar" class="progress-bar-fill"></div>
                </div>
                <div class="progress-stats">
                    <span id="progressFiles">0 файлов</span>
                    <span id="progressSpeed">0 MB/s</span>
                </div>
            </div>

            <!-- Success Box -->
            <div id="successBox" class="success-box">
                <svg style="width: 20px; height: 20px; fill: #30d158; flex-shrink: 0;" viewBox="0 0 24 24"><path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/></svg>
                <span id="successText">Файлы успешно отправлены на ПК</span>
            </div>
        </div>

        <!-- 2. Files from PC -->
        <div class="card">
            <div class="card-title">Получить с компьютера</div>
            <div id="downloadsList" style="display: flex; flex-direction: column; gap: 8px;">
                <div class="empty-hint">Перетащите файлы на компьютере в окно DropCast, и они сразу появятся здесь.</div>
            </div>
        </div>

        <!-- 3. Clipboard Sharing -->
        <div class="card">
            <div class="card-title">Текст и ссылки</div>
            <div class="clip-row">
                <input type="text" id="clipInput" class="clip-input" placeholder="Вставьте ссылку или текст для ПК...">
                <button class="btn-clip" onclick="sendClipboard()">Отправить</button>
            </div>
            <div id="pcClipBox" style="display: none; background: rgba(0,0,0,0.3); padding: 10px 12px; border-radius: 8px; font-size: 13px; word-break: break-all;">
                <div style="font-size: 11px; color: var(--text-secondary); margin-bottom: 4px;">СКОПИРОВАНО НА ПК:</div>
                <span id="pcClipText"></span>
            </div>
        </div>
    </div>

    <script>
        const photoInput = document.getElementById('photoInput');
        const fileInput = document.getElementById('fileInput');
        const progressBox = document.getElementById('progressBox');
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        const progressTitle = document.getElementById('progressTitle');
        const progressFiles = document.getElementById('progressFiles');
        const progressSpeed = document.getElementById('progressSpeed');
        const successBox = document.getElementById('successBox');
        const successText = document.getElementById('successText');
        const downloadsList = document.getElementById('downloadsList');

        photoInput.addEventListener('change', (e) => handleFiles(e.target.files));
        fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        }

        function handleFiles(files) {
            if (!files || files.length === 0) return;

            const formData = new FormData();
            let totalBytes = 0;
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
                totalBytes += files[i].size;
            }

            progressBox.style.display = 'flex';
            successBox.style.display = 'none';
            progressBar.style.width = '0%';
            progressPercent.textContent = '0%';
            progressFiles.textContent = files.length + (files.length === 1 ? ' файл' : ' файлов') + ' (' + formatBytes(totalBytes) + ')';
            progressTitle.textContent = 'Передача на ПК...';

            const startTime = Date.now();
            let lastLoaded = 0;
            let lastTime = startTime;

            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/upload', true);

            xhr.upload.onprogress = function(e) {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percent + '%';
                    progressPercent.textContent = percent + '%';

                    const now = Date.now();
                    const dt = (now - lastTime) / 1000;
                    if (dt > 0.4) {
                        const speedBps = (e.loaded - lastLoaded) / dt;
                        progressSpeed.textContent = (speedBps / (1024 * 1024)).toFixed(1) + ' MB/s';
                        lastLoaded = e.loaded;
                        lastTime = now;
                    }
                }
            };

            xhr.onload = function() {
                if (xhr.status === 200) {
                    progressBar.style.width = '100%';
                    progressPercent.textContent = '100%';
                    progressSpeed.textContent = '';
                    setTimeout(() => {
                        progressBox.style.display = 'none';
                        successBox.style.display = 'flex';
                        successText.textContent = 'Успешно отправлено: ' + files.length + ' ' + (files.length === 1 ? 'файл' : 'файлов');
                        if (navigator.vibrate) navigator.vibrate([40, 60, 40]);
                    }, 400);
                } else {
                    alert('Ошибка передачи: ' + xhr.statusText);
                    progressBox.style.display = 'none';
                }
                photoInput.value = '';
                fileInput.value = '';
            };

            xhr.onerror = function() {
                alert('Сетевая ошибка при передаче');
                progressBox.style.display = 'none';
            };

            xhr.send(formData);
        }

        // Fetch shared files from PC
        function loadDownloads() {
            fetch('/api/downloads')
                .then(r => r.json())
                .then(files => {
                    if (!files || files.length === 0) {
                        downloadsList.innerHTML = '<div class="empty-hint">Перетащите файлы на компьютере в окно DropCast, и они появятся здесь.</div>';
                        return;
                    }
                    let html = '';
                    files.forEach(f => {
                        html += `
                            <div class="download-item">
                                <div class="item-icon">
                                    <svg viewBox="0 0 24 24"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
                                </div>
                                <div class="item-details">
                                    <span class="item-name">${f.name}</span>
                                    <span class="item-size">${formatBytes(f.size)}</span>
                                </div>
                                <a href="/api/download/${encodeURIComponent(f.id)}" download="${f.name}" class="btn-download">Скачать</a>
                            </div>
                        `;
                    });
                    downloadsList.innerHTML = html;
                })
                .catch(() => {});
        }

        // Send clipboard text to PC
        function sendClipboard() {
            const input = document.getElementById('clipInput');
            const text = input.value.trim();
            if (!text) return;

            fetch('/api/clipboard', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            }).then(() => {
                input.value = '';
                alert('Скопировано в буфер обмена ПК!');
            });
        }

        // Poll for downloads & clipboard updates
        setInterval(loadDownloads, 3000);
        loadDownloads();
    </script>
</body>
</html>
"""
