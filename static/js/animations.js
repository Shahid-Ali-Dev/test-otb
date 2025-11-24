/* =========================
   ANIMATIONS.JS - OPTIMIZED & CLEANED
   All functionality preserved, better organization
========================= */

/* =========================
   PORTFOLIO MANAGER - FIXED VERSION
========================= */

class PortfolioManager {
    constructor() {
        if (PortfolioManager.instance) {
            return PortfolioManager.instance;
        }
        PortfolioManager.instance = this;
        
        this.currentFilter = 'all';
        this.visibleItems = 6;
        this.allItems = [];
        this.initialized = false;
        this.init();
    }

    init() {
        if (this.initialized) {
            console.log('PortfolioManager already initialized');
            return;
        }

        // Wait a bit for the data to be available
        setTimeout(() => {
            this.allItems = window.portfolioItems || [];
            console.log('Portfolio items loaded:', this.allItems.length);
            
            // Remove duplicates based on ID
            this.allItems = this.removeDuplicates(this.allItems);
            console.log('After removing duplicates:', this.allItems.length);
            
            this.renderPortfolio();
            this.initFilters();
            this.initLoadMore();
            this.initVideoModal();
            this.updateLoadMoreButton();
            this.initialized = true;
        }, 100);
    }

    removeDuplicates(items) {
        const seen = new Set();
        return items.filter(item => {
            const duplicate = seen.has(item.id);
            seen.add(item.id);
            return !duplicate;
        });
    }

    renderPortfolio() {
        const grid = document.getElementById('portfolioGrid');
        const filteredItems = this.getFilteredItems();
        const itemsToShow = filteredItems.slice(0, this.visibleItems);
        
        console.log('Rendering portfolio:', {
            totalItems: this.allItems.length,
            filteredItems: filteredItems.length,
            showing: itemsToShow.length,
            visibleItems: this.visibleItems
        });
        
        if (grid) {
            grid.innerHTML = itemsToShow.map((item, index) => 
                this.createPortfolioCard(item, index)
            ).join('');
        }
        
        this.updateLoadMoreButton();
        this.initItemAnimations();
    }

    loadMoreProjects() {
        const grid = document.getElementById('portfolioGrid');
        const filteredItems = this.getFilteredItems();
        
        console.log('Load more clicked:', {
            currentVisible: this.visibleItems,
            totalFiltered: filteredItems.length,
            canLoadMore: this.visibleItems < filteredItems.length
        });
        
        if (grid && this.visibleItems < filteredItems.length) {
            const newItems = filteredItems.slice(this.visibleItems, this.visibleItems + 3);
            
            console.log('Loading new items:', newItems.length, newItems.map(item => item.id));
            
            newItems.forEach((item, index) => {
                const cardHTML = this.createPortfolioCard(item, this.visibleItems + index);
                grid.insertAdjacentHTML('beforeend', cardHTML);
            });
            
            this.visibleItems += 3;
            this.updateLoadMoreButton();
            this.initItemAnimations();
        } else {
            console.log('No more items to load');
        }
    }

    createPortfolioCard(item, index) {
        // Fix delay calculation - use proper sequence
        const delayIndex = (index % 6) + 1;
        const delayClass = `delay-${delayIndex}`;
        const isComingSoon = item.status === 'coming_soon';
        const videoId = item.video_id || item.youtube_id;
        const videoType = item.videoType || item.video_type;
        
        // Ensure tags is an array
        const tags = Array.isArray(item.tags) ? item.tags : [];
        
        return `
            <div class="video-card fade-in-element ${delayClass}" data-category="${item.category}" data-id="${item.id}">
                <div class="video-container">
                    ${isComingSoon ? this.createComingSoonThumbnail() : this.createVideoThumbnail(item, videoId, videoType)}
                </div>
                <div class="video-content">
                    <h5 class="mb-2">${this.escapeHtml(item.title)}</h5>
                    <p class="text-muted mb-3">${this.escapeHtml(item.description)}</p>
                    <div class="d-flex flex-wrap gap-2 mb-3">
                        ${tags.map(tag => `<span class="badge bg-orange">${this.escapeHtml(tag)}</span>`).join('')}
                    </div>
                    <div class="video-actions">
                        ${isComingSoon ? 
                            '<button class="btn btn-outline-custom btn-fixed" disabled>Coming Soon</button>' : 
                            `<button class="btn btn-outline-custom btn-fixed watch-video-btn" data-video-id="${videoId}" data-video-type="${videoType}">Watch Video</button>`
                        }
                    </div>
                </div>
            </div>
        `;
    }

