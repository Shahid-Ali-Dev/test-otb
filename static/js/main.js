// =========================
// CLEAN MAIN.JS - FIXED VERSION
// Works with animation system
// =========================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Shout OTB - Main.js initialized');
    
    // Initialize core functionality
    initializeNavbar();
    initializeSmoothScrolling();
    initializeFormHandling();
    
    // Check if we're on profile page and initialize profile features
    initializeProfileFeatures();
    
    // Ensure elements are visible (safe version)
    ensureElementVisibility();
});

// =========================
// NAVBAR FUNCTIONALITY
// =========================
function initializeNavbar() {
    const navbar = document.querySelector('.navbar-custom');
    if (!navbar) return;
    
    // Set initial state
    navbar.style.opacity = '1';
    navbar.style.visibility = 'visible';
    
    window.addEventListener('scroll', debounce(function() {
        if (window.scrollY > 100) {
            navbar.style.backgroundColor = 'rgba(30, 30, 30, 0.95)';
            navbar.style.backdropFilter = 'blur(10px)';
        } else {
            navbar.style.backgroundColor = '';
            navbar.style.backdropFilter = '';
        }
    }, 10));
}

// =========================
// SMOOTH SCROLLING
// =========================
function initializeSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            
            if (href !== '#' && href !== '' && href.length > 1) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

// =========================
// FORM HANDLING
// =========================
function initializeFormHandling() {
    const forms = document.querySelectorAll('form');
    if (forms.length === 0) return;
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                handleFormSubmission(submitBtn, e);
            }
        });
    });
}

function handleFormSubmission(submitBtn, e) {
    const originalHTML = submitBtn.innerHTML;
    
    // Show loading state
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Processing...';
    submitBtn.disabled = true;
    
    // In production, remove this setTimeout and handle actual form submission
    setTimeout(() => {
        submitBtn.innerHTML = originalHTML;
        submitBtn.disabled = false;
        
        // Optional: Show success message
        console.log('Form submission handled');
    }, 2000);
}

// =========================
// PROFILE PAGE FUNCTIONALITY
// =========================
function initializeProfileFeatures() {
    const profileForm = document.getElementById('profileForm');
    const profilePictureInput = document.getElementById('profile_picture');
    
    // Only initialize if we're on the profile page
    if (!profileForm || !profilePictureInput) {
        console.log('Not on profile page - skipping profile features');
        return;
    }
    
    console.log('Initializing profile page features');
    initializeImageCropping();
}

