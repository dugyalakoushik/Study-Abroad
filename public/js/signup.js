document.addEventListener('DOMContentLoaded', function () {
    // Fix for mobile viewport height
    function setViewportHeight() {
        let vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }
    // Set initial viewport height
    setViewportHeight();
    // Update viewport height on resize
    window.addEventListener('resize', () => {
        setViewportHeight();
    });
    // Form handling
    const signupForm = document.getElementById('signupForm');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const firstNameInput = document.getElementById('fname');
    const lastNameInput = document.getElementById('lname');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');
    const roleInput = document.getElementById('role');

    // Password validation
    function validatePassword(password) {
        const validations = {
            length: password.length >= 8 && password.length <= 30,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /[0-9]/.test(password),
            special: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)
        };
        
        return {
            isValid: Object.values(validations).every(valid => valid),
            validations
        };
    }
    
    // Update password validation UI
    function updatePasswordValidationUI(validations) {
        for (const [key, isValid] of Object.entries(validations)) {
            const element = document.getElementById(key);
            if (element) {
                if (isValid) {
                    element.classList.add('valid');
                    element.classList.remove('invalid');
                } else {
                    element.classList.add('invalid');
                    element.classList.remove('valid');
                }
            }
        }
    }
    
    // Add real-time password validation
    passwordInput.addEventListener('input', function() {
        const { validations } = validatePassword(this.value);
        updatePasswordValidationUI(validations);
    });

    // Handle form submission
    signupForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        // Basic validation
        if (passwordInput.value !== confirmPasswordInput.value) {
            alert('Passwords do not match!');
            return;
        }
        
        // Password policy validation
        const { isValid, validations } = validatePassword(passwordInput.value);
        if (!isValid) {
            alert('Your password does not meet the requirements!');
            updatePasswordValidationUI(validations);
            return;
        }
        
        if (!roleInput.value) {
            alert('Please select a role.');
            return;
        }
        // Collect form data
        const userData = {
            email: emailInput.value,
            password: passwordInput.value,
            firstName: firstNameInput.value,
            lastName: lastNameInput.value,
            phone: phoneInput.value || '',
            userRole: roleInput.value
        };
        try {
            // Make API call to your backend Lambda function via API Gateway
            const response = await fetch('https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(userData),
            });
            if (!response.ok) {
                const errorResponse = await response.json();
                throw new Error(errorResponse.message || 'Error signing up user.');
            }
            const result = await response.json();
            console.log('Sign-up successful:', result);
            alert(`Sign-up successful! Welcome, ${result.username}. Please check your email for verification.`);
            // Redirect to verify page with the username as a URL parameter and auto-fill the role
            // Redirect to verify page with username and role
            window.location.href = `verify.html?username=${encodeURIComponent(result.username)}&role=${encodeURIComponent(roleInput.value)}`;
        } catch (error) {
            console.error('Error during sign-up:', error);
            alert(`Sign-up failed: ${error.message}`);
        }
    });
    // Handle Google Sign-In (if applicable)
    const googleSignInBtn = document.getElementById('googleSignIn');
    googleSignInBtn.addEventListener('click', function () {
        console.log('Google Sign-In clicked');
        // Add your Google Sign-In logic here
    });
    
    // Handle Login button redirect
    const loginBtn = document.querySelector('.top-login-btn');
    loginBtn.addEventListener('click', function () {
        console.log('Login clicked');
        window.location.href = 'login.html'; // Redirect to login page
    });
});