    createVideoThumbnail(item, videoId, videoType) {
        if (!videoId) {
            return this.createComingSoonThumbnail();
        }

        if (videoType === 'instagram') {
            return `
                <div class="instagram-thumbnail" data-video-id="${videoId}" data-video-type="${videoType}">
                    <div class="instagram-thumbnail-background">
                        <div class="instagram-branding">
                            <i class="fab fa-instagram"></i>
                            <span>Instagram Reel</span>
                        </div>
                        <div class="video-preview-content">
                            <h6>${this.escapeHtml(item.title)}</h6>
                            <p>Click to watch preview</p>
                        </div>
                    </div>
                    <div class="play-button-overlay">
                        <i class="fas fa-play"></i>
                    </div>
                </div>
            `;
        } else {
            return `
                <div class="video-thumbnail" data-video-id="${videoId}" data-video-type="${videoType}">
                    <img src="https://img.youtube.com/vi/${videoId}/maxresdefault.jpg" 
                         alt="${this.escapeHtml(item.title)}" 
                         class="thumbnail-img"
                         onerror="this.src='https://img.youtube.com/vi/${videoId}/hqdefault.jpg'">
                    <div class="play-button-overlay">
                        <i class="fas fa-play"></i>
                    </div>
                </div>
            `;
        }
    }

    createComingSoonThumbnail() {
        return `
            <div class="coming-soon-thumbnail">
                <div class="coming-soon-content">
                    <i class="fas fa-clock coming-soon-icon"></i>
                    <h6>Coming Soon</h6>
                    <p>Exciting project in progress</p>
                </div>
            </div>
        `;
    }

    getFilteredItems() {
        if (this.currentFilter === 'all') {
            return this.allItems;
        }
        return this.allItems.filter(item => item.category === this.currentFilter);
    }