function initializeImageCropping() {
    let cropper;
    let originalImageFile;
    let croppedImageBlob = null;

    // Preview image function
    window.previewImage = function(input) {
        const file = input.files[0];
        if (file) {
            // Check file size (5MB limit)
            if (file.size > 5 * 1024 * 1024) {
                alert('File size must be less than 5MB.');
                input.value = '';
                return;
            }
            
            // Check file type
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
            if (!allowedTypes.includes(file.type)) {
                alert('Please upload a valid image file (JPEG, PNG, GIF).');
                input.value = '';
                return;
            }
            
            originalImageFile = file;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const preview = document.getElementById('imagePreview');
                if (preview) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                    const uploadPlaceholder = document.querySelector('.upload-placeholder');
                    if (uploadPlaceholder) {
                        uploadPlaceholder.style.display = 'none';
                    }
                    
                    // Open crop modal
                    openCropModal(e.target.result);
                }
            }
            reader.readAsDataURL(file);
        }
    }

    function openCropModal(imageSrc) {
        const cropImage = document.getElementById('cropImage');
        const cropOverlay = document.getElementById('cropOverlay');
        
        if (!cropImage || !cropOverlay) return;
        
        cropImage.src = imageSrc;
        cropOverlay.style.display = 'flex';
        
        // Initialize cropper
        setTimeout(() => {
            if (cropper) {
                cropper.destroy();
            }
            
            cropper = new Cropper(cropImage, {
                aspectRatio: 1,
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 0.8,
                restore: false,
                guides: true,
                center: true,
                highlight: false,
                cropBoxMovable: true,
                cropBoxResizable: true,
                toggleDragModeOnDblclick: false,
                background: false,
                modal: true,
                responsive: true
            });
        }, 100);
    }

    window.closeCrop = function() {
        const cropOverlay = document.getElementById('cropOverlay');
        if (cropOverlay) {
            cropOverlay.style.display = 'none';
        }
        
        if (cropper) {
            cropper.destroy();
            cropper = null;
        }
        
        // Don't reset file input if we have a cropped image
        if (!croppedImageBlob) {
            const fileInput = document.getElementById('profile_picture');
            const preview = document.getElementById('imagePreview');
            const uploadPlaceholder = document.querySelector('.upload-placeholder');
            
            if (fileInput) fileInput.value = '';
            if (preview) preview.style.display = 'none';
            if (uploadPlaceholder) uploadPlaceholder.style.display = 'flex';
        }
    }

    window.applyCrop = function() {
        if (cropper) {
            // Get cropped canvas
            const canvas = cropper.getCroppedCanvas({
                width: 300,
                height: 300,
                fillColor: '#fff',
                imageSmoothingEnabled: true,
                imageSmoothingQuality: 'high'
            });
            
            if (canvas) {
                // Convert canvas to blob
                canvas.toBlob(function(blob) {
                    // Store the cropped blob globally
                    croppedImageBlob = blob;
                    
                    // Create a new file from the blob
                    const croppedFile = new File([blob], `profile_${Date.now()}.jpg`, {
                        type: 'image/jpeg',
                        lastModified: Date.now()
                    });
                    
                    // Create a new DataTransfer and set the file
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(croppedFile);
                    
                    // Update the file input
                    const fileInput = document.getElementById('profile_picture');
                    if (fileInput) {
                        fileInput.files = dataTransfer.files;
                    }
                    
                    // Update preview with cropped image
                    const preview = document.getElementById('imagePreview');
                    const uploadPlaceholder = document.querySelector('.upload-placeholder');
                    
                    if (preview) {
                        preview.src = canvas.toDataURL('image/jpeg', 0.9);
                        preview.style.display = 'block';
                    }
                    if (uploadPlaceholder) {
                        uploadPlaceholder.style.display = 'none';
                    }
                    
                    // Close crop modal
                    closeCrop();
                    
                    console.log('Cropped image ready for upload:', croppedFile);
                    
                }, 'image/jpeg', 0.9);
            }
        }
    }

    // Enhanced form submission handler for profile form only
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            const fileInput = document.getElementById('profile_picture');
            
            // Check if there's a file to upload
            if (fileInput && fileInput.files.length > 0) {
                const file = fileInput.files[0];
                
                // Validate file size
                if (file.size > 5 * 1024 * 1024) {
                    e.preventDefault();
                    alert('File size must be less than 5MB.');
                    return;
                }
                
                // Validate file type
                const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
                if (!allowedTypes.includes(file.type)) {
                    e.preventDefault();
                    alert('Please upload a valid image file (JPEG, PNG, GIF).');
                    return;
                }
                
                console.log('Submitting profile form with file:', file.name, file.size, file.type);
            }
        });
    }

    // Allow re-cropping if user clicks on the preview
    const imagePreview = document.getElementById('imagePreview');
    if (imagePreview) {
        imagePreview.addEventListener('click', function() {
            if (this.style.display !== 'none') {
                const fileInput = document.getElementById('profile_picture');
                if (fileInput && fileInput.files.length > 0) {
                    const file = fileInput.files[0];
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        openCropModal(e.target.result);
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
    }

    // Keyboard shortcuts for crop modal
    document.addEventListener('keydown', function(e) {
        const cropOverlay = document.getElementById('cropOverlay');
        if (cropOverlay && cropOverlay.style.display === 'flex' && e.key === 'Escape') {
            closeCrop();
        }
    });

    // Reset croppedImageBlob when form is successfully submitted
    if (profileForm) {
        profileForm.addEventListener('submit', function() {
            croppedImageBlob = null;
        });
    }
}


/* =========================
   CUSTOM "OTHER" INPUT HANDLING
========================= */

// Contact form - Service other input
function toggleServiceOther() {
    const serviceSelect = document.getElementById('service');
    const otherContainer = document.getElementById('serviceOtherContainer');
    const otherInput = document.getElementById('service_other');
    
    if (serviceSelect.value === 'other') {
        otherContainer.style.display = 'block';
        otherInput.required = true;
    } else {
        otherContainer.style.display = 'none';
        otherInput.required = false;
        otherInput.value = '';
    }
}

// Review form - Service category other input
function toggleReviewServiceOther() {
    const categorySelect = document.getElementById('serviceCategory');
    const otherContainer = document.getElementById('reviewServiceOtherContainer');
    const otherInput = document.getElementById('service_category_other');
    
    if (categorySelect.value === 'other') {
        otherContainer.style.display = 'block';
        otherInput.required = true;
    } else {
        otherContainer.style.display = 'none';
        otherInput.required = false;
        otherInput.value = '';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize contact form "other" field
    if (document.getElementById('service')) {
        toggleServiceOther();
    }
    
    // Initialize review form "other" field
    if (document.getElementById('serviceCategory')) {
        toggleReviewServiceOther();
    }
    
    // Handle form submission to combine "other" values
    initCustomInputHandling();
});

function initCustomInputHandling() {
    // Contact form submission handling
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            const serviceSelect = document.getElementById('service');
            const serviceOther = document.getElementById('service_other');
            
            if (serviceSelect.value === 'other' && serviceOther.value.trim()) {
                // Create a hidden input to send the custom service value
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'service';
                hiddenInput.value = serviceOther.value.trim();
                contactForm.appendChild(hiddenInput);
                
                // Disable the original select to avoid conflict
                serviceSelect.disabled = true;
            }
        });
    }
    
    // Review form submission handling
    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm) {
        reviewForm.addEventListener('submit', function(e) {
            const categorySelect = document.getElementById('serviceCategory');
            const categoryOther = document.getElementById('service_category_other');
            
            if (categorySelect.value === 'other' && categoryOther.value.trim()) {
                // Create a hidden input to send the custom category value
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'service_category';
                hiddenInput.value = categoryOther.value.trim();
                reviewForm.appendChild(hiddenInput);
                
                // Disable the original select to avoid conflict
                categorySelect.disabled = true;
            }
        });
    }
}

