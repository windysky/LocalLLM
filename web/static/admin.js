// Main API base (LLM server) and local proxy through this web app
const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`;
const ADMIN_API_BASE = '';
let currentModels = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function () {
    loadModels();
    setInterval(loadModels, 10000); // Refresh every 10 seconds
    loadHfTokenStatus(); // Load token status
});

function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected tab
    document.getElementById(tabName + '-tab').classList.add('active');

    // Try to highlight the clicked tab
    if (event && event.target) {
        event.target.classList.add('active');
    }

    // Load tab-specific content
    if (tabName === 'system') {
        loadSystemInfo();
    }
}

async function loadModels() {
    try {
        // Increase timeout for model status check
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout for status check

        const response = await fetch('/api/models', {
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        if (!data || data.success === false) {
            throw new Error(data?.message || 'Failed to load models');
        }

        // If proxied format, unwrap
        const available = data.available || data.data || [];
        currentModels = available;
        const loaded = data.loaded || [];

        // Create downloaded object from models present on disk (downloaded or incomplete)
        const downloaded = {};
        currentModels.forEach(model => {
            if (model.status === 'downloaded' || model.status === 'incomplete') {
                downloaded[model.name] = {
                    size_gb: model.size_gb,
                    status: model.status
                };
            }
        });

        // Update stats
        document.getElementById('totalModels').textContent = currentModels.length;
        document.getElementById('downloadedModels').textContent = Object.keys(downloaded).length;
        document.getElementById('loadedModels').textContent = loaded.length;

        // Calculate disk usage
        let totalSize = 0;
        for (const [name, info] of Object.entries(downloaded)) {
            if (info.size_gb && info.size_gb !== 'N/A') {
                totalSize += parseFloat(info.size_gb);
            }
        }
        document.getElementById('diskUsage').textContent = `${totalSize.toFixed(1)} GB`;

        // Render model grid
        renderModels(currentModels, downloaded, loaded);

    } catch (error) {
        console.error('Failed to load models:', error);
        document.getElementById('modelGrid').innerHTML =
            '<div class="loading">Failed to load models. Is the server running?<br><small>Error: ' + error.message + '</small></div>';
    }
}

function renderModels(models, downloaded, loaded) {
    const grid = document.getElementById('modelGrid');

    if (models.length === 0) {
        grid.innerHTML = '<div class="loading">No models available</div>';
        return;
    }

    grid.innerHTML = '';

    // Create and append each model card
    models.forEach(model => {
        const isDownloaded = model.name in downloaded;
        const isIncomplete = isDownloaded && downloaded[model.name].status === 'incomplete';
        const isLoaded = loaded.some(m => m.name === model.name);
        const info = downloaded[model.name] || {};

        const modelCard = document.createElement('div');
        modelCard.className = 'model-card';

        // Model name and status
        const modelNameDiv = document.createElement('div');
        modelNameDiv.className = 'model-name';
        modelNameDiv.textContent = model.name;
        modelCard.appendChild(modelNameDiv);

        // Status badge
        const statusSpan = document.createElement('span');
        statusSpan.className = 'model-status ' +
            (isLoaded ? 'status-loaded'
                : isDownloaded
                    ? (isIncomplete ? 'status-not-downloaded' : 'status-downloaded')
                    : 'status-not-downloaded');
        statusSpan.textContent =
            isLoaded ? 'Loaded' :
                isDownloaded ? (isIncomplete ? 'Incomplete' : 'Downloaded') : 'Not Downloaded';
        modelCard.appendChild(statusSpan);

        // Meta info
        const metaDiv = document.createElement('div');
        metaDiv.className = 'model-meta';
        metaDiv.innerHTML = 'Type: ' + (model.type || 'Unknown') + '<br>';
        if (info.size_gb) {
            metaDiv.innerHTML += 'Size: ' + info.size_gb + ' GB';
        }
        modelCard.appendChild(metaDiv);

        // Actions container
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'model-actions';

        if (!isDownloaded) {
            // Just show download button for all models
            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'btn-primary';
            downloadBtn.textContent = 'Download';
            downloadBtn.id = 'download-' + model.name;
            downloadBtn.onclick = () => downloadModel(model.name);
            actionsDiv.appendChild(downloadBtn);
        } else if (isLoaded) {
            const unloadBtn = document.createElement('button');
            unloadBtn.className = 'btn-warning';
            unloadBtn.textContent = 'Unload';
            unloadBtn.onclick = (e) => unloadModel(model.name, e);
            actionsDiv.appendChild(unloadBtn);
        } else {
            const loadBtn = document.createElement('button');
            loadBtn.className = 'btn-success';
            loadBtn.textContent = 'Load';
            loadBtn.onclick = (e) => loadModel(model.name, e);
            actionsDiv.appendChild(loadBtn);
        }

        if (isDownloaded && !isLoaded) {
            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn-danger';
            removeBtn.textContent = 'Remove from Disk';
            removeBtn.onclick = (e) => removeModel(model.name, e);
            actionsDiv.appendChild(removeBtn);
        }

        modelCard.appendChild(actionsDiv);
        grid.appendChild(modelCard);
    });
}

window.downloadModel = async function downloadModel(modelName, event) {
    // Show a quick-select for format using a simple prompt fallback
    const typeSelect = document.createElement('select');
    typeSelect.innerHTML = `
        <option value="safetensors">safetensors</option>
        <option value="gguf">gguf</option>
        <option value="pytorch">pytorch</option>
    `;
    typeSelect.style.fontSize = '16px';
    typeSelect.style.padding = '8px';
    typeSelect.style.marginTop = '10px';

    const modal = document.createElement('div');
    modal.style.position = 'fixed';
    modal.style.top = 0;
    modal.style.left = 0;
    modal.style.width = '100%';
    modal.style.height = '100%';
    modal.style.background = 'rgba(0,0,0,0.4)';
    modal.style.display = 'flex';
    modal.style.justifyContent = 'center';
    modal.style.alignItems = 'center';
    modal.style.zIndex = '9999';

    const box = document.createElement('div');
    box.style.background = 'white';
    box.style.padding = '20px';
    box.style.borderRadius = '8px';
    box.style.minWidth = '260px';
    box.style.boxShadow = '0 10px 30px rgba(0,0,0,0.2)';
    box.innerHTML = `<h3 style="margin-bottom:10px;">Select format for ${modelName}</h3>`;
    box.appendChild(typeSelect);

    const btnRow = document.createElement('div');
    btnRow.style.marginTop = '12px';
    btnRow.style.display = 'flex';
    btnRow.style.justifyContent = 'flex-end';
    btnRow.style.gap = '8px';

    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = 'Cancel';
    cancelBtn.onclick = () => document.body.removeChild(modal);
    const okBtn = document.createElement('button');
    okBtn.textContent = 'Download';
    okBtn.style.background = '#667eea';
    okBtn.style.color = 'white';
    okBtn.style.border = 'none';
    okBtn.style.padding = '8px 12px';
    okBtn.style.borderRadius = '5px';

    btnRow.appendChild(cancelBtn);
    btnRow.appendChild(okBtn);
    box.appendChild(btnRow);
    modal.appendChild(box);
    document.body.appendChild(modal);

    okBtn.onclick = async () => {
        const type = typeSelect.value;
        document.body.removeChild(modal);

        const button = document.getElementById('download-' + modelName);
        if (button) {
            button.disabled = true;
            button.textContent = 'Downloading...';
        }

        try {
            const response = await fetch(API_BASE + '/models/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model: modelName, type })
            });

            const result = await response.json();

            if (response.ok) {
                showInfo('✅ Downloading ' + modelName + ' started!\n\nThis may take several minutes.');

                // Check progress periodically
                const checkInterval = setInterval(async () => {
                    try {
                        console.log('Checking download progress for', modelName);
                        const progressResponse = await fetch(API_BASE + '/models/download/' + encodeURIComponent(modelName) + '/progress');
                        const progressData = await progressResponse.json();
                        console.log('Progress data:', progressData);

                        if (progressData.status === 'completed') {
                            console.log('Download completed for', modelName);
                            clearInterval(checkInterval);
                            showSuccess('✅ ' + modelName + ' downloaded successfully!');
                            loadModels();
                        } else if (progressData.status === 'failed') {
                            console.log('Download failed for', modelName, progressData.message);
                            clearInterval(checkInterval);
                            showError('❌ Failed to download ' + modelName + ':\n' + progressData.message);
                            loadModels();
                        } else if (progressData.status === 'downloading') {
                            // Update button with progress
                            console.log('Download in progress for', modelName, ':', progressData.progress + '%');
                            if (button) {
                                button.textContent = `Downloading... ${progressData.progress}%`;
                                button.className = 'btn-downloading';
                            }
                        }
                    } catch (e) {
                        console.error('Error checking progress:', e);
                    }
                }, 2000); // Check every 2 seconds for smoother updates

                // Stop checking after 5 minutes
                setTimeout(() => clearInterval(checkInterval), 300000);

            } else {
                // Check if this is actually a success message (model already downloaded)
                if (result.message && result.message.includes('already downloaded')) {
                    showSuccess('✅ ' + modelName + ' is already downloaded!');
                    loadModels();
                    if (button) {
                        button.disabled = false;
                        button.textContent = 'Download';
                        button.className = 'btn-download';
                    }
                    return;
                }

                const errorMsg = result.detail || result.message || 'Unknown error';
                let fullErrorMessage = '❌ Failed to download ' + modelName + ':\n' + errorMsg;

                // Add specific help based on error
                if (errorMsg.includes('403') || errorMsg.includes('not authorized') || errorMsg.includes('restricted')) {
                    fullErrorMessage += '\n\n📋 This model requires access approval:\n';
                    fullErrorMessage += '1. Visit the model page on Hugging Face\n';
                    fullErrorMessage += '2. Click "Request access" and accept the license terms\n';
                    fullErrorMessage += '3. Wait for approval (usually immediate)\n';
                    fullErrorMessage += '4. Try downloading again';
                } else if (errorMsg.includes('401') || errorMsg.includes('authenticated')) {
                    fullErrorMessage += '\n\n🔑 Authentication required:\n';
                    fullErrorMessage += '1. Save your Hugging Face token in System tab\n';
                    fullErrorMessage += '2. Ensure you have been granted access\n';
                    fullErrorMessage += '3. Restart the server and try again';
                }

                showError(fullErrorMessage);

                if (button) {
                    button.disabled = false;
                    button.textContent = 'Download';
                    button.className = 'btn-primary';
                }
            }
        } catch (error) {
            showError('❌ Error downloading model: ' + error.message);

            if (button) {
                button.disabled = false;
                button.textContent = 'Download';
                button.className = 'btn-primary';
            }
        }
    }; // Close okBtn.onclick
}; // Close downloadModel

function showAuthWarning(modelName) {
    const repoUrl = 'https://huggingface.co/' + getModelRepoId(modelName);
    const userAction = confirm('🔒 Authentication Required for ' + modelName + '\n\n' +
        'This model requires access to Hugging Face.\n\n' +
        'Click OK to open the Hugging Face page to request access');

    if (userAction) {
        window.open(repoUrl, '_blank');
    }
}

function getModelRepoId(modelName) {
    const repoMap = {
        'gemma-2-9b': 'google/gemma-2-9b-it',
        'gemma-2-9b-it': 'google/gemma-2-9b-it',
        'llama-3.1-8b': 'meta-llama/Llama-3.1-8B',
        'llama-3.1-8b-instruct': 'meta-llama/Llama-3.1-8B-Instruct'
    };
    return repoMap[modelName] || modelName;
}

window.loadModel = async function loadModel(modelName, evt) {
    console.log('loadModel called for:', modelName);
    if (!confirm('Load model ' + modelName + '?\n\nThis will make the model ready for use and may take a moment.')) {
        return;
    }

    // Disable button and show loading
    const button = evt?.target;
    const originalText = button?.textContent;
    if (button) {
        button.disabled = true;
        button.textContent = 'Loading...';
    }

    try {
        const response = await fetch(`/api/models/${encodeURIComponent(modelName)}/load`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Load response:', result); // Debug log

            if (result.success && result.message && result.message.includes('successfully')) {
                alert('✅ ' + modelName + ' loaded successfully!\n\nYou can now use it for chat completions.');
                loadModels();
            } else if (result.success) {
                alert('✅ ' + modelName + ' loaded successfully!\n\nYou can now use it for chat completions.');
                loadModels();
            } else {
                alert('⚠️ Model load response: ' + (result.message || 'Unknown response'));
                loadModels();
            }
        } else {
            const errorData = await response.json();
            alert('❌ Failed to load ' + modelName + ':\n' + (errorData.detail || errorData.message || 'Unknown error'));

            if (button) {
                button.disabled = false;
                button.textContent = originalText;
            }
        }
    } catch (error) {
        alert('❌ Error loading model: ' + error.message);

        if (button) {
            button.disabled = false;
            button.textContent = originalText;
        }
    }
}

window.unloadModel = async function unloadModel(modelName, evt) {
    console.log('unloadModel called for:', modelName);
    if (!confirm('Unload model ' + modelName + '?\n\nThis will free up memory but the model will remain on disk.')) {
        return;
    }

    try {
        const response = await fetch(`/api/models/${encodeURIComponent(modelName)}/unload`, {
            method: 'POST'
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Unload response:', result); // Debug log

            if (result.success && result.message && result.message.includes('successfully')) {
                alert('✅ ' + modelName + ' unloaded successfully');
                loadModels();
            } else if (result.success) {
                alert('✅ ' + modelName + ' unloaded successfully');
                loadModels();
            } else {
                alert('⚠️ Model unload: ' + (result.message || 'Unknown response'));
                loadModels();
            }
        } else {
            const errorData = await response.json();
            alert('❌ Failed to unload ' + modelName + ': ' + (errorData.detail || errorData.message || 'Unknown error'));
        }
    } catch (error) {
        alert('❌ Error unloading model: ' + error.message);
    }
}

window.removeModel = async function removeModel(modelName, evt) {
    console.log('removeModel called for:', modelName);
    if (!confirm('Remove ' + modelName + ' from disk?\n\n⚠️ This will permanently delete all downloaded files for this model and cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`/api/models/${encodeURIComponent(modelName)}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            const result = await response.json();
            alert('✅ ' + result.message);
            // Wait a moment for the filesystem to update, then refresh
            setTimeout(loadModels, 500);
        } else {
            const errorData = await response.json();
            showError('❌ Failed to remove ' + modelName + ':\n' + (errorData.detail || errorData.message || 'Unknown error'));
        }
    } catch (error) {
        showError('❌ Error removing model: ' + error.message);
    }
}

