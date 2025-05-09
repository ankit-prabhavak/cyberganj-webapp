/**
 * Password strength checker functionality for CyberGanj
 */

document.addEventListener('DOMContentLoaded', function() {
    const passwordInput = document.getElementById('password-input');
    const togglePassword = document.getElementById('toggle-password');
    const checkPasswordBtn = document.getElementById('check-password');
    const passwordResult = document.getElementById('password-result');
    const strengthText = document.getElementById('strength-text');
    const strengthBar = document.getElementById('strength-bar');
    const feedbackList = document.getElementById('feedback-list');
    
    // Only initialize if we're on the tools page with password checker
    if (!passwordInput || !checkPasswordBtn) return;
    
    // Toggle password visibility
    if (togglePassword) {
        togglePassword.addEventListener('click', function() {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            // Change the eye icon
            const icon = this.querySelector('i');
            icon.classList.toggle('fa-eye');
            icon.classList.toggle('fa-eye-slash');
        });
    }
    
    // Handle password check button click
    checkPasswordBtn.addEventListener('click', checkPasswordStrength);
    
    // Also check when user presses Enter in the input field
    passwordInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            checkPasswordStrength();
        }
    });
    
    function checkPasswordStrength() {
        const password = passwordInput.value.trim();
        
        if (!password) {
            alert('Please enter a password to check');
            return;
        }
        
        // Send to backend for analysis
        fetch('/api/check-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ password: password }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            displayPasswordResults(data);
        })
        .catch(error => {
            console.error('Error checking password:', error);
            // Fallback to client-side checking if API fails
            const fallbackResult = clientSidePasswordCheck(password);
            displayPasswordResults(fallbackResult);
        });
    }
    
    function displayPasswordResults(data) {
        // Show the results container
        passwordResult.classList.remove('hidden');
        
        // Update strength text
        strengthText.textContent = data.strength;
        
        // Update strength bar
        const scorePercentage = (data.score / 5) * 100;
        strengthBar.style.width = `${scorePercentage}%`;
        
        // Set color based on strength
        if (data.score <= 1) {
            strengthBar.style.backgroundColor = 'var(--danger-color)';
            strengthText.style.color = 'var(--danger-color)';
        } else if (data.score <= 3) {
            strengthBar.style.backgroundColor = 'var(--warning-color)';
            strengthText.style.color = 'var(--warning-color)';
        } else {
            strengthBar.style.backgroundColor = 'var(--success-color)';
            strengthText.style.color = 'var(--success-color)';
        }
        
        // Display feedback
        feedbackList.innerHTML = '';
        if (data.feedback && data.feedback.length > 0) {
            data.feedback.forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                feedbackList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'Your password meets all basic security criteria.';
            feedbackList.appendChild(li);
        }
        
        // Scroll to results if not visible
        passwordResult.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    // Fallback client-side password check in case API fails
    function clientSidePasswordCheck(password) {
        let score = 0;
        let feedback = [];
        
        // Check length
        if (password.length < 8) {
            feedback.push('Password is too short (minimum 8 characters)');
        } else if (password.length >= 12) {
            score += 1;
        }
        
        // Check for uppercase letters
        if (!/[A-Z]/.test(password)) {
            feedback.push('Add uppercase letters');
        } else {
            score += 1;
        }
        
        // Check for lowercase letters
        if (!/[a-z]/.test(password)) {
            feedback.push('Add lowercase letters');
        } else {
            score += 1;
        }
        
        // Check for numbers
        if (!/[0-9]/.test(password)) {
            feedback.push('Add numbers');
        } else {
            score += 1;
        }
        
        // Check for special characters
        if (!/[^A-Za-z0-9]/.test(password)) {
            feedback.push('Add special characters (!@#$%^&*...)');
        } else {
            score += 1;
        }
        
        // Check for common patterns
        const commonPatterns = [
            'password', '123456', 'qwerty', 'admin', 
            '111111', '12345', 'welcome', 'abc123'
        ];
        
        if (commonPatterns.some(pattern => password.toLowerCase().includes(pattern))) {
            feedback.push('Avoid common patterns in your password');
            score = Math.max(0, score - 1);
        }
        
        // Check for repetitive characters
        if (/(.)\1{2,}/.test(password)) {
            feedback.push('Avoid repeating characters (e.g., "aaa", "111")');
            score = Math.max(0, score - 1);
        }
        
        // Check for sequential characters
        const sequences = ['abcdefghijklmnopqrstuvwxyz', '0123456789'];
        
        for (const seq of sequences) {
            for (let i = 0; i < seq.length - 2; i++) {
                const fragment = seq.substring(i, i + 3);
                if (password.toLowerCase().includes(fragment)) {
                    feedback.push('Avoid sequential characters (e.g., "abc", "123")');
                    score = Math.max(0, score - 1);
                    break;
                }
            }
        }
        
        // Determine strength label
        let strength;
        if (score <= 1) {
            strength = 'Very Weak';
        } else if (score === 2) {
            strength = 'Weak';
        } else if (score === 3) {
            strength = 'Moderate';
        } else if (score === 4) {
            strength = 'Strong';
        } else {
            strength = 'Very Strong';
        }
        
        return {
            score: score,
            strength: strength,
            feedback: feedback
        };
    }
});