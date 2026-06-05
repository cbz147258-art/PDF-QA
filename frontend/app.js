// ========== Configuration ==========
const API_BASE = '/api';

// ========== State ==========
let currentDocId = null;
let currentCollection = null;

// ========== DOM Elements ==========
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const uploadZone = $('#uploadZone');
const fileInput = $('#fileInput');
const uploadStatus = $('#uploadStatus');
const progressBar = $('#progressBar');
const progressFill = $('#progressFill');
const docList = $('#docList');
const docSelect = $('#docSelect');
const chatMessages = $('#chatMessages');
const questionInput = $('#questionInput');
const sendBtn = $('#sendBtn');
const refreshDocsBtn = $('#refreshDocs');
const historyToggle = $('#historyToggle');
const historyDrawer = $('#historyDrawer');
const drawerOverlay = $('#drawerOverlay');
const closeDrawer = $('#closeDrawer');
const historyContent = $('#historyContent');

// ========== Toast ==========
function showToast(msg, type = 'success') {
    const container = $('.toast-container') || (() => {
        const div = document.createElement('div');
        div.className = 'toast-container';
        document.body.appendChild(div);
        return div;
    })();
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ========== Document List ==========
async function loadDocuments() {
    try {
        const res = await fetch(`${API_BASE}/documents`);
        const docs = await res.json();
        renderDocList(docs);
        renderDocSelect(docs);
    } catch (err) {
        console.error('加载文档列表失败', err);
    }
}

function renderDocList(docs) {
    if (docs.length === 0) {
        docList.innerHTML = `<div class="empty-state"><span class="empty-icon">&#x1F4AD;</span><p>暂无文档，上传一个 PDF 开始吧</p></div>`;
        return;
    }
    docList.innerHTML = docs.map(d => `
        <div class="doc-item ${d.id === currentDocId ? 'active' : ''}" data-id="${d.id}">
            <span class="doc-item-icon">&#x1F4C4;</span>
            <div class="doc-item-info">
                <div class="doc-item-name" title="${escapeHtml(d.filename)}">${escapeHtml(d.filename)}</div>
                <div class="doc-item-meta">${d.total_chars} 字 · ${d.chunk_count} 块</div>
            </div>
            <span class="doc-item-badge">${d.chunk_count}块</span>
        </div>
    `).join('');

    // Click handler
    docList.querySelectorAll('.doc-item').forEach(item => {
        item.addEventListener('click', () => selectDocument(
            parseInt(item.dataset.id),
            docs.find(d => d.id === parseInt(item.dataset.id))
        ));
    });
}

function renderDocSelect(docs) {
    docSelect.innerHTML = '<option value="">-- 请选择文档 --</option>' +
        docs.map(d => `<option value="${d.id}">${escapeHtml(d.filename)} (${d.chunk_count}块)</option>`).join('');
}

function selectDocument(id, doc) {
    currentDocId = id;
    // Update doc list active state
    docList.querySelectorAll('.doc-item').forEach(el => el.classList.remove('active'));
    const target = docList.querySelector(`[data-id="${id}"]`);
    if (target) target.classList.add('active');
    // Update select
    docSelect.value = id;
    // Clear chat
    chatMessages.innerHTML = `
        <div class="welcome-msg">
            <div class="welcome-icon">&#x1F4D6;</div>
            <h3>已选择：${escapeHtml(doc?.filename || '文档')}</h3>
            <p>开始提问吧</p>
            <div class="suggestions">
                <span class="suggestion-chip">这篇文章讲了什么？</span>
                <span class="suggestion-chip">总结文档要点</span>
                <span class="suggestion-chip">列出关键数据和结论</span>
            </div>
        </div>
    `;
    bindSuggestionChips();
    showToast(`已选择文档：${doc?.filename}`, 'success');
}

// ========== Upload ==========
uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
});
uploadZone.addEventListener('dragleave', () => uploadZone.classList.remove('drag-over'));
uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
});

fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (file) handleUpload(file);
    fileInput.value = '';
});

async function handleUpload(file) {
    if (file.type !== 'application/pdf') {
        showToast('仅支持 PDF 格式', 'error');
        return;
    }
    if (file.size > 20 * 1024 * 1024) {
        showToast('文件不能超过 20MB', 'error');
        return;
    }

    uploadStatus.textContent = '正在上传并处理...';
    uploadStatus.className = 'upload-status loading';
    progressBar.hidden = false;
    progressFill.style.width = '30%';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData,
        });
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || '上传失败');

        progressFill.style.width = '100%';
        uploadStatus.textContent = data.message || '上传成功';
        uploadStatus.className = 'upload-status success';

        setTimeout(() => {
            progressBar.hidden = true;
            progressFill.style.width = '0%';
            uploadStatus.textContent = '';
        }, 2000);

        showToast(`上传成功！切分为 ${data.chunk_count} 个文本块`, 'success');
        await loadDocuments();

        if (data.id) {
            const docs = await fetch(`${API_BASE}/documents`).then(r => r.json());
            const doc = docs.find(d => d.id === data.id);
            selectDocument(data.id, doc);
        }
    } catch (err) {
        uploadStatus.textContent = err.message;
        uploadStatus.className = 'upload-status error';
        progressBar.hidden = true;
    }
}

// ========== Chat ==========
async function sendQuestion() {
    const question = questionInput.value.trim();
    if (!question || !currentDocId) return;

    // Disable input
    questionInput.disabled = true;
    sendBtn.disabled = true;

    // Add question bubble
    appendMessage('question', question);

    // Add typing indicator
    const typingEl = addTypingIndicator();

    // Clear input
    questionInput.value = '';
    questionInput.style.height = 'auto';
    scrollToBottom();

    try {
        const res = await fetch(`${API_BASE}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ document_id: currentDocId, question }),
        });
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || '问答失败');

        // Remove typing, add answer
        typingEl.remove();
        appendMessage('answer', data.answer, data.sources);
        scrollToBottom();
    } catch (err) {
        typingEl.remove();
        appendMessage('answer', `&#x26A0; 出错了：${err.message}`, []);
        scrollToBottom();
    } finally {
        questionInput.disabled = false;
        sendBtn.disabled = false;
        questionInput.focus();
    }
}

function appendMessage(type, text, sources) {
    const div = document.createElement('div');
    div.className = `message msg-${type}`;

    if (type === 'question') {
        div.innerHTML = `<div class="msg-bubble">${escapeHtml(text)}</div>`;
    } else {
        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            sourcesHtml = `
                <details class="msg-sources">
                    <summary>&#x1F50D; 引用来源（${sources.length}条）</summary>
                    ${sources.map((s, i) => `<div class="source-block">[${i+1}] ${escapeHtml(s)}</div>`).join('')}
                </details>
            `;
        }
        div.innerHTML = `
            <span class="msg-avatar">&#x1F916;</span>
            <div>
                <div class="msg-bubble">${formatAnswer(text)}</div>
                ${sourcesHtml}
            </div>
        `;
    }

    chatMessages.appendChild(div);
}

function addTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'message msg-answer msg-typing';
    div.innerHTML = `
        <span class="msg-avatar">&#x1F916;</span>
        <div class="msg-bubble"><div class="dot-flashing"><span></span><span></span><span></span></div></div>
    `;
    chatMessages.appendChild(div);
    scrollToBottom();
    return div;
}

function formatAnswer(text) {
    // Simple markdown-like formatting
    return escapeHtml(text)
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>')
        .replace(/^/, '<p>')
        .replace(/$/, '</p>');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Send button
sendBtn.addEventListener('click', sendQuestion);

// Enter to send, Shift+Enter for newline
questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendQuestion();
    }
});

// Auto-resize textarea
questionInput.addEventListener('input', () => {
    questionInput.style.height = 'auto';
    questionInput.style.height = Math.min(questionInput.scrollHeight, 120) + 'px';
});