function closeModal() {
    document.getElementById('addModelModal').style.display = 'none';
}

async function searchModels() {
    const query = document.getElementById('searchInput').value;
    if (!query) return;

    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<div class="loading">🔍 Searching Hugging Face...</div>';

    try {
        const response = await fetch('/api/search/huggingface?query=' + encodeURIComponent(query) + '&limit=10');
        const data = await response.json();

        if (data.success && data.models.length > 0) {
            resultsDiv.innerHTML = data.models.map(model => `
                <div class="search-result-item" onclick="showAddModelDialog('${model.id}')">
                    <div class="search-result-title">${model.id}</div>
                    <div class="search-result-meta">
                        ${model.author ? 'by ' + model.author + ' | ' : ''}
                        Downloads: ${model.downloads.toLocaleString()} |
                        Likes: ${model.likes.toLocaleString()}
                        ${model.pipeline_tag ? ' | ' + model.pipeline_tag : ''}
                    </div>
                    ${model.description ? '<div class="search-result-desc">' + model.description.substring(0, 150) + '...</div>' : ''}
                </div>
            `).join('');
        } else {
            resultsDiv.innerHTML = '<div class="loading">No models found for "' + query + '". Try different keywords.</div>';
        }
    } catch (error) {
        console.error('Search error:', error);
        resultsDiv.innerHTML = '<div class="loading">Search failed: ' + error.message + '</div>';
    }
}

