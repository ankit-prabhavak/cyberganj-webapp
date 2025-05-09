/**
 * Main JavaScript for CyberGanj
 */

document.addEventListener('DOMContentLoaded', function() {
    // Mobile navigation toggle
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('change', function() {
            if (this.checked) {
                navMenu.classList.add('nav-open');
            } else {
                navMenu.classList.remove('nav-open');
            }
        });
        
        // Close mobile menu when clicking on a link
        const navLinks = navMenu.querySelectorAll('a');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navToggle.checked = false;
                navMenu.classList.remove('nav-open');
            });
        });
    }
    
    // Security checklist functionality
    const securityCheckboxes = document.querySelectorAll('.security-checkbox');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    
    if (securityCheckboxes.length > 0 && progressBar && progressText) {
        // Load saved checklist state from localStorage
        securityCheckboxes.forEach((checkbox, index) => {
            const isChecked = localStorage.getItem(`securityCheck_${index}`) === 'true';
            checkbox.checked = isChecked;
            
            checkbox.addEventListener('change', updateSecurityProgress);
        });
        
        updateSecurityProgress();
    }
    
    function updateSecurityProgress() {
        let checkedCount = 0;
        securityCheckboxes.forEach((checkbox, index) => {
            if (checkbox.checked) {
                checkedCount++;
                localStorage.setItem(`securityCheck_${index}`, 'true');
            } else {
                localStorage.setItem(`securityCheck_${index}`, 'false');
            }
        });
        
        const totalCount = securityCheckboxes.length;
        const progressPercentage = (checkedCount / totalCount) * 100;
        
        progressBar.style.width = `${progressPercentage}%`;
        progressText.textContent = `${checkedCount}/${totalCount} completed`;
        
        // Change progress bar color based on completion level
        if (progressPercentage < 30) {
            progressBar.style.backgroundColor = 'var(--danger-color)';
        } else if (progressPercentage < 70) {
            progressBar.style.backgroundColor = 'var(--warning-color)';
        } else {
            progressBar.style.backgroundColor = 'var(--success-color)';
        }
    }
    
    // Initialize any tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', function() {
            const tooltipText = this.getAttribute('data-tooltip');
            const tooltipElement = document.createElement('div');
            tooltipElement.className = 'tooltip';
            tooltipElement.textContent = tooltipText;
            document.body.appendChild(tooltipElement);
            
            const rect = this.getBoundingClientRect();
            tooltipElement.style.top = `${rect.top - tooltipElement.offsetHeight - 10}px`;
            tooltipElement.style.left = `${rect.left + (rect.width / 2) - (tooltipElement.offsetWidth / 2)}px`;
            tooltipElement.style.opacity = '1';
            
            this.addEventListener('mouseleave', function() {
                tooltipElement.remove();
            });
        });
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                e.preventDefault();
                window.scrollTo({
                    top: targetElement.offsetTop - 80, // Account for fixed header
                    behavior: 'smooth'
                });
            }
        });
    });
});