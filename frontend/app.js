const API_URL = 'http://localhost:8000';

// DOM Elements
const codeInput = document.getElementById('code-input');
const filenameInput = document.getElementById('filename');
const runBtn = document.getElementById('run-btn');
const loader = document.getElementById('loader');
const statusText = document.getElementById('status-text');
const resultsDisplay = document.getElementById('results-display');
const placeholder = document.getElementById('placeholder');
const verdictBanner = document.getElementById('verdict-banner');
const verdictLabel = document.getElementById('verdict-label');
const verdictReason = document.getElementById('verdict-reason');
const verdictIcon = document.getElementById('verdict-icon');

const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

const reviewContent = document.getElementById('review-content');
const docsContent = document.getElementById('docs-content');
const rawContent = document.getElementById('raw-content');

// Event Listeners
runBtn.addEventListener('click', runAnalysis);

tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.getAttribute('data-tab');
        switchTab(tabName);
    });
});

async function runAnalysis() {
    const code = codeInput.value.trim();
    if (!code) {
        alert('Please enter some code first.');
        return;
    }

    // Reset UI
    placeholder.classList.add('hidden');
    resultsDisplay.classList.add('hidden');
    loader.classList.remove('hidden');
    runBtn.disabled = true;
    statusText.innerText = 'Agents are analyzing your code...';

    try {
        const response = await fetch(`${API_URL}/review`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                filename: filenameInput.value || 'main.py'
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.error(error);
        alert(`Failed to run analysis: ${error.message}`);
        placeholder.classList.remove('hidden');
    } finally {
        loader.classList.add('hidden');
        runBtn.disabled = false;
    }
}

function displayResults(data) {
    resultsDisplay.classList.remove('hidden');
    
    // Verdict
    const isSafe = data.label.toLowerCase() === 'safe';
    verdictBanner.className = `verdict-banner ${isSafe ? 'safe' : 'needs-work'}`;
    verdictLabel.innerText = data.label;
    verdictReason.innerText = data.reason;
    verdictIcon.innerText = isSafe ? '✓' : '⚠';

    // Content
    reviewContent.innerHTML = formatMarkdown(data.review);
    docsContent.innerHTML = formatMarkdown(data.docs);
    rawContent.innerText = JSON.stringify(data, null, 2);

    switchTab('review');
}

function switchTab(tabName) {
    tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabName);
    });
    
    tabContents.forEach(content => {
        content.classList.toggle('hidden', content.id !== `${tabName}-tab`);
    });
}

// Simple Markdown Formatter (since we don't want to load a heavy lib if not needed)
function formatMarkdown(text) {
    if (!text) return '_No content generated._';
    
    return text
        .replace(/^### (.*$)/gm, '<h3>$1</h3>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        .replace(/^\* (.*$)/gm, '<li>$1</li>')
        .replace(/^- (.*$)/gm, '<li>$1</li>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\*\*(.*)\*\*/g, '<strong>$1</strong>')
        .replace(/\n\n/g, '<br>')
        .replace(/\n/g, '<br>');
}
