/**
 * HMS Enterprise JavaScript
 * Main application functionality
 */

(function() {
    'use strict';

    // DOM Elements
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const menuToggle = document.getElementById('menuToggle');
    const themeToggle = document.getElementById('themeToggle');
    
    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        initSidebar();
        initTheme();
        initAlerts();
        initModals();
        initTooltips();
        initFormValidation();
    });

    /**
     * Sidebar Toggle Functionality
     */
    function initSidebar() {
        if (!sidebar || (!sidebarToggle && !menuToggle)) return;

        const toggleSidebar = () => {
            if (window.innerWidth <= 768) {
                sidebar.classList.toggle('active');
            } else {
                // For desktop, we could implement collapsed state
                document.body.classList.toggle('sidebar-collapsed');
            }
        };

        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', toggleSidebar);
        }

        if (menuToggle) {
            menuToggle.addEventListener('click', toggleSidebar);
        }

        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            if (window.innerWidth <= 768 && 
                sidebar && 
                sidebar.classList.contains('active') &&
                !sidebar.contains(event.target) &&
                !menuToggle.contains(event.target)) {
                sidebar.classList.remove('active');
            }
        });
    }

    /**
     * Theme Toggle (Light/Dark Mode)
     */
    function initTheme() {
        if (!themeToggle) return;

        // Check for saved theme preference or default to light
        const savedTheme = localStorage.getItem('hms-theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);

        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('hms-theme', newTheme);
            
            // Dispatch custom event for other components to react
            window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: newTheme } }));
        });
    }

    /**
     * Alert Dismissal
     */
    function initAlerts() {
        const alertDismissButtons = document.querySelectorAll('[data-dismiss="alert"]');
        
        alertDismissButtons.forEach(function(button) {
            button.addEventListener('click', function() {
                const alert = button.closest('.alert');
                if (alert) {
                    alert.classList.add('fade');
                    setTimeout(() => {
                        alert.remove();
                    }, 150);
                }
            });
        });

        // Auto-dismiss success alerts after 5 seconds
        const autoDismissAlerts = document.querySelectorAll('.alert-success.alert-dismissible');
        autoDismissAlerts.forEach(function(alert) {
            setTimeout(() => {
                alert.classList.add('fade');
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.remove();
                    }
                }, 150);
            }, 5000);
        });
    }

    /**
     * Modal Functionality
     */
    function initModals() {
        const modalTriggers = document.querySelectorAll('[data-toggle="modal"]');
        
        modalTriggers.forEach(function(trigger) {
            trigger.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                const modal = document.querySelector(targetId);
                
                if (modal) {
                    showModal(modal);
                }
            });
        });

        // Close modal on backdrop click
        document.querySelectorAll('.modal-backdrop').forEach(function(backdrop) {
            backdrop.addEventListener('click', function() {
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    hideModal(modal);
                }
            });
        });

        // Close modal on escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    hideModal(modal);
                }
            }
        });
    }

    /**
     * Show Modal
     */
    function showModal(modal) {
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop show';
        document.body.appendChild(backdrop);
        
        modal.classList.add('show');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('role', 'dialog');
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        
        // Focus first focusable element
        const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (firstFocusable) {
            firstFocusable.focus();
        }
    }

    /**
     * Hide Modal
     */
    function hideModal(modal) {
        modal.classList.remove('show');
        modal.removeAttribute('aria-modal');
        modal.removeAttribute('role');
        
        const backdrop = document.querySelector('.modal-backdrop.show');
        if (backdrop) {
            backdrop.remove();
        }
        
        // Restore body scroll
        document.body.style.overflow = '';
    }

    /**
     * Tooltips (Simple Implementation)
     */
    function initTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(function(element) {
            element.addEventListener('mouseenter', function() {
                const tooltipText = this.getAttribute('data-tooltip');
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = tooltipText;
                
                // Position tooltip
                const rect = this.getBoundingClientRect();
                tooltip.style.position = 'absolute';
                tooltip.style.top = `${rect.top - 30}px`;
                tooltip.style.left = `${rect.left + (rect.width / 2)}px`;
                tooltip.style.transform = 'translateX(-50%)';
                
                document.body.appendChild(tooltip);
                
                this._tooltip = tooltip;
            });
            
            element.addEventListener('mouseleave', function() {
                if (this._tooltip) {
                    this._tooltip.remove();
                    this._tooltip = null;
                }
            });
        });
    }

    /**
     * Form Validation
     */
    function initFormValidation() {
        const forms = document.querySelectorAll('form.needs-validation');
        
        forms.forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                
                form.classList.add('was-validated');
            });
        });
    }

    /**
     * CSRF Token Helper for AJAX
     */
    function getCSRFToken() {
        const metaTag = document.querySelector('meta[name="csrf-token"]');
        return metaTag ? metaTag.getAttribute('content') : '';
    }

    // Expose utilities globally
    window.HMS = {
        showModal: showModal,
        hideModal: hideModal,
        getCSRFToken: getCSRFToken,
        
        /**
         * Show Toast Notification
         */
        showToast: function(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `alert alert-${type} fade show`;
            toast.style.position = 'fixed';
            toast.style.bottom = '20px';
            toast.style.right = '20px';
            toast.style.zIndex = '9999';
            toast.style.minWidth = '300px';
            toast.textContent = message;
            
            document.body.appendChild(toast);
            
            setTimeout(() => {
                toast.classList.add('fade');
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, 150);
            }, 3000);
        },
        
        /**
         * Confirm Action Dialog
         */
        confirm: function(message) {
            return new Promise((resolve) => {
                if (window.confirm(message)) {
                    resolve(true);
                } else {
                    resolve(false);
                }
            });
        }
    };

})();