function showAddModelDialog(modelId) {
    const modal = document.getElementById('addModelModal');
    const modalBody = document.getElementById('modalBody');

    // Extract a meaningful local name from the model ID
    const localName = extractLocalName(modelId);

    modalBody.innerHTML = `
        <p><strong>Model:</strong> ${modelId}</p>
        <p><strong>Local Name:</strong> <input type="text" id="localName" value="${localName}" placeholder="Enter a name for local reference" style="width: 100%; padding: 8px; margin: 10px 0;"></p>
        <p><strong>Type:</strong> <select id="modelType" style="padding: 8px;">
            <option value="safetensors">Safetensors</option>
            <option value="gguf">GGUF</option>
            <option value="pytorch">PyTorch</option>
        </select></p>
        <p><strong>Files:</strong> <input type="text" id="modelFiles" placeholder="e.g., model.safetensors, config.json (comma-separated)" style="width: 100%; padding: 8px; margin: 10px 0;"></p>
        <div style="margin-top: 20px;">
            <button class="btn-primary" onclick="addModelToRegistry('${modelId}')">Add to Registry</button>
            <button onclick="closeModal()" style="margin-left: 10px;">Cancel</button>
        </div>
    `;

    modal.style.display = 'block';
}

function extractLocalName(modelId) {
    // Extract a clean, lowercase name from the model ID
    const parts = modelId.split('/');
    const modelPart = parts[parts.length - 1]; // Get the last part after /

    // Convert to lowercase and replace common patterns
    let localName = modelPart
        .toLowerCase()
        .replace(/[^a-z0-9-]/g, '-') // Replace non-alphanumeric with hyphens
        .replace(/-+/g, '-') // Replace multiple hyphens with single
        .replace(/^-|-$/g, ''); // Remove leading/trailing hyphens

    // Common name mappings
    const nameMappings = {
        'deepseek-r1-distill-qwen-32b': 'deepseek-r1-32b',
        'deepseek-r1-distill-qwen-1-5b': 'deepseek-r1-1.5b',
        'deepseek-ocr': 'deepseek-ocr',
        'phi-3-mini-4k-instruct': 'phi-3-mini',
        'phi-3-small-8k-instruct': 'phi-3-small',
        'phi-3-medium-14b-instruct': 'phi-3-medium',
        'llama-2-7b-chat-hf': 'llama-2-7b-chat',
        'llama-2-13b-chat-hf': 'llama-2-13b-chat',
        'mistral-7b-instruct-v0-3': 'mistral-7b-instruct',
        'code-llama-7b-instruct-hf': 'codellama-7b-instruct',
        'tinyllama-1-1b-chat-v1-0': 'tinyllama-1.1b-chat'
    };

    return nameMappings[localName] || localName;
}