// =========================
// VISIBILITY FIXES (SAFE)
// =========================
function ensureElementVisibility() {
    // Only fix elements that should always be visible
    const alwaysVisibleSelectors = [
        '.navbar-custom',
        '.hero-section',
        '.hero-title',
        '.hero-subtitle'
    ];
    
    alwaysVisibleSelectors.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => {
            el.style.opacity = '1';
            el.style.visibility = 'visible';
        });
    });
    
    // Ensure buttons are visible (but don't break animations)
    setTimeout(() => {
        document.querySelectorAll('.btn-custom, .btn-outline-custom').forEach(btn => {
            if (!btn.classList.contains('fade-in-element')) {
                btn.style.opacity = '1';
                btn.style.visibility = 'visible';
            }
        });
        
        // Ensure footer is visible
        const footer = document.querySelector('.footer');
        if (footer) {
            footer.style.opacity = '1';
            footer.style.visibility = 'visible';
        }
    }, 100);
}

// =========================
// UTILITY FUNCTIONS
// =========================
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// =========================
// FALLBACK FOR ANIMATIONS
// =========================
// If animations don't work, ensure elements are visible after a timeout
setTimeout(() => {
    const animatedElements = document.querySelectorAll('.fade-in-element, .service-card, .video-card');
    animatedElements.forEach(el => {
        if (el.getBoundingClientRect().top < window.innerHeight && el.style.opacity === '0') {
            el.style.opacity = '1';
            el.style.visibility = 'visible';
            el.style.transform = 'none';
        }
    });
}, 2000);

// =========================
// DEBUG HELPERS
// =========================
function debugElements() {
    console.log('=== DEBUG ELEMENT VISIBILITY ===');
    
    const checkSelectors = [
        '.btn-custom',
        '.btn-outline-custom', 
        '.footer',
        '.fade-in-element',
        '.service-card'
    ];
    
    checkSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        console.log(`${selector}: ${elements.length} elements found`);
        
        elements.forEach((el, index) => {
            const style = window.getComputedStyle(el);
            console.log(`  ${selector}[${index}]:`, {
                opacity: style.opacity,
                visibility: style.visibility,
                display: style.display,
                hasAnimated: el.classList.contains('animated')
            });
        });
    });
}


// Uncomment to debug:
// setTimeout(debugElements, 1000);