// Suggestion chips
function bindSuggestionChips() {
    document.querySelectorAll('.suggestion-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            questionInput.value = chip.textContent;
            sendQuestion();
        });
    });
}
bindSuggestionChips();

// Doc select change
docSelect.addEventListener('change', async () => {
    const id = parseInt(docSelect.value);
    if (!id) {
        currentDocId = null;
        chatMessages.innerHTML = `
            <div class="welcome-msg">
                <div class="welcome-icon">&#x1F916;</div>
                <h3>你好！我是文档助手</h3>
                <p>上传 PDF 后，选择文档即可开始提问</p>
            </div>
        `;
        docList.querySelectorAll('.doc-item').forEach(el => el.classList.remove('active'));
        return;
    }
    try {
        const docs = await fetch(`${API_BASE}/documents`).then(r => r.json());
        const doc = docs.find(d => d.id === id);
        selectDocument(id, doc);
    } catch (err) {
        console.error(err);
    }
});

// Refresh button
refreshDocsBtn.addEventListener('click', loadDocuments);

// ========== History Drawer ==========
historyToggle.addEventListener('click', async () => {
    if (!currentDocId) {
        showToast('请先选择文档', 'error');
        return;
    }
    await loadHistory();
    historyDrawer.classList.add('open');
    drawerOverlay.classList.add('open');
});

closeDrawer.addEventListener('click', closeDrawerFn);
drawerOverlay.addEventListener('click', closeDrawerFn);

function closeDrawerFn() {
    historyDrawer.classList.remove('open');
    drawerOverlay.classList.remove('open');
}

async function loadHistory() {
    try {
        const res = await fetch(`${API_BASE}/history/${currentDocId}`);
        const records = await res.json();

        if (records.length === 0) {
            historyContent.innerHTML = '<p class="drawer-hint">暂无问答记录</p>';
            return;
        }

        historyContent.innerHTML = records.map(r => `
            <div class="history-item">
                <div class="history-q">&#x2753; ${escapeHtml(r.question)}</div>
                <div class="history-a">${escapeHtml(r.answer).substring(0, 200)}${r.answer.length > 200 ? '...' : ''}</div>
                <div class="history-time">${r.created_at ? new Date(r.created_at).toLocaleString('zh-CN') : ''}</div>
            </div>
        `).join('');
    } catch (err) {
        historyContent.innerHTML = '<p class="drawer-hint">加载失败</p>';
    }
}

// ========== Init ==========
loadDocuments();
// ========== Tab Navigation ==========
document.querySelectorAll(".tab-btn").forEach(function(btn) {
    btn.addEventListener("click", function() {
        document.querySelectorAll(".tab-btn").forEach(function(b) { b.classList.remove("active"); });
        document.querySelectorAll(".tab-content").forEach(function(t) { t.classList.remove("active"); });
        btn.classList.add("active");
        document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
    });
});

// ========== Resume State ==========
var currentResumeId = null;

// ========== Resume Upload ==========
var resumeUploadZone = document.getElementById("resumeUploadZone");
var resumeFileInput = document.getElementById("resumeFileInput");

resumeUploadZone.addEventListener("click", function() { resumeFileInput.click(); });

resumeUploadZone.addEventListener("dragover", function(e) {
    e.preventDefault();
    resumeUploadZone.classList.add("drag-over");
});
resumeUploadZone.addEventListener("dragleave", function() {
    resumeUploadZone.classList.remove("drag-over");
});
resumeUploadZone.addEventListener("drop", function(e) {
    e.preventDefault();
    resumeUploadZone.classList.remove("drag-over");
    var file = e.dataTransfer.files[0];
    if (file) handleResumeUpload(file);
});

resumeFileInput.addEventListener("change", function() {
    var file = resumeFileInput.files[0];
    if (file) handleResumeUpload(file);
    resumeFileInput.value = "";
});