    initFilters() {
        const filterButtons = document.querySelectorAll('.btn-group .btn-outline-custom');
        
        filterButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                filterButtons.forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                this.currentFilter = e.target.getAttribute('data-filter');
                this.visibleItems = 6;
                this.renderPortfolio();
            });
        });
    }

    initLoadMore() {
        const loadMoreBtn = document.getElementById('loadMore');
        
        if (loadMoreBtn) {
            // Remove any existing event listeners
            loadMoreBtn.replaceWith(loadMoreBtn.cloneNode(true));
            const newLoadMoreBtn = document.getElementById('loadMore');
            
            newLoadMoreBtn.addEventListener('click', () => {
                this.loadMoreProjects();
            });
        }
    }

    updateLoadMoreButton() {
        const loadMoreBtn = document.getElementById('loadMore');
        if (loadMoreBtn) {
            const filteredItems = this.getFilteredItems();
            const shouldShow = this.visibleItems < filteredItems.length;
            
            console.log('Update load more button:', {
                visibleItems: this.visibleItems,
                filteredItems: filteredItems.length,
                shouldShow: shouldShow
            });
            
            loadMoreBtn.style.display = shouldShow ? 'block' : 'none';
            
            loadMoreBtn.innerHTML = shouldShow ? 
                '<i class="fas fa-plus me-2"></i>Load More Projects' : 
                '<i class="fas fa-check me-2"></i>All Projects Loaded';
        }
    }

    initItemAnimations() {
        const scrollElements = document.querySelectorAll('.video-card.fade-in-element');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animated');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        scrollElements.forEach(el => observer.observe(el));
    }
    

    initVideoModal() {
    const modal = document.getElementById('videoModal');
    const modalContainer = document.getElementById('modalVideoContainer');
    const closeBtn = document.querySelector('.close-modal');

    // Function to open video modal
    const openVideoModal = (videoId, videoType) => {
        if (!videoId || videoId === 'null') {
            alert('Video coming soon!');
            return;
        }

        let embedHtml = '';
        
        if (videoType === 'instagram') {
            // Instagram embed - vertical format
            embedHtml = `
                <div class="instagram-embed-container">
                    <iframe src="https://www.instagram.com/reel/${videoId}/embed/" 
                            class="instagram-embed"
                            frameborder="0" 
                            scrolling="no"
                            allowtransparency="true"
                            allow="encrypted-media"
                            style="width: 100%; min-height: 700px; max-width: 400px; margin: 0 auto; display: block; border: none; border-radius: 12px;">
                    </iframe>
                </div>
            `;
        } else {
            // YouTube embed - maintain 16:9 aspect ratio
            embedHtml = `
                <div class="youtube-embed-container">
                    <iframe src="https://www.youtube.com/embed/${videoId}?autoplay=1" 
                            frameborder="0" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                            allowfullscreen
                            style="width: 100%; height: 70vh; max-width: 1200px; border: none; border-radius: 12px;">
                    </iframe>
                </div>
            `;
        }

        if (modalContainer) {
            modalContainer.innerHTML = embedHtml;
        }
        if (modal) {
            modal.style.display = 'flex';
        }
        
        // Ensure close button is visible and functional
        if (closeBtn) {
            closeBtn.style.display = 'block';
            closeBtn.style.zIndex = '10000';
        }
        
        document.body.style.overflow = 'hidden';
    };

    // Function to close video modal
    const closeVideoModal = () => {
        if (modal) {
            modal.style.display = 'none';
        }
        if (modalContainer) {
            modalContainer.innerHTML = '';
        }
        document.body.style.overflow = 'auto';
    };

    // Event listeners for video clicks
    document.addEventListener('click', (e) => {
        // Click on video thumbnails
        if (e.target.closest('.video-thumbnail, .instagram-thumbnail')) {
            const thumbnail = e.target.closest('.video-thumbnail, .instagram-thumbnail');
            const videoId = thumbnail.getAttribute('data-video-id');
            const videoType = thumbnail.getAttribute('data-video-type');
            openVideoModal(videoId, videoType);
        }
        
        // Click on watch video buttons
        if (e.target.closest('.watch-video-btn')) {
            const button = e.target.closest('.watch-video-btn');
            const videoId = button.getAttribute('data-video-id');
            const videoType = button.getAttribute('data-video-type');
            openVideoModal(videoId, videoType);
        }
    });

    // Close modal events
    if (closeBtn) {
        closeBtn.addEventListener('click', closeVideoModal);
    }
    
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeVideoModal();
        });
    }
    
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeVideoModal();
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

/* =========================
   SCROLL ANIMATOR
========================= */
class ScrollAnimator {
    constructor() {
        this.observerOptions = {
            threshold: 0.3,
            rootMargin: '0px 0px -10% 0px'
        };
        this.init();
    }

    init() {
        this.initScrollAnimations();
        this.initHoverEffects();
        this.initNavigation();
        this.initPortfolioAnimations();
    }

    initScrollAnimations() {
    // Don't apply scroll animations on admin pages
    if (window.location.pathname.includes('/admin/')) {
        console.log('Admin page detected - skipping scroll animations');
        // Instead, apply immediate fade-in for admin pages
        document.querySelectorAll('.fade-in-element').forEach(el => {
            el.classList.add('animated');
        });
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, this.observerOptions);

    const scrollElements = [
        '.fade-in-element',
        '.service-card',
        '.quote-box',
        '.video-card',
        '.contact-form-card',
        '.contact-info-card',
        '.quick-contact-card',
        '.map-container',
        '.testimonial-card',
        '.case-study-card',
        '.stat-item',
        '.feature-icon',
        '.footer',
        '.btn-outline-custom',
        '.scroll-animate',
        '.scroll-animate-fade-up',
        '.scroll-animate-fade-left',
        '.scroll-animate-fade-right',
        '.scroll-animate-scale',
        '.scroll-animate-flip'
    ];

    scrollElements.forEach(selector => {
        document.querySelectorAll(selector).forEach(el => observer.observe(el));
    });
}

