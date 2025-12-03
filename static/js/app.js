/**
 * Main Application JavaScript
 * Modular, maintainable, and follows best practices
 */

class ERPApp {
    constructor() {
        this.sidebar = null;
        this.overlay = null;
        this.isInitialized = false;
        this.breakpoints = {
            mobile: 768,
            tablet: 1024,
            desktop: 1440
        };
        
        this.init();
    }

    /**
     * Initialize the application
     */
    init() {
        if (this.isInitialized) return;
        
        this.cacheElements();
        this.bindEvents();
        this.setupSidebar();
        this.setupAnimations();
        this.setupActiveNavigation();
        this.isInitialized = true;
        
        console.log('ERP App initialized successfully');
    }

    /**
     * Cache DOM elements for better performance
     */
    cacheElements() {
        this.sidebar = document.querySelector('.sidebar');
        this.overlay = document.querySelector('.sidebar-overlay');
        this.navLinks = document.querySelectorAll('.sidebar .nav-link');
        this.cards = document.querySelectorAll('.card');
        this.buttons = document.querySelectorAll('.btn');
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Window resize handler
        window.addEventListener('resize', this.debounce(this.handleResize.bind(this), 250));
        
        // Mobile sidebar toggle
        document.addEventListener('click', this.handleDocumentClick.bind(this));
        
        // Navigation link clicks
        this.navLinks.forEach(link => {
            link.addEventListener('click', this.handleNavClick.bind(this));
        });

        // Keyboard navigation
        document.addEventListener('keydown', this.handleKeydown.bind(this));
    }

    /**
     * Setup sidebar functionality
     */
    setupSidebar() {
        if (!this.sidebar) return;

        // Create overlay if it doesn't exist
        if (!this.overlay) {
            this.overlay = document.createElement('div');
            this.overlay.className = 'sidebar-overlay';
            this.overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 999;
                display: none;
            `;
            document.body.appendChild(this.overlay);
        }

        // Overlay click handler
        this.overlay.addEventListener('click', this.closeSidebar.bind(this));
    }

    /**
     * Setup animations for cards and elements
     */
    setupAnimations() {
        // Intersection Observer for fade-in animations
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('fade-in');
                    }
                });
            }, {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            });

            this.cards.forEach(card => {
                observer.observe(card);
            });
        }
    }

    /**
     * Setup active navigation highlighting
     */
    setupActiveNavigation() {
        const currentPath = window.location.pathname;
        
        this.navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }

    /**
     * Handle window resize
     */
    handleResize() {
        const width = window.innerWidth;
        
        if (width > this.breakpoints.mobile) {
            this.closeSidebar();
        }
    }

    /**
     * Handle document clicks for mobile sidebar
     */
    handleDocumentClick(event) {
        const isSidebarToggle = event.target.closest('[data-sidebar-toggle]');
        const isSidebar = event.target.closest('.sidebar');
        
        if (isSidebarToggle && window.innerWidth <= this.breakpoints.mobile) {
            this.toggleSidebar();
        } else if (!isSidebar && window.innerWidth <= this.breakpoints.mobile) {
            this.closeSidebar();
        }
    }

    /**
     * Handle navigation link clicks
     */
    handleNavClick(event) {
        if (window.innerWidth <= this.breakpoints.mobile) {
            this.closeSidebar();
        }
    }

    /**
     * Handle keyboard navigation
     */
    handleKeydown(event) {
        // ESC key closes sidebar
        if (event.key === 'Escape' && this.sidebar?.classList.contains('show')) {
            this.closeSidebar();
        }
    }

    /**
     * Toggle sidebar visibility
     */
    toggleSidebar() {
        if (!this.sidebar) return;
        
        this.sidebar.classList.toggle('show');
        this.overlay.style.display = this.sidebar.classList.contains('show') ? 'block' : 'none';
        document.body.style.overflow = this.sidebar.classList.contains('show') ? 'hidden' : '';
    }

    /**
     * Close sidebar
     */
    closeSidebar() {
        if (!this.sidebar) return;
        
        this.sidebar.classList.remove('show');
        this.overlay.style.display = 'none';
        document.body.style.overflow = '';
    }

    /**
     * Debounce utility function
     */
    debounce(func, wait) {
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

    /**
     * Get current breakpoint
     */
    getCurrentBreakpoint() {
        const width = window.innerWidth;
        
        if (width <= this.breakpoints.mobile) return 'mobile';
        if (width <= this.breakpoints.tablet) return 'tablet';
        if (width <= this.breakpoints.desktop) return 'desktop';
        return 'large';
    }

    /**
     * Utility method to add ripple effect to buttons
     */
    addRippleEffect(element) {
        element.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    }
}

/**
 * Language Toggle Utility
 */
class LanguageToggle {
    constructor() {
        this.currentLang = 'en';
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        const toggleBtn = document.querySelector('[data-language-toggle]');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', this.toggleLanguage.bind(this));
        }
    }

    toggleLanguage() {
        this.currentLang = this.currentLang === 'en' ? 'bn' : 'en';
        this.updateLanguage();
    }

    updateLanguage() {
        // Update text content based on language
        const elements = document.querySelectorAll('[data-lang]');
        elements.forEach(element => {
            const key = element.getAttribute('data-lang');
            element.textContent = this.getTranslation(key, this.currentLang);
        });
    }

    getTranslation(key, lang) {
        const translations = {
            'dashboard': { en: 'Dashboard', bn: 'ড্যাশবোর্ড' },
            'customers': { en: 'Customers', bn: 'গ্রাহক' },
            'suppliers': { en: 'Suppliers', bn: 'সরবরাহকারী' },
            'stock': { en: 'Stock', bn: 'স্টক' },
            'sales': { en: 'Sales', bn: 'বিক্রয়' },
            'purchases': { en: 'Purchases', bn: 'ক্রয়' },
            'reports': { en: 'Reports', bn: 'রিপোর্ট' }
        };
        
        return translations[key]?.[lang] || key;
    }
}

/**
 * Dashboard Utilities
 */
class DashboardUtils {
    static refreshDashboard() {
        // Add loading state
        const refreshBtn = document.querySelector('[onclick="refreshDashboard()"]');
        if (refreshBtn) {
            const originalText = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '<i class="bi bi-arrow-clockwise spin"></i> Refreshing...';
            refreshBtn.disabled = true;
            
            // Simulate refresh
            setTimeout(() => {
                location.reload();
            }, 1000);
        }
    }

    static exportDashboard() {
        // Implement dashboard export functionality
        console.log('Exporting dashboard data...');
        // Add export logic here
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.erpApp = new ERPApp();
    window.languageToggle = new LanguageToggle();
    
    // Add ripple effects to buttons
    document.querySelectorAll('.btn').forEach(btn => {
        window.erpApp.addRippleEffect(btn);
    });
});

// Global functions for backward compatibility
window.refreshDashboard = DashboardUtils.refreshDashboard;
window.exportDashboard = DashboardUtils.exportDashboard;
window.toggleLanguage = () => window.languageToggle.toggleLanguage();