function addModelToRegistry(modelId) {
    const localName = document.getElementById('localName').value || extractLocalName(modelId);
    const modelType = document.getElementById('modelType').value;
    const modelFiles = document.getElementById('modelFiles').value || '';

    // Validation
    if (!localName) {
        alert('Please enter a local name for the model.');
        return;
    }

    // Build the YAML entry for the model
    const yamlEntry = `  ${localName}:
    repo_id: "${modelId}"
    files: [
      ${modelFiles ? modelFiles.split(',').map(f => '"' + f.trim() + '"').join(',\n      ') : '"model.safetensors", "config.json", "tokenizer.json"'}
    ]
    type: "${modelType}"
    description: "Model added from Hugging Face: ${modelId}"`;

    alert('✅ Model Configuration:\n\n' + yamlEntry + '\n\n' +
        'To add this model to your LocalLLM registry:\n\n' +
        '1. Add the above to your models.yaml file\n' +
        '2. Run: python update_model_registry.py\n' +
        '3. Restart the LocalLLM server\n\n' +
        'Note: You may need to specify the correct files for this model.');

    // Optionally copy to clipboard
    navigator.clipboard.writeText(yamlEntry);
    setTimeout(() => alert('Configuration copied to clipboard!'), 100);

    closeModal();
}

