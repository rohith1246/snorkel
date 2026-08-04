document.addEventListener('DOMContentLoaded', () => {
    // --- MODE NAVIGATION ---
    const modeAuditorBtn = document.getElementById('modeAuditorBtn');
    const modeTemplateBtn = document.getElementById('modeTemplateBtn');
    const modeIdeasBtn = document.getElementById('modeIdeasBtn');
    const sectionAuditor = document.getElementById('sectionAuditor');
    const sectionTemplate = document.getElementById('sectionTemplate');
    const sectionIdeas = document.getElementById('sectionIdeas');

    modeAuditorBtn.addEventListener('click', () => {
        modeAuditorBtn.classList.add('active');
        if (modeTemplateBtn) modeTemplateBtn.classList.remove('active');
        modeIdeasBtn.classList.remove('active');
        sectionAuditor.style.display = 'grid';
        if (sectionTemplate) sectionTemplate.style.display = 'none';
        sectionIdeas.style.display = 'none';
    });

    if (modeTemplateBtn) {
        modeTemplateBtn.addEventListener('click', () => {
            modeTemplateBtn.classList.add('active');
            modeAuditorBtn.classList.remove('active');
            modeIdeasBtn.classList.remove('active');
            sectionAuditor.style.display = 'none';
            if (sectionTemplate) sectionTemplate.style.display = 'block';
            sectionIdeas.style.display = 'none';
            loadTerminus3Structure();
        });
    }

    modeIdeasBtn.addEventListener('click', () => {
        modeIdeasBtn.classList.add('active');
        modeAuditorBtn.classList.remove('active');
        if (modeTemplateBtn) modeTemplateBtn.classList.remove('active');
        sectionAuditor.style.display = 'none';
        if (sectionTemplate) sectionTemplate.style.display = 'none';
        sectionIdeas.style.display = 'block';
        loadTaskIdeas(1);
    });

    // --- TASK AUDITOR LOGIC ---
    const uploadZone = document.getElementById('uploadZone');
    const zipFileInput = document.getElementById('zipFileInput');
    const selectedFileInfo = document.getElementById('selectedFileInfo');
    const fileNameSpan = document.getElementById('fileName');
    const fileSizeSpan = document.getElementById('fileSize');
    const runAuditBtn = document.getElementById('runAuditBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const scoreCard = document.getElementById('scoreCard');
    const resultsCard = document.getElementById('resultsCard');
    const groqApiKeyInput = document.getElementById('groqApiKey');
    const toggleKeyVisibility = document.getElementById('toggleKeyVisibility');

    let currentFile = null;

    toggleKeyVisibility.addEventListener('click', () => {
        const type = groqApiKeyInput.type === 'password' ? 'text' : 'password';
        groqApiKeyInput.type = type;
        toggleKeyVisibility.innerHTML = type === 'password' ? '<i class="fa-solid fa-eye"></i>' : '<i class="fa-solid fa-eye-slash"></i>';
    });

    uploadZone.addEventListener('click', (e) => {
        if (e.target !== zipFileInput) {
            zipFileInput.click();
        }
    });

    zipFileInput.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    zipFileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFileSelect(e.target.files[0]);
    });

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (!file.name.toLowerCase().endsWith('.zip')) {
            alert('Please select a valid .zip archive.');
            return;
        }
        currentFile = file;
        fileNameSpan.textContent = file.name;
        fileSizeSpan.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
        selectedFileInfo.style.display = 'inline-flex';
        runAuditBtn.disabled = false;
    }

    runAuditBtn.addEventListener('click', async () => {
        if (!currentFile) return;

        const formData = new FormData();
        formData.append('task_zip', currentFile);
        formData.append('groq_api_key', groqApiKeyInput.value.trim());

        loadingOverlay.style.display = 'flex';

        try {
            const resp = await fetch('/api/audit', { method: 'POST', body: formData });
            const result = await resp.json();
            loadingOverlay.style.display = 'none';

            if (result.status === 'SUCCESS') {
                renderAuditResults(result.data);
            } else {
                alert('Audit Error: ' + result.message);
            }
        } catch (err) {
            loadingOverlay.style.display = 'none';
            alert('Failed to connect to auditor server: ' + err.message);
        }
    });

    function renderAuditResults(data) {
        scoreCard.style.display = 'block';
        resultsCard.style.display = 'block';

        document.getElementById('taskNameBadge').textContent = 'Task: ' + data.task_name;
        document.getElementById('scoreValue').textContent = data.score;
        document.getElementById('passCount').textContent = data.passed_checks;
        document.getElementById('failCount').textContent = data.failed_checks;
        document.getElementById('warnCount').textContent = data.warning_checks;
        document.getElementById('summaryText').textContent = data.summary;

        const circle = document.getElementById('scoreCircle');
        if (data.score >= 90) circle.style.borderColor = 'var(--pass-green)';
        else if (data.score >= 70) circle.style.borderColor = 'var(--warn-yellow)';
        else circle.style.borderColor = 'var(--fail-red)';

        // Render Findings List
        const findingsList = document.getElementById('findingsList');
        findingsList.innerHTML = '';

        data.checks.forEach(check => {
            const item = document.createElement('div');
            item.className = `finding-item status-${check.status}`;
            item.dataset.status = check.status;
            item.innerHTML = `
                <div class="finding-header">
                    <span class="finding-title">${check.name}</span>
                    <span class="badge badge-${check.status === 'PASS' ? 'success' : (check.status === 'FAIL' ? 'danger' : 'neutral')}">${check.status}</span>
                </div>
                <div class="finding-msg">${check.message}</div>
                ${check.suggestion ? `<div class="finding-fix"><i class="fa-solid fa-wrench"></i> ${check.suggestion}</div>` : ''}
            `;
            findingsList.appendChild(item);
        });

        // Render AI Analysis Content
        const aiContent = document.getElementById('aiAnalysisContent');
        const aiTag = document.getElementById('aiSourceTag');
        if (data.ai_analysis) {
            aiTag.textContent = 'Source: ' + data.ai_analysis.source;
            aiContent.textContent = data.ai_analysis.analysis;
        }

        // Render File Tree
        const fileTree = document.getElementById('fileTreeContainer');
        fileTree.innerHTML = data.file_tree.map(f => `<div class="tree-file"><i class="fa-solid fa-file-code icon-blue"></i> ${f}</div>`).join('');
    }

    // Tabs inside Auditor
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });

    // Findings Filters
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const filter = btn.dataset.filter;
            document.querySelectorAll('.finding-item').forEach(item => {
                if (filter === 'all' || item.dataset.status === filter) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });

    // --- 100 TASK IDEAS CATALOGUE LOGIC (WITH CLAIM SYSTEM) ---
    let currentPage = 1;
    let currentCategory = 'all';
    let currentSearch = '';
    let showClaimed = false; // Default: Hides claimed tasks!

    const ideasListContainer = document.getElementById('ideasListContainer');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageNumBadge = document.getElementById('pageNumBadge');
    const paginationInfo = document.getElementById('paginationInfo');
    const taskSearchInput = document.getElementById('taskSearchInput');
    const toggleShowClaimedBtn = document.getElementById('toggleShowClaimedBtn');

    // Claim Modal Elements
    const claimModal = document.getElementById('claimModal');
    const closeClaimBtn = document.getElementById('closeClaimBtn');
    const cancelClaimBtn = document.getElementById('cancelClaimBtn');
    const confirmClaimBtn = document.getElementById('confirmClaimBtn');
    const claimTaskNameCode = document.getElementById('claimTaskNameCode');
    const claimantNameInput = document.getElementById('claimantNameInput');
    let taskToClaim = null;

    toggleShowClaimedBtn.addEventListener('click', () => {
        showClaimed = !showClaimed;
        if (showClaimed) {
            toggleShowClaimedBtn.innerHTML = '<i class="fa-solid fa-eye"></i> Showing All (Including Claimed)';
            toggleShowClaimedBtn.classList.remove('btn-outline');
            toggleShowClaimedBtn.classList.add('btn-primary');
        } else {
            toggleShowClaimedBtn.innerHTML = '<i class="fa-solid fa-eye-slash"></i> Hide Claimed (Active Only)';
            toggleShowClaimedBtn.classList.remove('btn-primary');
            toggleShowClaimedBtn.classList.add('btn-outline');
        }
        loadTaskIdeas(1);
    });

    async function loadTaskIdeas(page = 1) {
        currentPage = page;
        ideasListContainer.innerHTML = '<p class="placeholder-text">Loading task ideas for page ' + page + '...</p>';

        try {
            const url = `/api/task-ideas?page=${page}&per_page=5&category=${encodeURIComponent(currentCategory)}&search=${encodeURIComponent(currentSearch)}&show_claimed=${showClaimed}`;
            const resp = await fetch(url);
            const data = await resp.json();

            if (data.status === 'SUCCESS') {
                renderTaskIdeas(data);
            }
        } catch (err) {
            ideasListContainer.innerHTML = '<p class="placeholder-text">Failed to load task ideas.</p>';
        }
    }

    function renderTaskIdeas(data) {
        ideasListContainer.innerHTML = '';

        if (data.tasks.length === 0) {
            ideasListContainer.innerHTML = '<p class="placeholder-text">No available task ideas found matching criteria.</p>';
            paginationInfo.innerHTML = 'Showing Tasks <strong>0</strong> of <strong>0</strong>';
            pageNumBadge.textContent = 'Page 0 of 0';
            prevPageBtn.disabled = true;
            nextPageBtn.disabled = true;
            return;
        }

        data.tasks.forEach(task => {
            const card = document.createElement('div');
            card.className = `card white-card task-idea-card ${task.is_claimed ? 'claimed' : ''}`;
            card.innerHTML = `
                <div class="task-idea-header">
                    <div class="task-idea-title">
                        <code>${task.name}</code>
                    </div>
                    <div class="task-idea-meta">
                        <span class="badge badge-primary">${task.category}</span>
                        <span class="badge badge-neutral">Difficulty: ${task.difficulty}</span>
                        ${task.is_claimed ? `<span class="badge badge-danger"><i class="fa-solid fa-user-lock"></i> Claimed by ${task.claimed_by}</span>` : ''}
                    </div>
                </div>
                <div class="task-idea-body">
                    <div class="problem-statement-text">${task.problem_statement}</div>
                    <div class="mechanism-box">
                        <div class="mechanism-title"><i class="fa-solid fa-shield-cat"></i> Hardening Mechanism</div>
                        <div class="mechanism-desc">${task.hardening_mechanism}</div>
                    </div>
                </div>
                <div class="task-idea-footer">
                    <div>
                        <i class="fa-solid fa-file-code icon-blue"></i> Output: <code>${task.output_artifact}</code>
                    </div>
                    <div class="score-targets">
                        <span class="target-badge target-oracle">Oracle: ${task.oracle_score}</span>
                        <span class="target-badge target-llm">LLM: ${task.llm_score}</span>
                        ${task.is_claimed ? 
                            `<button class="btn-unclaim" data-name="${task.name}"><i class="fa-solid fa-undo"></i> Unclaim</button>` : 
                            `<button class="btn-claim" data-name="${task.name}"><i class="fa-solid fa-hand-pointer"></i> Claim Task</button>`
                        }
                    </div>
                </div>
            `;
            ideasListContainer.appendChild(card);
        });

        // Add Claim button click handlers
        document.querySelectorAll('.btn-claim').forEach(b => {
            b.addEventListener('click', (e) => {
                taskToClaim = e.target.closest('button').dataset.name;
                claimTaskNameCode.textContent = taskToClaim;
                claimantNameInput.value = '';
                claimModal.classList.add('active');
            });
        });

        // Add Unclaim button click handlers
        document.querySelectorAll('.btn-unclaim').forEach(b => {
            b.addEventListener('click', async (e) => {
                const tName = e.target.closest('button').dataset.name;
                if (confirm(`Unclaim task '${tName}' and restore it to available tasks?`)) {
                    await fetch('/api/unclaim-task', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ task_name: tName })
                    });
                    loadTaskIdeas(currentPage);
                }
            });
        });

        const startItem = (data.current_page - 1) * data.per_page + 1;
        const endItem = Math.min(data.current_page * data.per_page, data.total_tasks);
        paginationInfo.innerHTML = `Showing Active Tasks <strong>${startItem} - ${endItem}</strong> of <strong>${data.total_tasks}</strong> (5 per page)`;
        pageNumBadge.textContent = `Page ${data.current_page} of ${data.total_pages}`;

        prevPageBtn.disabled = data.current_page <= 1;
        nextPageBtn.disabled = data.current_page >= data.total_pages;
    }

    closeClaimBtn.addEventListener('click', () => claimModal.classList.remove('active'));
    cancelClaimBtn.addEventListener('click', () => claimModal.classList.remove('active'));

    confirmClaimBtn.addEventListener('click', async () => {
        if (!taskToClaim) return;
        const friendName = claimantNameInput.value.trim() || 'Friend';

        try {
            const resp = await fetch('/api/claim-task', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ task_name: taskToClaim, claimed_by: friendName })
            });
            const result = await resp.json();
            claimModal.classList.remove('active');

            if (result.status === 'SUCCESS') {
                alert(result.message);
                loadTaskIdeas(currentPage);
            } else {
                alert('Error: ' + result.message);
            }
        } catch (err) {
            alert('Failed to claim task: ' + err.message);
        }
    });

    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) loadTaskIdeas(currentPage - 1);
    });

    nextPageBtn.addEventListener('click', () => {
        loadTaskIdeas(currentPage + 1);
    });

    // Category Filter Buttons
    document.querySelectorAll('.cat-filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.cat-filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentCategory = btn.dataset.cat;
            loadTaskIdeas(1);
        });
    });

    // Terminus 3 Tree Structure Explorer Logic
    async function loadTerminus3Structure() {
        const treeNav = document.getElementById('t3TreeNav');
        if (!treeNav) return;
        
        try {
            const resp = await fetch('/api/terminus3-structure');
            const data = await resp.json();
            if (data.status === 'SUCCESS') {
                renderT3Tree(data.structure);
            }
        } catch (e) {
            console.error('Failed to load Terminus 3 structure:', e);
        }
    }

    function renderT3Tree(items) {
        const treeNav = document.getElementById('t3TreeNav');
        const detailContent = document.getElementById('t3DetailContent');
        if (!treeNav) return;
        treeNav.innerHTML = '';
        
        items.forEach((item, idx) => {
            const row = document.createElement('div');
            row.style.padding = '8px 10px';
            row.style.margin = '4px 0';
            row.style.borderRadius = '6px';
            row.style.cursor = 'pointer';
            row.style.transition = 'all 0.2s ease';
            row.style.border = '1px solid transparent';
            
            const icon = item.type === 'folder' ? '<i class="fa-solid fa-folder icon-blue" style="margin-right:8px;"></i>' : '<i class="fa-regular fa-file-code" style="margin-right:8px; color:#0E7490;"></i>';
            row.innerHTML = `${icon} <strong>${item.path}</strong>`;
            
            row.addEventListener('mouseenter', () => {
                row.style.background = '#F1F5F9';
                row.style.borderColor = '#CBD5E1';
            });
            row.addEventListener('mouseleave', () => {
                row.style.background = 'transparent';
                row.style.borderColor = 'transparent';
            });
            
            row.addEventListener('click', () => {
                detailContent.innerHTML = `
                    <h3 style="font-size: 16px; font-weight: 700; color: #0E7490;">
                        ${icon} ${item.path}
                    </h3>
                    <p style="margin-top: 10px; font-size: 14px; color: #334155; line-height: 1.6;">
                        ${item.description}
                    </p>
                    <div style="margin-top: 15px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; font-size: 13px;">
                        <strong>Requirement Check:</strong> Must adhere to official Terminus 3 platform rules.
                    </div>
                `;
            });
            
            treeNav.appendChild(row);
        });
    }
});
