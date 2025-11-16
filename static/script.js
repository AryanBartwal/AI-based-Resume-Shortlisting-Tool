// File Upload Handling
const fileInput = document.getElementById('resume-files');
const fileList = document.getElementById('file-list');
const uploadArea = document.getElementById('file-upload-area');

fileInput.addEventListener('change', handleFileSelect);

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#4F46E5';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = '#D1D5DB';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#D1D5DB';
    
    const files = e.dataTransfer.files;
    fileInput.files = files;
    handleFileSelect();
});

function handleFileSelect() {
    const files = fileInput.files;
    fileList.innerHTML = '';
    
    if (files.length > 0) {
        document.querySelector('.upload-placeholder').style.display = 'none';
        
        Array.from(files).forEach(file => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            
            const fileSize = formatFileSize(file.size);
            
            fileItem.innerHTML = `
                <div class="file-item-info">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/>
                    </svg>
                    <div>
                        <div class="file-item-name">${file.name}</div>
                        <div class="file-item-size">${fileSize}</div>
                    </div>
                </div>
            `;
            
            fileList.appendChild(fileItem);
        });
    } else {
        document.querySelector('.upload-placeholder').style.display = 'block';
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Form Submission
document.getElementById('upload-form').addEventListener('submit', handleUploadSubmit);

async function handleUploadSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const files = fileInput.files;
    
    if (files.length === 0) {
        showError('Please select at least one PDF file');
        return;
    }
    
    showLoading();
    clearResults();
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to process resumes');
        }
        
        hideLoading();
        displayResults(data);
        
    } catch (error) {
        hideLoading();
        showError(error.message);
    }
}

// Display Results
function displayResults(data) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.classList.remove('hidden');
    
    let html = `
        <div class="results-header">
            <h2>📊 Ranking Results</h2>
            <div class="results-stats">
                <div class="stat-item">
                    <div class="stat-value">${data.total_resumes}</div>
                    <div class="stat-label">Resumes</div>
                </div>
            </div>
        </div>
        
        <div class="job-req-display">
            <h3>Job Requirements</h3>
            <p>${escapeHtml(data.job_requirements)}</p>
        </div>
    `;
    
    // Display detailed analysis for top candidates
    data.detailed_analysis.forEach(result => {
        const recommendation = getRecommendation(result.match_percentage);
        const rankClass = result.rank <= 3 ? `rank-${result.rank}` : 'rank-other';
        
        html += `
            <div class="resume-card">
                <div class="resume-card-header">
                    <div class="resume-rank">
                        <div class="rank-badge ${rankClass}">#${result.rank}</div>
                        <div class="resume-info">
                            <h3>${escapeHtml(result.filename)}</h3>
                            <div class="resume-category">Category: ${escapeHtml(result.category)}</div>
                        </div>
                    </div>
                    <div class="match-score">
                        <div class="score-value">${result.match_percentage}%</div>
                        <div class="score-label">Match Score</div>
                    </div>
                </div>
                
                <div class="recommendation ${recommendation.class}">
                    ${recommendation.icon} ${recommendation.text}
                </div>
                
                <div class="keywords-section">
                    ${result.matching_keywords.length > 0 ? `
                        <div class="keywords-group">
                            <h4>✓ Matching Keywords (${result.matching_keywords.length})</h4>
                            <div class="keyword-tags">
                                ${result.matching_keywords.map(kw => 
                                    `<span class="keyword-tag keyword-match">${escapeHtml(kw)}</span>`
                                ).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${result.missing_keywords.length > 0 ? `
                        <div class="keywords-group">
                            <h4>✗ Missing Keywords (${result.missing_keywords.length})</h4>
                            <div class="keyword-tags">
                                ${result.missing_keywords.map(kw => 
                                    `<span class="keyword-tag keyword-missing">${escapeHtml(kw)}</span>`
                                ).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    // Show remaining results (simplified)
    if (data.results.length > 3) {
        html += '<h3 style="margin: 30px 0 20px; color: #6B7280;">Other Candidates</h3>';
        
        data.results.slice(3).forEach((result, index) => {
            const rank = index + 4;
            html += `
                <div class="resume-card">
                    <div class="resume-card-header">
                        <div class="resume-rank">
                            <div class="rank-badge rank-other">#${rank}</div>
                            <div class="resume-info">
                                <h3>${escapeHtml(result.filename)}</h3>
                                <div class="resume-category">Category: ${escapeHtml(result.category)}</div>
                            </div>
                        </div>
                        <div class="match-score">
                            <div class="score-value">${result.match_percentage}%</div>
                            <div class="score-label">Match Score</div>
                        </div>
                    </div>
                </div>
            `;
        });
    }
    
    resultsDiv.innerHTML = html;
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function getRecommendation(score) {
    if (score >= 80) {
        return {
            text: 'HIGHLY RECOMMENDED',
            class: 'rec-high',
            icon: '⭐'
        };
    } else if (score >= 65) {
        return {
            text: 'RECOMMENDED',
            class: 'rec-good',
            icon: '✓'
        };
    } else {
        return {
            text: 'MODERATE MATCH',
            class: 'rec-moderate',
            icon: '⚠'
        };
    }
}

// Utility Functions
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function clearResults() {
    document.getElementById('results').classList.add('hidden');
    document.getElementById('results').innerHTML = '';
}

function showError(message) {
    alert('Error: ' + message);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