async function loadSystemInfo() {
    const infoDiv = document.getElementById('systemInfo');

    try {
        // Get models info for health status
        const modelsResponse = await fetch(API_BASE + '/models/status');
        const modelsData = await modelsResponse.json();

        // Get Ollama info
        const ollamaResponse = await fetch('http://localhost:11434/api/tags');
        const ollamaData = await ollamaResponse.json();

        infoDiv.innerHTML = `
            <div class="info-item">
                <div class="info-label">Server Status</div>
                <div class="info-value">✅ Healthy</div>
            </div>
            <div class="info-item">
                <div class="info-label">Models Loaded</div>
                <div class="info-value">${modelsData.loaded ? modelsData.loaded.length : 0}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Ollama Models</div>
                <div class="info-value">${ollamaData.models?.length || 0} models</div>
            </div>
            <div class="info-item">
                <div class="info-label">Server Uptime</div>
                <div class="info-value">${new Date().toLocaleString()}</div>
            </div>
            <div class="info-item">
                <div class="info-label">API Endpoints</div>
                <div class="info-value">
                    <a href="${API_BASE}/v1/models" target="_blank" style="color: #667eea;">Models API</a><br>
                    <a href="${API_BASE}/health" target="_blank" style="color: #667eea;">Health Check</a>
                </div>
            </div>
        `;
    } catch (error) {
        infoDiv.innerHTML = '<div class="loading">Failed to load system information</div>';
    }
}

