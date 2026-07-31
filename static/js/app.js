document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const uploadZone = document.getElementById('uploadZone');
    const zipFileInput = document.getElementById('zipFileInput');
    const selectedFileInfo = document.getElementById('selectedFileInfo');
    const fileNameDisplay = document.getElementById('fileName');
    const fileSizeDisplay = document.getElementById('fileSize');
    const runAuditBtn = document.getElementById('runAuditBtn');
    
    const groqApiKeyInput = document.getElementById('groqApiKey');
    const toggleKeyVisibilityBtn = document.getElementById('toggleKeyVisibility');

    const scoreCard = document.getElementById('scoreCard');
    const resultsCard = document.getElementById('resultsCard');
    const scoreCircle = document.getElementById('scoreCircle');
    const scoreValue = document.getElementById('scoreValue');
    const passCount = document.getElementById('passCount');
    const failCount = document.getElementById('failCount');
    const warnCount = document.getElementById('warnCount');
    const taskNameBadge = document.getElementById('taskNameBadge');
    const summaryText = document.getElementById('summaryText');

    const findingsList = document.getElementById('findingsList');
    const aiAnalysisContent = document.getElementById('aiAnalysisContent');
    const aiSourceTag = document.getElementById('aiSourceTag');
    const fileTreeContainer = document.getElementById('fileTreeContainer');
    
    const loadingOverlay = document.getElementById('loadingOverlay');
    const openHistoryBtn = document.getElementById('openHistoryBtn');
    const historyModal = document.getElementById('historyModal');
    const closeHistoryBtn = document.getElementById('closeHistoryBtn');
    const historyList = document.getElementById('historyList');

    let currentFile = null;
    let currentAuditData = null;

    // Toggle Password Visibility for Groq Key
    toggleKeyVisibilityBtn.addEventListener('click', () => {
        const type = groqApiKeyInput.getAttribute('type') === 'password' ? 'text' : 'password';
        groqApiKeyInput.setAttribute('type', type);
        toggleKeyVisibilityBtn.innerHTML = type === 'password' ? '<i class="fa-solid fa-eye"></i>' : '<i class="fa-solid fa-eye-slash"></i>';
    });

    // Upload Zone Click & Drag-Drop
    uploadZone.addEventListener('click', () => zipFileInput.click());

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('dragover'));

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    zipFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (!file.name.endsWith('.zip')) {
            alert('Please select a valid .zip task archive file.');
            return;
        }
        currentFile = file;
        fileNameDisplay.textContent = file.name;
        fileSizeDisplay.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
        selectedFileInfo.style.display = 'inline-flex';
        runAuditBtn.disabled = false;
    }

    // Run Audit Event
    runAuditBtn.addEventListener('click', async () => {
        if (!currentFile) return;

        const formData = new FormData();
        formData.append('task_zip', currentFile);
        formData.append('groq_api_key', groqApiKeyInput.value.trim());

        loadingOverlay.style.display = 'flex';

        try {
            const resp = await fetch('/api/audit', {
                method: 'POST',
                body: formData
            });

            const res = await resp.json();
            loadingOverlay.style.display = 'none';

            if (res.status === 'SUCCESS') {
                currentAuditData = res.data;
                renderAuditResults(res.data);
            } else {
                alert('Audit Error: ' + res.message);
            }
        } catch (err) {
            loadingOverlay.style.display = 'none';
            alert('Network Error during audit execution: ' + err.message);
        }
    });

    // Render Results
    function renderAuditResults(data) {
        scoreCard.style.display = 'block';
        resultsCard.style.display = 'block';

        // Animate Score
        animateScore(data.score);
        taskNameBadge.textContent = 'Task: ' + data.task_name;

        passCount.textContent = data.passed_checks;
        failCount.textContent = data.failed_checks;
        warnCount.textContent = data.warning_checks;

        summaryText.textContent = data.summary;

        // Render Findings
        renderFindings(data.checks, 'all');

        // Render AI Analysis
        if (data.ai_analysis) {
            aiSourceTag.textContent = 'Source: ' + data.ai_analysis.source;
            aiAnalysisContent.innerHTML = formatMarkdown(data.ai_analysis.analysis);
        }

        // Render File Tree
        renderFileTree(data.file_tree);
    }

    function animateScore(targetScore) {
        let current = 0;
        const duration = 1000;
        const stepTime = 20;
        const steps = duration / stepTime;
        const increment = targetScore / steps;

        const timer = setInterval(() => {
            current += increment;
            if (current >= targetScore) {
                current = targetScore;
                clearInterval(timer);
            }
            scoreValue.textContent = Math.round(current);
        }, stepTime);

        // Color coding
        if (targetScore >= 90) {
            scoreCircle.style.borderColor = 'var(--pass-green)';
            scoreCircle.style.boxShadow = '0 0 25px rgba(16, 185, 129, 0.4)';
        } else if (targetScore >= 70) {
            scoreCircle.style.borderColor = 'var(--warn-yellow)';
            scoreCircle.style.boxShadow = '0 0 25px rgba(245, 158, 11, 0.4)';
        } else {
            scoreCircle.style.borderColor = 'var(--fail-red)';
            scoreCircle.style.boxShadow = '0 0 25px rgba(239, 68, 68, 0.4)';
        }
    }

    function renderFindings(checks, filter) {
        findingsList.innerHTML = '';
        const filtered = checks.filter(c => filter === 'all' || c.status === filter);

        if (filtered.length === 0) {
            findingsList.innerHTML = '<p class="placeholder-text">No findings match the selected filter.</p>';
            return;
        }

        filtered.forEach(c => {
            const item = document.createElement('div');
            item.className = `finding-item status-${c.status}`;

            const badgeClass = c.status === 'PASS' ? 'badge-info' : (c.status === 'FAIL' ? 'badge-fail' : 'badge-warn');
            const icon = c.status === 'PASS' ? '<i class="fa-solid fa-circle-check" style="color:var(--pass-green)"></i>' : (c.status === 'FAIL' ? '<i class="fa-solid fa-circle-xmark" style="color:var(--fail-red)"></i>' : '<i class="fa-solid fa-triangle-exclamation" style="color:var(--warn-yellow)"></i>');

            item.innerHTML = `
                <div class="finding-header">
                    <span class="finding-title">${icon} [${c.category}] ${c.name}</span>
                    <span class="badge ${badgeClass}">${c.status}</span>
                </div>
                <div class="finding-msg">${c.message}</div>
                ${c.details ? `<div style="font-size:0.85rem;color:var(--text-muted);margin-bottom:6px;">${c.details}</div>` : ''}
                ${c.suggestion ? `<div class="finding-fix"><i class="fa-solid fa-lightbulb"></i> Fix: ${c.suggestion}</div>` : ''}
            `;
            findingsList.appendChild(item);
        });
    }

    // Filter Findings
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            if (currentAuditData) {
                renderFindings(currentAuditData.checks, btn.dataset.filter);
            }
        });
    });

    // Tab Switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });

    function renderFileTree(files) {
        fileTreeContainer.innerHTML = '';
        if (!files || files.length === 0) {
            fileTreeContainer.innerHTML = '<p class="placeholder-text">No files found.</p>';
            return;
        }
        files.forEach(f => {
            const div = document.createElement('div');
            div.className = 'tree-file';
            div.innerHTML = `<i class="fa-regular fa-file-code"></i> ${f}`;
            fileTreeContainer.appendChild(div);
        });
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let html = text
            .replace(/### (.*)/g, '<h3 style="font-size:1.1rem;margin:12px 0 6px;color:var(--primary-glow);">$1</h3>')
            .replace(/#### (.*)/g, '<h4 style="font-size:1rem;margin:10px 0 4px;">$1</h4>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/`(.*?)`/g, '<code style="background:rgba(0,0,0,0.5);padding:2px 6px;border-radius:4px;font-family:var(--font-mono);">$1</code>');
        return html;
    }

    // Audit History Modal
    openHistoryBtn.addEventListener('click', async () => {
        historyModal.classList.add('active');
        try {
            const resp = await fetch('/api/history');
            const data = await resp.json();
            if (data.status === 'SUCCESS') {
                renderHistory(data.history);
            }
        } catch (e) {
            historyList.innerHTML = '<p class="placeholder-text">Failed to load history.</p>';
        }
    });

    closeHistoryBtn.addEventListener('click', () => {
        historyModal.classList.remove('active');
    });

    function renderHistory(logs) {
        historyList.innerHTML = '';
        if (!logs || logs.length === 0) {
            historyList.innerHTML = '<p class="placeholder-text">No previous audit logs.</p>';
            return;
        }

        logs.forEach(log => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.style.cssText = 'padding:12px;border-bottom:1px solid var(--border-color);display:flex;justify-content:space-between;align-items:center;';
            div.innerHTML = `
                <div>
                    <strong>${log.task_name}</strong>
                    <div style="font-size:0.8rem;color:var(--text-muted);">${log.created_at}</div>
                </div>
                <div style="text-align:right;">
                    <span class="badge ${log.score >= 80 ? 'badge-info' : 'badge-fail'}">Score: ${log.score}/100</span>
                </div>
            `;
            historyList.appendChild(div);
        });
    }
});
