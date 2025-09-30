// Client-side JavaScript for OCR Application

document.addEventListener('DOMContentLoaded', function() {
    // File input validation
    const fileInput = document.getElementById('marksheet');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            validateFile(this);
        });
    }
    
    // Form submission loading state
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
                submitBtn.disabled = true;
            }
        });
    }
});

/**
 * Validates the uploaded file type and size
 * @param {HTMLInputElement} input - The file input element
 */
function validateFile(input) {
    const file = input.files[0];
    if (!file) return;
    
    // Check file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
    if (!allowedTypes.includes(file.type)) {
        alert('Invalid file type. Please upload JPG, JPEG, PNG, or PDF files only.');
        input.value = '';
        return;
    }
    
    // Check file size (max 10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB in bytes
    if (file.size > maxSize) {
        alert('File is too large. Maximum file size is 10MB.');
        input.value = '';
        return;
    }
    
    // Show file name in a friendly format
    const fileNameDisplay = document.createElement('div');
    fileNameDisplay.classList.add('mt-2', 'text-muted');
    fileNameDisplay.innerHTML = `<i class="bi bi-file-earmark"></i> ${file.name} (${formatFileSize(file.size)})`;
    
    // Remove previous file name display if exists
    const previousDisplay = input.parentElement.querySelector('.text-muted');
    if (previousDisplay) {
        previousDisplay.remove();
    }
    
    input.parentElement.appendChild(fileNameDisplay);
}

/**
 * Formats file size in a human-readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} - Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' bytes';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    else return (bytes / 1048576).toFixed(1) + ' MB';
}