async function handleResumeUpload(file) {
    var status = document.getElementById("resumeUploadStatus");
    status.innerHTML = "<div class=\"upload-status uploading\">正在上传 " + file.name + "...</div>";
    try {
        var formData = new FormData();
        formData.append("file", file);
        var res = await fetch("/api/resume/upload", { method: "POST", body: formData });
        var data = await res.json();
        status.innerHTML = "<div class=\"upload-status success\">" + (data.message || "上传成功") + "</div>";
        loadResumes();
    } catch (err) {
        status.innerHTML = "<div class=\"upload-status error\">上传失败: " + err.message + "</div>";
    }
}

// ========== Load Resumes ==========
async function loadResumes() {
    try {
        var res = await fetch("/api/resume/list");
        var items = await res.json();
        var list = document.getElementById("resumeList");
        if (items.length === 0) {
            list.innerHTML = "<div class=\"empty-state\"><span class=\"empty-icon\">&#x1F4ED;</span><p>暂无简历</p></div>";
            return;
        }
        list.innerHTML = items.map(function(r) {
            var active = r.id === currentResumeId ? "active" : "";
            return "<div class=\"doc-item " + active + "\" data-resume-id=\"" + r.id + "\">" +
                "<span class=\"doc-item-icon\">&#x1F4C4;</span>" +
                "<div class=\"doc-item-info\">" +
                "<div class=\"doc-item-name\">" + escapeHtml(r.filename) + "</div>" +
                "<div class=\"doc-item-meta\">" + r.char_count + " 字" + (r.has_optimized ? " \u2705 已优化" : "") + "</div>" +
                "</div></div>";
        }).join("");
        list.querySelectorAll(".doc-item").forEach(function(item) {
            item.addEventListener("click", function() {
                selectResume(parseInt(item.dataset.resumeId));
            });
        });
    } catch (err) {
        console.error("load resumes error", err);
    }
}

async function selectResume(id) {
    currentResumeId = id;
    document.querySelectorAll("#resumeList .doc-item").forEach(function(el) {
        el.classList.remove("active");
    });
    var target = document.querySelector("#resumeList [data-resume-id=\"" + id + "\"]");
    if (target) target.classList.add("active");
    document.getElementById("optimizeControls").style.display = "block";
    try {
        var res = await fetch("/api/resume/" + id);
        var data = await res.json();
        var content = document.getElementById("resumeContent");
        content.innerHTML = "<div class=\"resume-text\">" + formatResumeText(data.original) + "</div>";
        if (data.optimized) {
            document.getElementById("comparisonView").style.display = "block";
            document.getElementById("cmpOriginal").innerHTML = formatResumeText(data.original);
            document.getElementById("cmpOptimized").innerHTML = formatResumeText(data.optimized);
        } else {
            document.getElementById("comparisonView").style.display = "none";
        }
    } catch (err) {
        console.error("load resume error", err);
    }
}

function formatResumeText(text) {
    return escapeHtml(text)
        .replace(/---/g, "<hr>")
        .replace(/\n\n/g, "</p><p>")
        .replace(/\n/g, "<br>")
        .replace(/^/, "<p>")
        .replace(/$/, "</p>");
}

// ========== Analyze Resume ==========
document.getElementById("analyzeBtn").addEventListener("click", async function() {
    if (!currentResumeId) { alert("请先选择简历"); return; }
    var btn = this;
    btn.disabled = true;
    btn.innerHTML = "&#x23F3; 分析中...";
    var content = document.getElementById("resumeContent");
    try {
        var res = await fetch("/api/resume/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ resume_id: currentResumeId })
        });
        var data = await res.json();
        content.innerHTML = "<div class=\"resume-text\"><h3 style=\"color:var(--accent1);margin-bottom:12px;\">&#x1F50D; AI 简历分析</h3>" +
            formatResumeText(data.analysis) + "</div>";
    } catch (err) {
        content.innerHTML = "<div class=\"resume-text\"><p style=\"color:#ef4444;\">分析失败: " + err.message + "</p></div>";
    }
    btn.disabled = false;
    btn.innerHTML = "&#x1F50D; AI 分析简历";
});