    initHoverEffects() {
        // Service cards
        document.querySelectorAll('.service-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-10px) scale(1.05)';
                card.style.boxShadow = '0 25px 50px rgba(255, 107, 53, 0.3)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
                card.style.boxShadow = '';
            });
        });

        // Magnetic buttons
        document.querySelectorAll('.btn-magnetic').forEach(btn => {
            btn.addEventListener('mouseenter', () => btn.style.transform = 'translateY(-3px) scale(1.05)');
            btn.addEventListener('mouseleave', () => btn.style.transform = 'translateY(0) scale(1)');
        });

        // Navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('mouseenter', () => link.style.transform = 'translateY(-2px)');
            link.addEventListener('mouseleave', () => link.style.transform = 'translateY(0)');
        });
    }

    initNavigation() {
        // Smooth scrolling
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const href = anchor.getAttribute('href');
                // Check if the href is just '#' and skip if it is
                if (href === '#') {
                    return;
                }
                const target = document.querySelector(href);
                target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
            });
        });

        // Navbar scroll effect
        const navbar = document.querySelector('.navbar-custom');
        if (navbar) {
            window.addEventListener('scroll', () => {
                if (window.scrollY > 100) {
                    navbar.style.backgroundColor = 'rgba(30, 30, 30, 0.95)';
                    navbar.style.backdropFilter = 'blur(10px)';
                } else {
                    navbar.style.backgroundColor = '';
                    navbar.style.backdropFilter = '';
                }
            });
        }
    }

    initPortfolioAnimations() {
        // Initialize Portfolio Manager if we're on portfolio page - ONLY ONCE
        if (document.getElementById('portfolioGrid') && window.portfolioItems && !window.portfolioManagerInitialized) {
            new PortfolioManager();
            window.portfolioManagerInitialized = true;
        }

        const filterButtons = document.querySelectorAll('.btn-outline-custom.fade-in-element');
        const videoCards = document.querySelectorAll('.video-card.fade-in-element');
        
        const portfolioObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const delay = this.getDelayFromClass(entry.target);
                    setTimeout(() => {
                        entry.target.classList.add('animated');
                        portfolioObserver.unobserve(entry.target);
                    }, delay);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
        
        [...filterButtons, ...videoCards].forEach(el => portfolioObserver.observe(el));

        // Stats counter
        const statItems = document.querySelectorAll('.stat-item h2');
        const statsObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.animateCounter(entry.target);
                    statsObserver.unobserve(entry.target);
                }
            });
        }, { threshold: 0.5 });
        
        statItems.forEach(stat => statsObserver.observe(stat));
    }

    getDelayFromClass(element) {
        const delays = {
            'delay-1': 100,
            'delay-2': 200,
            'delay-3': 300,
            'delay-4': 400,
            'delay-5': 500
        };
        
        for (const [className, delay] of Object.entries(delays)) {
            if (element.classList.contains(className)) return delay;
        }
        return 0;
    }

    animateCounter(counter) {
        const target = parseInt(counter.getAttribute('data-count'));
        const duration = 2000;
        const step = target / (duration / 16);
        let current = 0;
        
        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                counter.textContent = target + '+';
                clearInterval(timer);
            } else {
                counter.textContent = Math.floor(current);
            }
        }, 16);
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new ScrollAnimator();
    
    // Initialize Portfolio Manager separately if needed
    if (document.getElementById('portfolioGrid') && window.portfolioItems) {
        new PortfolioManager();
    }
});

/* =========================
   UTILITY FUNCTIONS
========================= */

// Counter animations
function initCounterAnimations() {
    const statItems = document.querySelectorAll('.stat-item h2');
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.getAttribute('data-count'));
                const duration = 2000;
                const step = target / (duration / 16);
                let current = 0;
                
                const timer = setInterval(() => {
                    current += step;
                    if (current >= target) {
                        counter.textContent = target + '+';
                        clearInterval(timer);
                    } else {
                        counter.textContent = Math.floor(current);
                    }
                }, 16);
                
                statsObserver.unobserve(counter);
            }
        });
    }, { threshold: 0.5 });
    
    statItems.forEach(stat => statsObserver.observe(stat));
}

// Form animations
function initFormAnimations() {
    document.querySelectorAll('.form-control').forEach(input => {
        input.addEventListener('focus', () => input.parentElement.classList.add('focused'));
        input.addEventListener('blur', () => {
            if (!input.value) input.parentElement.classList.remove('focused');
        });
    });
}

