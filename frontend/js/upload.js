// Upload functionality for receipt processing
// Session check for upload page
fetch('/api/auth/current', { credentials: 'include' })
    .then(res => res.json())
    .then(data => {
        if (!data.user) {
            window.location.href = 'login.html';
        }
    })
    .catch(() => {
        window.location.href = 'login.html';
    });
let selectedFile = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeUpload();
});

function initializeUpload() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const ocrText = document.getElementById('ocrText');
    const uploadBtn = document.getElementById('uploadBtn');

    // Click to select file
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener('change', handleFileSelect);

    // Drag and drop functionality
    dropZone.addEventListener('dragover', handleDragOver);
    dropZone.addEventListener('dragleave', handleDragLeave);
    dropZone.addEventListener('drop', handleDrop);

    // Enable upload button when file or text is provided
    fileInput.addEventListener('change', updateUploadButton);
    ocrText.addEventListener('input', updateUploadButton);

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDragOver(e) {
    document.getElementById('dropZone').classList.add('drag-over');
}

function handleDragLeave(e) {
    document.getElementById('dropZone').classList.remove('drag-over');
}

function handleDrop(e) {
    document.getElementById('dropZone').classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect({ target: { files: files } });
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
        showError('Please select a valid image file (JPG, PNG) or PDF.');
        return;
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
        showError('File size must be less than 10MB.');
        return;
    }

    selectedFile = file;
    updateDropZoneDisplay();
    updateUploadButton();
}

function updateDropZoneDisplay() {
    const dropZone = document.getElementById('dropZone');
    if (selectedFile) {
        dropZone.innerHTML = `
            <span class="material-symbols-outlined text-4xl text-green-500 mb-4 block">check_circle</span>
            <p class="text-lg text-green-600 mb-2">File Selected: ${selectedFile.name}</p>
            <p class="text-sm text-gray-500 mb-4">Size: ${formatFileSize(selectedFile.size)}</p>
            <p class="text-xs text-gray-400">Click to select a different file</p>
        `;
    }
}

function updateUploadButton() {
    const uploadBtn = document.getElementById('uploadBtn');
    const ocrText = document.getElementById('ocrText').value.trim();
    
    const hasFile = selectedFile !== null;
    const hasText = ocrText.length > 0;
    
    uploadBtn.disabled = !(hasFile || hasText);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function processReceipt() {
    const ocrText = document.getElementById('ocrText').value.trim();
    
    if (!selectedFile && !ocrText) {
        showError('Please select a file or enter receipt text.');
        return;
    }

    // Show processing status
    showProcessingStatus(true);
    document.getElementById('uploadBtn').disabled = true;
    document.getElementById('errorContainer').innerHTML = '';

    try {
        let fileBase64 = '';
        let filename = 'receipt.txt';

        // Convert file to base64 if file is selected
        if (selectedFile) {
            fileBase64 = await fileToBase64(selectedFile);
            filename = selectedFile.name;
        }

        // Prepare request data
        const requestData = {
            file_base64: fileBase64,
            filename: filename,
            ocr_text: ocrText || 'Manual text input'
        };

        // Call the classify API
        const result = await API.apiCall('classify', {
            method: 'POST',
            body: JSON.stringify(requestData)
        });

        // Show results
        displayResults(result);

    } catch (error) {
        console.error('Upload error:', error);
        showError(`Failed to process receipt: ${error.message}`);
    } finally {
        showProcessingStatus(false);
        document.getElementById('uploadBtn').disabled = false;
    }
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = () => {
            // Remove the data:image/jpeg;base64, prefix
            const base64 = reader.result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = error => reject(error);
    });
}

function showProcessingStatus(show) {
    const statusElement = document.getElementById('processingStatus');
    if (show) {
        statusElement.classList.remove('hidden');
    } else {
        statusElement.classList.add('hidden');
    }
}

function displayResults(result) {
    const resultsSection = document.getElementById('resultsSection');
    
    // Update result fields
    document.getElementById('resultVendor').textContent = result.vendor || 'Unknown';
    document.getElementById('resultAmount').textContent = 
        result.currency ? `${result.currency} ${result.total_amount || 0}` : (result.total_amount || 0);
    document.getElementById('resultDate').textContent = result.invoice_date || 'Unknown';
    document.getElementById('resultCategory').textContent = result.category || 'Others';
    document.getElementById('resultTransactionId').textContent = 
        result.transaction_id ? result.transaction_id.substring(0, 8) + '...' : 'N/A';
    document.getElementById('resultDocumentId').textContent = 
        result.document_id ? result.document_id.substring(0, 8) + '...' : 'N/A';
    document.getElementById('resultCurrency').textContent = result.currency || 'N/A';
    
    // Show results section
    resultsSection.classList.remove('hidden');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function resetUpload() {
    // Reset file selection
    selectedFile = null;
    document.getElementById('fileInput').value = '';
    document.getElementById('ocrText').value = '';
    
    // Reset drop zone display
    const dropZone = document.getElementById('dropZone');
    dropZone.innerHTML = `
        <span class="material-symbols-outlined text-4xl text-gray-400 mb-4 block">cloud_upload</span>
        <p class="text-lg text-gray-600 mb-2">Drag & drop your receipt here</p>
        <p class="text-sm text-gray-500 mb-4">or click to select file</p>
        <p class="text-xs text-gray-400">Supports: JPG, PNG, PDF (Max 10MB)</p>
    `;
    
    // Hide results and reset UI
    document.getElementById('resultsSection').classList.add('hidden');
    document.getElementById('errorContainer').innerHTML = '';
    
    // Update button state
    updateUploadButton();
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}