// Search on Enter key
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            searchModels();
        }
    });
}

// Close modal on outside click
window.onclick = function (event) {
    const modal = document.getElementById('addModelModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

// Hugging Face Token Management
async function saveHfToken() {
    const token = document.getElementById('hfToken').value.trim();

    if (!token) {
        alert('Please enter a valid token');
        return;
    }

    try {
        const response = await fetch('/api/settings/hf_token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: token })
        });

        const result = await response.json();

        if (result.success) {
            alert('✅ ' + result.message);
            // Clear the input field for security
            document.getElementById('hfToken').value = '';
            // Show current token status
            loadHfTokenStatus();
        } else {
            alert('❌ Failed to save token: ' + result.message);
        }
    } catch (error) {
        alert('❌ Error saving token: ' + error.message);
    }
}

async function loadHfTokenStatus() {
    try {
        const response = await fetch('/api/settings/hf_token');
        const result = await response.json();

        if (result.success) {
            if (result.has_token) {
                // Update UI to show token exists
                const tokenInput = document.getElementById('hfToken');
                if (tokenInput) {
                    tokenInput.placeholder = 'Token is set (click to update)';
                }
            }
        }
    } catch (error) {
        console.error('Failed to load token status:', error);
    }
}

// Notification System
function showNotification(message, type = 'info', duration = 0) {
    const notificationArea = document.getElementById('notificationArea');
    const notification = document.getElementById('notification');
    const notificationText = document.getElementById('notificationText');

    if (!notificationArea || !notification || !notificationText) return;

    // Set message and type
    notificationText.textContent = message;
    notification.className = 'notification ' + type;

    // Show notification
    notificationArea.style.display = 'block';

    // Auto-hide after duration (if specified)
    if (duration > 0) {
        setTimeout(() => {
            hideNotification();
        }, duration);
    }
}

window.hideNotification = function () {
    const notificationArea = document.getElementById('notificationArea');
    if (notificationArea) {
        notificationArea.style.display = 'none';
    }
}

// Helper functions to replace alert()
function showError(message) {
    showNotification(message, 'error');
}

function showSuccess(message) {
    showNotification(message, 'success', 5000); // Auto-hide success after 5 seconds
}

function showInfo(message) {
    showNotification(message, 'info', 5000); // Auto-hide info after 5 seconds
}

console.log('Admin functions loaded');