// Scroll progress indicator
function initScrollProgress() {
    const progressBar = document.createElement('div');
    progressBar.className = 'scroll-progress';
    document.body.appendChild(progressBar);

    window.addEventListener('scroll', () => {
        const windowHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
        const scrolled = (window.pageYOffset / windowHeight) * 100;
        progressBar.style.width = scrolled + '%';
    });
}

// Quick Contact Widget
function initQuickContactWidget() {
    const quickContactBtn = document.getElementById('quickContactBtn');
    const contactOptions = document.getElementById('contactOptions');
    let isOpen = false;

    quickContactBtn?.addEventListener('click', function() {
        isOpen = !isOpen;
        quickContactBtn.classList.toggle('active', isOpen);
        contactOptions.classList.toggle('active', isOpen);
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (isOpen && !e.target.closest('.quick-contact-widget')) {
            isOpen = false;
            quickContactBtn.classList.remove('active');
            contactOptions.classList.remove('active');
        }
    });

    // Close on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && isOpen) {
            isOpen = false;
            quickContactBtn.classList.remove('active');
            contactOptions.classList.remove('active');
        }
    });
}

/* =========================
   INITIALIZATION
========================= */

// Main initialization
document.addEventListener('DOMContentLoaded', function() {
    new ScrollAnimator();
    new PortfolioManager();
    
    initFormAnimations();
    initScrollProgress();
    initCounterAnimations();
    initQuickContactWidget();
});

// Fallback for older browsers
if (!('IntersectionObserver' in window)) {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(() => {
            document.querySelectorAll('.fade-in-element, .service-card, .video-card').forEach(el => {
                el.classList.add('animated');
            });
        }, 500);
    });
}
// Force initialization after DOM load
setTimeout(() => {
    initQuickContactWidget();
}, 1000);

// Reviews Carousel Functionality
document.addEventListener('DOMContentLoaded', function() {
    const reviewsTrack = document.getElementById('reviewsTrack');
    const reviewCards = document.querySelectorAll('.review-card');
    
    if (reviewsTrack && reviewCards.length > 0) {
        // Clone cards for seamless infinite scroll
        const cardsToClone = Array.from(reviewCards).slice(0, 3);
        cardsToClone.forEach(card => {
            const clone = card.cloneNode(true);
            reviewsTrack.appendChild(clone);
        });

        // Star rating system
        const ratingStars = document.querySelectorAll('.rating-star');
        const selectedRating = document.getElementById('selectedRating');
        
        if (ratingStars) {
            ratingStars.forEach(star => {
                star.addEventListener('click', function() {
                    const rating = this.getAttribute('data-rating');
                    selectedRating.value = rating;
                    
                    // Update star display
                    ratingStars.forEach(s => {
                        if (s.getAttribute('data-rating') <= rating) {
                            s.classList.add('active');
                        } else {
                            s.classList.remove('active');
                        }
                    });
                });
            });
        }

        // Pause auto-scroll on hover
        reviewsTrack.addEventListener('mouseenter', function() {
            this.style.animationPlayState = 'paused';
        });

        reviewsTrack.addEventListener('mouseleave', function() {
            this.style.animationPlayState = 'running';
        });

        // Reset animation when it completes for infinite loop
        reviewsTrack.addEventListener('animationiteration', function() {
            // Smooth reset without jump
            this.style.animation = 'none';
            setTimeout(() => {
                this.style.animation = '';
            }, 10);
        });
    }
});
// Service video handling
document.addEventListener('DOMContentLoaded', function() {
    const serviceVideos = document.querySelectorAll('.service-animation-video');
    
    serviceVideos.forEach(video => {
        // Ensure video plays and loops properly
        video.addEventListener('loadeddata', function() {
            console.log('Service animation video loaded');
        });
        
        video.addEventListener('error', function() {
            console.error('Error loading service animation video');
        });
        
        // Optional: Add play/pause on hover
        video.addEventListener('mouseenter', function() {
            // video.play(); // Uncomment if you want hover play
        });
        
        video.addEventListener('mouseleave', function() {
            // video.pause(); // Uncomment if you want hover pause
            // video.currentTime = 0; // Reset to start
        });
    });
});