// ========== Optimize Resume ==========
document.getElementById("optimizeBtn").addEventListener("click", async function() {
    if (!currentResumeId) { alert("请先选择简历"); return; }
    var btn = this;
    btn.disabled = true;
    btn.innerHTML = "&#x23F3; 优化中...";
    var target = document.getElementById("optimizeTarget").value;
    var position = document.getElementById("positionInput").value;
    var content = document.getElementById("resumeContent");
    try {
        var res = await fetch("/api/resume/optimize", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ resume_id: currentResumeId, target: target, position: position })
        });
        var data = await res.json();
        // Show comparison
        document.getElementById("comparisonView").style.display = "block";
        document.getElementById("cmpOriginal").innerHTML = formatResumeText(data.original);
        document.getElementById("cmpOptimized").innerHTML = formatResumeText(data.optimized);
        content.innerHTML = "<div class=\"resume-text\"><h3 style=\"color:#10b981;margin-bottom:12px;\">&#x2728; 优化完成！</h3>" +
            formatResumeText(data.optimized) + "</div>";
        loadResumes();
    } catch (err) {
        content.innerHTML = "<div class=\"resume-text\"><p style=\"color:#ef4444;\">优化失败: " + err.message + "</p></div>";
    }
    btn.disabled = false;
    btn.innerHTML = "&#x2728; AI 优化简历";
});

// ========== Optimize Target Change ==========
document.getElementById("optimizeTarget").addEventListener("change", function() {
    document.getElementById("positionGroup").style.display =
        this.value === "position" ? "block" : "none";
});

// ========== Comparison View Tabs ==========
document.querySelectorAll(".cmp-tab").forEach(function(btn) {
    btn.addEventListener("click", function() {
        document.querySelectorAll(".cmp-tab").forEach(function(b) { b.classList.remove("active"); });
        btn.classList.add("active");
        var body = document.getElementById("comparisonBody");
        if (btn.dataset.view === "optimized") {
            body.classList.add("single-view");
        } else {
            body.classList.remove("single-view");
        }
    });
});

// ========== Refresh Resumes ==========
document.getElementById("refreshResumes").addEventListener("click", loadResumes);

// Remove old suggestion chips for resume page
// Bind new suggestion chips
setTimeout(function() {
    document.querySelectorAll("#tab-resume .suggestion-chip").forEach(function(chip) {
        chip.addEventListener("click", function() {
            if (chip.textContent.indexOf("分析") >= 0) {
                document.getElementById("analyzeBtn").click();
            } else {
                document.getElementById("optimizeBtn").click();
            }
        });
    });
}, 100);


// ========== Section Optimization ==========
document.addEventListener("click", function(e) {
    var btn = e.target.closest(".section-opt-btn");
    if (!btn) return;
    if (!currentResumeId) { alert("请先选择简历"); return; }

    var section = btn.dataset.section;
    var sectionNames = { project: "项目经验", skill: "专业技能", summary: "自我评价", education: "教育背景" };
    var content = document.getElementById("resumeContent");
    content.innerHTML = "<div class=\"resume-text\"><p style=\"color:var(--text-secondary);\">正在优化「" + sectionNames[section] + "」...</p></div>";

    fetch("/api/resume/optimize-section", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_id: currentResumeId, section: section })
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
        content.innerHTML = "<div class=\"resume-text\"><h3 style=\"color:#10b981;margin-bottom:12px;\">&#x2728; 优化后的「" + sectionNames[section] + "」</h3>" +
            formatResumeText(data.optimized) + "</div>";
    })
    .catch(function(err) {
        content.innerHTML = "<div class=\"resume-text\"><p style=\"color:#ef4444;\">优化失败: " + err.message + "</p></div>";
    });
});
