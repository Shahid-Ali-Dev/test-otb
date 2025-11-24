/* =========================
   ADMIN PORTFOLIO MANAGER - FIXED VERSION
========================= */
class AdminPortfolioManager {
    constructor() {
        this.currentEditingId = null;
        this.init();
    }

    init() {
        console.log('AdminPortfolioManager initialized');
        this.initEventListeners();
        this.initVideoTypeHandler();
        this.initModalHandlers();
    }

    initEventListeners() {
        // Use event delegation for dynamic buttons
        document.addEventListener('click', (e) => {
            // View buttons
            if (e.target.closest('.admin-view-btn')) {
                const btn = e.target.closest('.admin-view-btn');
                const itemId = btn.getAttribute('data-item-id');
                this.viewProject(itemId);
            }
            
            // Edit buttons
            if (e.target.closest('.admin-edit-btn')) {
                const btn = e.target.closest('.admin-edit-btn');
                const itemId = btn.getAttribute('data-item-id');
                this.editProject(itemId);
            }
            
            // Delete buttons
            if (e.target.closest('.admin-delete-btn')) {
                const btn = e.target.closest('.admin-delete-btn');
                const itemId = btn.getAttribute('data-item-id');
                this.confirmDelete(itemId);
            }
        });

        // Save project button
        document.getElementById('saveProjectBtn').addEventListener('click', () => {
            this.saveProject();
        });

        // Confirm delete button
        document.getElementById('confirmDeleteBtn').addEventListener('click', () => {
            this.deleteProject();
        });

        // Video URL input handler for automatic parsing
        document.getElementById('videoIdInput').addEventListener('input', (e) => {
            this.parseVideoUrl(e.target.value);
        });

        // Reset form when modal is hidden
        document.getElementById('addProjectModal').addEventListener('hidden.bs.modal', () => {
            this.resetForm();
        });
    }

    initVideoTypeHandler() {
        const videoTypeSelect = document.getElementById('videoTypeSelect');
        const videoIdInput = document.getElementById('videoIdInput');
        const videoIdLabel = document.getElementById('videoIdLabel');
        const videoIdHelp = document.getElementById('videoIdHelp');
        const comingSoonCheck = document.getElementById('comingSoonCheck');

        // Initial setup
        this.updateVideoFields(videoTypeSelect.value);

        videoTypeSelect.addEventListener('change', (e) => {
            this.updateVideoFields(e.target.value);
        });

        // Handle coming soon checkbox
        comingSoonCheck.addEventListener('change', (e) => {
            if (e.target.checked) {
                videoTypeSelect.value = '';
                videoTypeSelect.dispatchEvent(new Event('change'));
                videoTypeSelect.disabled = true;
                videoIdInput.value = '';
                videoIdInput.disabled = true;
            } else {
                videoTypeSelect.disabled = false;
                videoIdInput.disabled = false;
                videoTypeSelect.value = 'youtube'; // Default to YouTube
                videoTypeSelect.dispatchEvent(new Event('change'));
            }
        });
    }
    

    updateVideoFields(videoType) {
    const videoIdInput = document.getElementById('videoIdInput');
    const videoIdLabel = document.getElementById('videoIdLabel');
    const videoIdHelp = document.getElementById('videoIdHelp');

    if (videoType === 'youtube') {
        videoIdLabel.textContent = 'YouTube Video URL/ID';
        videoIdHelp.innerHTML = 'Paste any YouTube URL:<br>• youtube.com/watch?v=VIDEO_ID<br>• youtu.be/VIDEO_ID<br>• youtube.com/shorts/VIDEO_ID';
        videoIdInput.placeholder = 'e.g., https://youtube.com/watch?v=dQw4w9WgXcQ or dQw4w9WgXcQ';
        videoIdInput.style.display = 'block';
        videoIdInput.disabled = false;
    } else if (videoType === 'instagram') {
        videoIdLabel.textContent = 'Instagram Reel URL/ID';
        videoIdHelp.innerHTML = 'Paste any Instagram Reel URL:<br>• instagram.com/reel/REEL_ID<br>• instagram.com/p/POST_ID';
        videoIdInput.placeholder = 'e.g., https://instagram.com/reel/C3lWwBslWqg/ or C3lWwBslWqg';
        videoIdInput.style.display = 'block';
        videoIdInput.disabled = false;
    } else {
        videoIdLabel.textContent = 'Video ID';
        videoIdInput.style.display = 'block';
        videoIdInput.disabled = true;
        videoIdInput.value = '';
    }
}

