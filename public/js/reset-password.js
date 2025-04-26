document.addEventListener('DOMContentLoaded', function() {
    // Constants
    const API_ENDPOINT = 'https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/auth/resetpwd';
    
    // Elements
    const resetForm = document.getElementById('resetForm');
    const sendCodeBtn = document.getElementById('sendCodeBtn');
    const resetPasswordBtn = document.getElementById('resetPasswordBtn');
    const emailInput = document.getElementById('email');
    const codeInput = document.getElementById('code');
    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    
    // Error elements
    const emailError = document.getElementById('emailError');
    const codeError = document.getElementById('codeError');
    const passwordError = document.getElementById('passwordError');
    const confirmError = document.getElementById('confirmError');

    // Helper functions
    function showError(element, message) {
        element.textContent = message;
        element.style.display = 'block';
    }

    function clearErrors() {
        [emailError, codeError, passwordError, confirmError].forEach(error => {
            error.textContent = '';
            error.style.display = 'none';
        });
    }

    function setLoading(button, isLoading) {
        button.disabled = isLoading;
        button.textContent = isLoading ? 'Loading...' : button.getAttribute('data-original-text');
    }

    // Save original button text
    sendCodeBtn.setAttribute('data-original-text', sendCodeBtn.textContent);
    resetPasswordBtn.setAttribute('data-original-text', resetPasswordBtn.textContent);

    // Event Handlers
    sendCodeBtn.addEventListener('click', async function() {
        clearErrors();
        
        const email = emailInput.value.trim();
        if (!email) {
            showError(emailError, 'Please enter your email address');
            return;
        }

        setLoading(sendCodeBtn, true);
        
        try {
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    action: 'initiate'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                resetForm.classList.add('email-sent');
            } else {
                showError(emailError, data.message || 'Failed to send verification code');
            }
        } catch (error) {
            showError(emailError, 'An error occurred. Please try again.');
            console.error('Error:', error);
        } finally {
            setLoading(sendCodeBtn, false);
        }
    });
    
    resetPasswordBtn.addEventListener('click', async function() {
        clearErrors();
        
        const email = emailInput.value.trim();
        const code = codeInput.value.trim();
        const newPassword = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        
        // Validation
        if (!code) {
            showError(codeError, 'Please enter the verification code');
            return;
        }
        
        if (!newPassword) {
            showError(passwordError, 'Please enter a new password');
            return;
        }
        
        if (newPassword !== confirmPassword) {
            showError(confirmError, 'Passwords do not match');
            return;
        }
        
        setLoading(resetPasswordBtn, true);
        
        try {
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    action: 'confirm',
                    verificationCode: code,
                    newPassword: newPassword
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Redirect to login page after successful password reset
                window.location.href = 'login.html';
            } else {
                showError(codeError, data.message || 'Failed to reset password');
            }
        } catch (error) {
            showError(codeError, 'An error occurred. Please try again.');
            console.error('Error:', error);
        } finally {
            setLoading(resetPasswordBtn, false);
        }
    });
});