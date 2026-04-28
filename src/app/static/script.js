/**
 * AI Fraud Detection Agent - Frontend JavaScript
 * Handles file uploads, polling for results, and displaying analysis outcomes.
 */

/**
 * Escape HTML special characters to prevent XSS.
 * @param {string} text - Raw text to escape
 * @returns {string} HTML-escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const loadingSection = document.getElementById('loading');
    const resultsSection = document.getElementById('results');
    const demoBtn = document.getElementById('demo-btn');
    const newAnalysisBtn = document.getElementById('new-analysis-btn');

    let pollInterval = null;
    let currentTaskId = null;

    // Form submission handler
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await handleUpload();
    });

    // Demo data button
    demoBtn.addEventListener('click', function() {
        loadDemoData();
    });

    // New analysis button
    newAnalysisBtn.addEventListener('click', function() {
        resetToUpload();
    });

    /**
     * Handle file upload and analysis request
     */
    async function handleUpload() {
        const bankFile = document.getElementById('bank-statement').files[0];
        const taxFile = document.getElementById('tax-return').files[0];

        if (!bankFile || !taxFile) {
            alert('Please select both a bank statement and a tax return file.');
            return;
        }

        // Show loading
        showLoading();

        try {
            const formData = new FormData();
            formData.append('bank_statement', bankFile);
            formData.append('tax_return', taxFile);

            const response = await fetch('/upload/', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }

            const data = await response.json();
            currentTaskId = data.task_id;

            // Start polling for results
            startPolling(currentTaskId);

        } catch (error) {
            console.error('Upload error:', error);
            alert('Error uploading files: ' + error.message);
            resetToUpload();
        }
    }

    /**
     * Load demo data automatically
     */
    function loadDemoData() {
        // Load sample CSV files from server
        document.getElementById('bank-statement').value = ''; // Clear for demo
        document.getElementById('tax-return').value = '';

        showLoading();

        // Simulate analysis with pre-loaded demo
        fetch('/api/sample-data')
            .then(res => res.json())
            .then(sampleData => {
                // In a real implementation, we'd create Blob URLs for the sample CSVs
                // For demo purposes, we'll trigger a direct analysis call
                startDemoAnalysis(sampleData);
            })
            .catch(err => {
                console.error('Failed to load sample data:', err);
                alert('Demo data unavailable. Please upload files manually.');
                resetToUpload();
            });
    }

    /**
     * Start a demo analysis using sample data
     */
    async function startDemoAnalysis(sampleData) {
        try {
            // For demo, we'll call a special endpoint or simulate
            // In production, you'd have pre-loaded sample files
            alert('Demo mode: In a full implementation, sample CSV files would be auto-loaded. For now, please upload sample_bank_statements.csv and sample_tax_returns.csv manually from the data/ folder.');
            resetToUpload();
        } catch (error) {
            console.error('Demo analysis error:', error);
            resetToUpload();
        }
    }

    /**
     * Poll for results
     */
    function startPolling(taskId) {
        let attempts = 0;
        const maxAttempts = 60; // 2 minutes max

        pollInterval = setInterval(async function() {
            attempts++;

            try {
                const response = await fetch(`/results/${taskId}`);
                const data = await response.json();

                if (data.status === 'completed') {
                    clearInterval(pollInterval);
                    displayResults(data);
                } else if (data.status === 'failed') {
                    clearInterval(pollInterval);
                    alert('Analysis failed: ' + (data.error || 'Unknown error'));
                    resetToUpload();
                } else if (attempts >= maxAttempts) {
                    clearInterval(pollInterval);
                    alert('Analysis timed out. Please try again.');
                    resetToUpload();
                }

            } catch (error) {
                console.error('Polling error:', error);
                clearInterval(pollInterval);
                alert('Error fetching results: ' + error.message);
                resetToUpload();
            }
        }, 2000);
    }

    /**
     * Display analysis results
     */
    function displayResults(data) {
        loadingSection.style.display = 'none';
        resultsSection.style.display = 'block';

        // Update risk score gauge
        updateRiskGauge(data.risk_score, data.category);

        // Update business details
        const business = data.business_details || {};
        document.getElementById('business-name').textContent = business.business_name || 'N/A';
        document.getElementById('abn').textContent = business.abn || 'N/A';

        // Update APRA fields
        const apra = data.apra_fields || {};
        document.getElementById('apra-classification').textContent = apra.asset_classification || 'N/A';
        document.getElementById('apra-code').textContent = apra.regulatory_code || 'N/A';
        document.getElementById('apra-provision').textContent = formatCurrency(apra.impairment_provision || 0);
        document.getElementById('apra-ltv').textContent = ((apra.loan_to_value_ratio || 0) * 100).toFixed(2) + '%';
        document.getElementById('apra-review').textContent = apra.requires_manual_review ? 'Yes ✓' : 'No';

        // Update anomalies
        displayAnomalies(data.anomalies || []);

        // Update AML alerts
        displayAMLAlerts(data.aml_alerts || []);

        // Update summary stats
        document.getElementById('total-tx').textContent = data.summary?.total_transactions || 0;
        document.getElementById('flagged-tx').textContent = data.summary?.anomaly_count || 0;
        document.getElementById('aml-items').textContent = data.summary?.aml_alert_count || 0;
        document.getElementById('overall-risk').textContent = data.category || 'Low';

        // Update report download links
        if (data.report_url) {
            document.getElementById('download-pdf').href = data.report_url;
            // For markdown, we'd need to generate separately
            // document.getElementById('download-md').href = data.report_url.replace('.pdf', '.md');
        }

        // Smooth scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * Update risk gauge visualization
     */
    function updateRiskGauge(score, category) {
        const scoreEl = document.getElementById('risk-score');
        const gaugeEl = document.getElementById('risk-gauge');
        const categoryEl = document.getElementById('risk-category');

        // Animate score counter
        animateValue(scoreEl, 0, score, 1000);

        // Rotate gauge (0-100 maps to -90deg to +90deg)
        const angle = (score / 100) * 180 - 90;
        gaugeEl.style.transform = `rotate(${angle}deg)`;

        // Set category with color
        categoryEl.textContent = category;
        categoryEl.className = 'risk-category ' + category.toLowerCase();
    }

    /**
     * Display anomalies table
     */
    function displayAnomalies(anomalies) {
        const tbody = document.getElementById('anomalies-body');
        const countEl = document.getElementById('anomaly-count');
        const noData = document.getElementById('no-anomalies');

        countEl.textContent = anomalies.length;

        if (anomalies.length === 0) {
            tbody.innerHTML = '';
            noData.style.display = 'block';
            return;
        }

        noData.style.display = 'none';
        tbody.innerHTML = anomalies.map(a => `
            <tr>
                <td>${escapeHtml(formatType(a.type))}</td>
                <td>${a.transaction_id}</td>
                <td>${escapeHtml(a.date || 'N/A')}</td>
                <td>${formatCurrency(a.amount)}</td>
                <td class="severity-${escapeHtml(a.severity)}">${escapeHtml(a.severity.toUpperCase())}</td>
                <td>${escapeHtml(a.message || '')}</td>
            </tr>
        `).join('');
    }

    /**
     * Display AML alerts
     */
    function displayAMLAlerts(alerts) {
        const container = document.getElementById('aml-alerts');
        const countEl = document.getElementById('aml-count');
        const noData = document.getElementById('no-aml');

        countEl.textContent = alerts.length;

        if (alerts.length === 0) {
            container.innerHTML = '';
            noData.style.display = 'block';
            return;
        }

        noData.style.display = 'none';
        container.innerHTML = alerts.map(alert => `
            <div class="alert ${escapeHtml(alert.severity)}">
                <div class="alert-title">
                    ${getAlertIcon(alert.type)} ${escapeHtml(formatType(alert.type))}
                </div>
                <div class="alert-message">${escapeHtml(alert.message)}</div>
            </div>
        `).join('');
    }

    /**
     * Reset to upload view
     */
    function resetToUpload() {
        loadingSection.style.display = 'none';
        resultsSection.style.display = 'none';
        uploadForm.reset();
        currentTaskId = null;
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }

    /**
     * Show loading state
     */
    function showLoading() {
        loadingSection.style.display = 'block';
        resultsSection.style.display = 'none';
        document.getElementById('progress-fill').style.width = '0%';
    }

    /**
     * Utility: Format currency
     */
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-AU', {
            style: 'currency',
            currency: 'AUD'
        }).format(amount);
    }

    /**
     * Utility: Format anomaly type
     */
    function formatType(type) {
        return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    /**
     * Utility: Get alert icon
     */
    function getAlertIcon(type) {
        const icons = {
            'high_risk_jurisdiction': '🌍',
            'watchlist_entity': '⚠️',
            'watchlist_abn': '🆔',
            'shell_company_indicator': '🏢',
            'possible_structuring': '📊',
            'suspicious_pattern': '🔍'
        };
        return icons[type] || '🚨';
    }

    /**
     * Utility: Animate number counter
     */
    function animateValue(element, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const value = Math.floor(progress * (end - start) + start);
            element.textContent = value;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }
});