    initModalHandlers() {
        // Enable inputs when modal is shown
        document.getElementById('addProjectModal').addEventListener('shown.bs.modal', () => {
            document.querySelectorAll('#addProjectModal input, #addProjectModal select, #addProjectModal textarea').forEach(input => {
                input.disabled = false;
            });
        });
    }

parseVideoUrl(input) {
    const videoType = document.getElementById('videoTypeSelect').value;
    
    if (!input.trim()) return input;

    let videoId = input.trim();
    let extracted = false;

    console.log('🔍 Parsing URL:', input, 'Type:', videoType);

    if (videoType === 'youtube') {
        // Handle YouTube URLs - including Shorts
        const youtubeRegexes = [
            // Standard YouTube watch URLs
            /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^"&?\/\s]{11})/,
            // YouTube Shorts URLs
            /(?:youtube\.com\/shorts\/)([^"&?\/\s]{11})/,
            // YouTube mobile URLs
            /(?:m\.youtube\.com\/watch\?v=)([^"&?\/\s]{11})/,
            // Already a valid YouTube ID (11 characters)
            /^([a-zA-Z0-9_-]{11})$/
        ];
        
        for (const regex of youtubeRegexes) {
            const match = input.match(regex);
            if (match && match[1]) {
                videoId = match[1];
                document.getElementById('videoIdInput').value = videoId;
                this.showToast('YouTube video ID extracted successfully!', 'success');
                extracted = true;
                break;
            }
        }
    } else if (videoType === 'instagram') {
        // Handle Instagram URLs - multiple formats with better regex
        const instagramRegexes = [
            // Instagram Reel URLs (various formats)
            /(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:reel|p)\/([a-zA-Z0-9_-]+)(?:\/|\?|$)/,
            // Instagram TV URLs
            /(?:https?:\/\/)?(?:www\.)?instagram\.com\/tv\/([a-zA-Z0-9_-]+)(?:\/|\?|$)/,
            // Instagram stories (optional)
            /(?:https?:\/\/)?(?:www\.)?instagram\.com\/stories\/[^\/]+\/([0-9]+)(?:\/|\?|$)/,
            // Direct Instagram ID (11-12 characters typical for Instagram)
            /^([a-zA-Z0-9_-]{11,12})$/
        ];
        
        for (const regex of instagramRegexes) {
            const match = input.match(regex);
            if (match && match[1]) {
                videoId = match[1];
                document.getElementById('videoIdInput').value = videoId;
                this.showToast('Instagram Reel ID extracted successfully!', 'success');
                extracted = true;
                break;
            }
        }
        
        // Special handling for Instagram URLs with parameters
        if (!extracted && input.includes('instagram.com')) {
            // Try to extract from any Instagram URL format
            const cleanUrl = input.split('?')[0]; // Remove query parameters
            const urlParts = cleanUrl.split('/');
            
            for (let i = 0; i < urlParts.length; i++) {
                if (urlParts[i] === 'reel' || urlParts[i] === 'p' || urlParts[i] === 'tv') {
                    if (urlParts[i + 1] && urlParts[i + 1].trim() !== '') {
                        videoId = urlParts[i + 1];
                        document.getElementById('videoIdInput').value = videoId;
                        this.showToast('Instagram Reel ID extracted successfully!', 'success');
                        extracted = true;
                        break;
                    }
                }
            }
        }
        
        // Final fallback - extract any alphanumeric string that looks like an Instagram ID
        if (!extracted && input.includes('instagram.com')) {
            const idMatch = input.match(/\/([a-zA-Z0-9_-]{11,12})(?:\/|\?|$)/);
            if (idMatch && idMatch[1]) {
                videoId = idMatch[1];
                document.getElementById('videoIdInput').value = videoId;
                this.showToast('Instagram Reel ID extracted successfully!', 'success');
                extracted = true;
            }
        }
    }

    console.log('✅ Extracted ID:', videoId, 'Extracted:', extracted);
    return videoId;
}

    async viewProject(itemId) {
        try {
            console.log('Fetching project:', itemId);
            const response = await fetch(`/admin/portfolio/item/${itemId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const project = await response.json();
            console.log('Project data:', project);
            this.showProjectDetails(project);
        } catch (error) {
            console.error('Error viewing project:', error);
            this.showToast('Error loading project details: ' + error.message, 'error');
        }
    }

    showProjectDetails(project) {
    const modalContent = document.getElementById('viewProjectContent');
    
    const tagsHtml = Array.isArray(project.tags) 
        ? project.tags.map(tag => `<span class="badge bg-orange me-1">${this.escapeHtml(tag)}</span>`).join('')
        : '';

    // Create video preview based on type
    let videoPreview = '';
    if (project.video_type && project.youtube_id) {
        if (project.video_type === 'youtube') {
            videoPreview = `
                <div class="mb-4">
                    <h6 class="text-light mb-2">YouTube Video Preview</h6>
                    <div class="ratio ratio-16x9">
                        <iframe src="https://www.youtube.com/embed/${project.youtube_id}" 
                                frameborder="0" 
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                allowfullscreen>
                        </iframe>
                    </div>
                    <div class="mt-2 text-center">
                        <small class="text-muted">Video ID: ${project.youtube_id}</small>
                    </div>
                </div>
            `;
        } else if (project.video_type === 'instagram') {
            videoPreview = `
                <div class="mb-4">
                    <h6 class="text-light mb-2">Instagram Reel Preview</h6>
                    <div class="instagram-embed-container">
                        <iframe src="https://www.instagram.com/reel/${project.youtube_id}/embed/" 
                                frameborder="0" 
                                scrolling="no"
                                allowtransparency="true"
                                allow="encrypted-media"
                                style="width: 100%; min-height: 700px; max-width: 400px; margin: 0 auto; display: block; border: none; border-radius: 12px;">
                        </iframe>
                    </div>
                    <div class="mt-2 text-center">
                        <small class="text-muted">Reel ID: ${project.youtube_id}</small>
                        <br>
                        <a href="https://instagram.com/reel/${project.youtube_id}" 
                           target="_blank" 
                           class="btn btn-sm-outline mt-2">
                            <i class="fab fa-instagram me-2"></i>Open in Instagram
                        </a>
                    </div>
                </div>
            `;
        }
    }

    modalContent.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6 class="text-light mb-2">Project Information</h6>
                <table class="table table-dark table-sm">
                    <tr>
                        <td class="border-0 text-muted" style="width: 120px;">Title:</td>
                        <td class="border-0 text-light">${this.escapeHtml(project.title)}</td>
                    </tr>
                    <tr>
                        <td class="border-0 text-muted">Description:</td>
                        <td class="border-0 text-light">${this.escapeHtml(project.description)}</td>
                    </tr>
                    <tr>
                        <td class="border-0 text-muted">Category:</td>
                        <td class="border-0 text-light">
                            <span class="badge badge-admin">${this.escapeHtml(project.category)}</span>
                        </td>
                    </tr>
                    <tr>
                        <td class="border-0 text-muted">Video Type:</td>
                        <td class="border-0 text-light">
                            <span class="badge ${project.video_type === 'instagram' ? 'badge-admin' : 'bg-orange'}">
                                ${project.video_type ? this.escapeHtml(project.video_type) : 'No Video'}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td class="border-0 text-muted">Video ID:</td>
                        <td class="border-0 text-light">
                            <code style="background: var(--secondary-black); padding: 2px 6px; border-radius: 4px;">${project.youtube_id || 'N/A'}</code>
                        </td>
                    </tr>
                    <tr>
                        <td class="border-0 text-muted">Status:</td>
                        <td class="border-0 text-light">
                            <span class="badge ${project.status === 'active' ? 'bg-success' : 'bg-warning'}">
                                ${project.status === 'active' ? 'Active' : 'Coming Soon'}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td class="border-0 text-muted">Created:</td>
                        <td class="border-0 text-light">${new Date(project.created_at).toLocaleDateString()}</td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6 class="text-light mb-2">Tags</h6>
                <div class="mb-4">
                    ${tagsHtml || '<span class="text-muted">No tags</span>'}
                </div>
                ${videoPreview || '<p class="text-muted">No video available</p>'}
            </div>
        </div>
    `;

    // Show the modal
    const viewModal = new bootstrap.Modal(document.getElementById('viewProjectModal'));
    viewModal.show();
}
    async editProject(itemId) {
        try {
            const response = await fetch(`/admin/portfolio/item/${itemId}`);
            if (!response.ok) throw new Error('Failed to fetch project details');
            
            const project = await response.json();
            this.populateEditForm(project);
        } catch (error) {
            console.error('Error editing project:', error);
            this.showToast('Error loading project for editing', 'error');
        }
    }

    populateEditForm(project) {
        this.currentEditingId = project.id;

        // Enable all inputs first
        document.querySelectorAll('#addProjectModal input, #addProjectModal select, #addProjectModal textarea').forEach(input => {
            input.disabled = false;
        });

        // Populate form fields
        document.querySelector('input[name="title"]').value = project.title;
        document.querySelector('select[name="category"]').value = project.category;
        document.querySelector('textarea[name="description"]').value = project.description;
        document.querySelector('input[name="tags"]').value = Array.isArray(project.tags) ? project.tags.join(', ') : '';
        
        // Handle video type and ID
        const videoTypeSelect = document.getElementById('videoTypeSelect');
        const videoIdInput = document.getElementById('videoIdInput');
        const comingSoonCheck = document.getElementById('comingSoonCheck');

        if (project.status === 'coming_soon') {
            comingSoonCheck.checked = true;
            videoTypeSelect.value = '';
            videoTypeSelect.disabled = true;
            videoIdInput.value = '';
            videoIdInput.disabled = true;
        } else {
            comingSoonCheck.checked = false;
            videoTypeSelect.value = project.video_type || '';
            videoTypeSelect.disabled = false;
            videoIdInput.value = project.youtube_id || '';
            videoIdInput.disabled = false;
        }

        // Trigger change event to update UI
        this.updateVideoFields(videoTypeSelect.value);

        // Update modal title and button
        document.querySelector('#addProjectModal .modal-title').innerHTML = '<i class="fas fa-edit me-2"></i>Edit Project';
        document.getElementById('saveProjectBtn').innerHTML = '<i class="fas fa-save me-1"></i>Update Project';

        // Show the modal
        const addModal = new bootstrap.Modal(document.getElementById('addProjectModal'));
        addModal.show();
    }

    async saveProject() {
        const form = document.getElementById('addProjectForm');
        const formData = new FormData(form);
        
        // Get form values
        const projectData = {
            title: formData.get('title'),
            description: formData.get('description'),
            category: formData.get('category'),
            tags: formData.get('tags') ? formData.get('tags').split(',').map(tag => tag.trim()).filter(tag => tag) : [],
            is_coming_soon: document.getElementById('comingSoonCheck').checked
        };

        // Handle video data
        const videoType = formData.get('videoType');
        let videoId = formData.get('videoId');

        if (videoId) {
            videoId = this.parseVideoUrl(videoId);
        }

        if (projectData.is_coming_soon) {
            projectData.video_type = null;
            projectData.youtube_id = null;
            projectData.status = 'coming_soon';
        } else {
            projectData.video_type = videoType;
            projectData.youtube_id = videoId;
            projectData.status = 'active';
        }

        // Validate required fields
        if (!projectData.title || !projectData.description || !projectData.category) {
            this.showToast('Please fill in all required fields', 'error');
            return;
        }

        try {
            const url = this.currentEditingId 
                ? `/admin/portfolio/edit/${this.currentEditingId}`
                : '/admin/portfolio/add';
            
            const method = this.currentEditingId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(projectData)
            });

            const result = await response.json();

            if (result.success) {
                this.showToast(result.message, 'success');
                this.resetForm();
                
                // Close modal and reload page after a short delay
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addProjectModal'));
                    modal.hide();
                    window.location.reload();
                }, 1500);
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('Error saving project:', error);
            this.showToast('Error saving project', 'error');
        }
    }

    confirmDelete(itemId) {
        this.currentEditingId = itemId;
        
        // Find the project name for confirmation
        const projectRow = document.querySelector(`.admin-delete-btn[data-item-id="${itemId}"]`).closest('tr');
        const projectName = projectRow.querySelector('strong').textContent;
        
        document.getElementById('deleteProjectName').textContent = projectName;
        
        const deleteModal = new bootstrap.Modal(document.getElementById('deleteProjectModal'));
        deleteModal.show();
    }
    

    async deleteProject() {
        if (!this.currentEditingId) return;

        try {
            const response = await fetch(`/admin/portfolio/delete/${this.currentEditingId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.success) {
                this.showToast(result.message, 'success');
                
                // Close modal and reload page after a short delay
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(document.getElementById('deleteProjectModal'));
                    modal.hide();
                    window.location.reload();
                }, 1500);
            } else {
                this.showToast(result.message, 'error');
            }
        } catch (error) {
            console.error('Error deleting project:', error);
            this.showToast('Error deleting project', 'error');
        }
    }

    resetForm() {
        const form = document.getElementById('addProjectForm');
        form.reset();
        
        // Re-enable all inputs
        document.querySelectorAll('#addProjectModal input, #addProjectModal select, #addProjectModal textarea').forEach(input => {
            input.disabled = false;
        });
        
        document.getElementById('videoTypeSelect').value = 'youtube';
        this.updateVideoFields('youtube');
        this.currentEditingId = null;
        
        // Reset modal title and button
        document.querySelector('#addProjectModal .modal-title').innerHTML = '<i class="fas fa-plus me-2"></i>Add New Project';
        document.getElementById('saveProjectBtn').innerHTML = '<i class="fas fa-save me-1"></i>Save Project';
    }

    showToast(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        const toastId = 'toast-' + Date.now();
        const bgColor = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-info';
        
        const toastHTML = `
            <div id="${toastId}" class="toast align-items-center text-white ${bgColor} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();

        // Remove toast from DOM after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
    

    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .toString()
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on admin portfolio page
    if (document.getElementById('addProjectModal')) {
        new AdminPortfolioManager();
    }

}
);
/* =========================
   ADMIN MANAGER
========================= */
class AdminManager {
    constructor() {
        this.currentSubmission = null;

        // Only activate on contact or review pages
        const currentPath = window.location.pathname;
        if (currentPath.includes("/admin/contact") || currentPath.includes("/admin/reviews")) {
            this.init();
        }
    }

    init() {
        this.initAdminTooltips();
        this.initAdminModals();
        this.initAdminTables();
    }

    initAdminTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    initAdminModals() {
        // View submission modal
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('admin-view-btn')) {
                const submissionId = e.target.getAttribute('data-submission-id');
                this.viewSubmission(submissionId);
            }
        });

        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeSubmissionModal();
            }
        });
    }

    initAdminTables() {
        // Add hover effects to admin tables
        const adminTables = document.querySelectorAll('.admin-table');
        adminTables.forEach(table => {
            table.addEventListener('mouseover', (e) => {
                if (e.target.closest('tr')) {
                    e.target.closest('tr').style.backgroundColor = 'rgba(255, 107, 53, 0.05)';
                }
            });
            
            table.addEventListener('mouseout', (e) => {
                if (e.target.closest('tr')) {
                    e.target.closest('tr').style.backgroundColor = '';
                }
            });
        });
    }

    async viewSubmission(submissionId) {
        try {
            const response = await fetch(`/admin/contact-submission/${submissionId}`);
            const data = await response.json();
            this.currentSubmission = data;
            this.openSubmissionModal(data);
        } catch (error) {
            console.error('Error fetching submission:', error);
            alert('Error loading submission details.');
        }
    }

    openSubmissionModal(data) {
        const modalContent = `
            <div class="row">
                <div class="col-md-6">
                    <h6 class="text-orange mb-2">Personal Information</h6>
                    <p><strong class="text-light">Name:</strong> <span class="text-light">${data.name}</span></p>
                    <p><strong class="text-light">Email:</strong> <a href="mailto:${data.email}" class="text-orange">${data.email}</a></p>
                    <p><strong class="text-light">Phone:</strong> <span class="text-light">${data.phone || 'Not provided'}</span></p>
                </div>
                <div class="col-md-6">
                    <h6 class="text-orange mb-2">Project Details</h6>
                    <p><strong class="text-light">Company:</strong> <span class="text-light">${data.company || 'Not provided'}</span></p>
                    <p><strong class="text-light">Service:</strong> ${data.service ? `<span class="badge badge-admin">${data.service}</span>` : '<span class="text-light">Not specified</span>'}</p>
                    <p><strong class="text-light">Budget:</strong> ${data.budget ? `<span class="badge badge-admin">${data.budget}</span>` : '<span class="text-light">Not specified</span>'}</p>
                </div>
            </div>
            <hr style="border-color: rgba(255, 255, 255, 0.1);">
            <h6 class="text-orange mb-2">Message</h6>
            <div class="rounded p-3" style="background: var(--secondary-black);">
                <p class="mb-0 text-light">${data.message || 'No message provided.'}</p>
            </div>
            <div class="mt-3 text-muted small">
                <i class="fas fa-clock me-1"></i>Submitted on ${data.submitted_at}
            </div>
        `;

        // Create or update modal
        let modal = document.getElementById('adminSubmissionModal');
        if (!modal) {
            modal = this.createAdminModal();
        }
        
        document.getElementById('adminModalContent').innerHTML = modalContent;
        new bootstrap.Modal(modal).show();
    }

    createAdminModal() {
        const modalHTML = `
            <div class="modal fade admin-modal" id="adminSubmissionModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header border-secondary">
                            <h5 class="modal-title text-orange">
                                <i class="fas fa-file-alt me-2"></i>Submission Details
                            </h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body" id="adminModalContent">
                            <!-- Content loaded dynamically -->
                        </div>
                        <div class="modal-footer border-secondary">
                            <button type="button" class="btn btn-sm-outline" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-sm-custom" onclick="adminManager.replyToSubmission()">
                                <i class="fas fa-reply me-1"></i>Reply via Email
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        return document.getElementById('adminSubmissionModal');
    }

    closeSubmissionModal() {
        const modal = document.getElementById('adminSubmissionModal');
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    }

    replyToSubmission() {
        if (this.currentSubmission) {
            const subject = encodeURIComponent(`Re: Your inquiry to Shout OTB`);
            const body = encodeURIComponent(`Hi ${this.currentSubmission.name},\n\nThank you for contacting Shout OTB. We have received your inquiry regarding "${this.currentSubmission.service || 'our services'}" and will get back to you shortly.\n\nBest regards,\nShout OTB Team`);
            window.location.href = `mailto:${this.currentSubmission.email}?subject=${subject}&body=${body}`;
        }
    }
}

// Initialize Admin Manager
let adminManager;

document.addEventListener('DOMContentLoaded', function() {
    adminManager = new AdminManager();
});

