import { setSession, getSession } from './session.js';

document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('loginForm');
    const loginStatus = document.createElement('div');
    loginStatus.id = 'loginStatus';
    loginForm.appendChild(loginStatus); // Place status inside form for styling

    loginForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const remember = document.getElementById('remember').checked;
        const submitButton = loginForm.querySelector('button[type="submit"]');

        // Show loading state
        submitButton.disabled = true;
        loginStatus.innerText = 'Logging in...';
        loginStatus.style.color = 'black';

        try {
            // Basic client-side validation
            if (!email || !email.includes('@')) throw new Error('Please enter a valid email');
            if (!password) throw new Error('Please enter a password');

            // Authenticate with Lambda
            const response = await fetch(
                'https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/auth/login',
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password, remember }),
                }
            );

            const data = await response.json();
            console.log('Login response:', data); // Debug response
            if (data.success) {
                // Store tokens in session using session.js
                setSession(data);
                localStorage.setItem('email', email); // Store email for later use
                localStorage.setItem('name', data.name); // Store remember choice
                loginStatus.innerText = 'Successfully Logged In';
                loginStatus.style.color = 'green';

                // Redirect based on role
                const role = data.role ? data.role.toLowerCase() : null;
                console.log('Normalized role:', role); // Debug role
                switch (role) {
                    case 'student':
                        window.location.href = 'student.html';
                        break;
                    case 'faculty':
                        window.location.href = 'faculty.html';
                        break;
                    case 'admin':
                        window.location.href = 'admin.html';
                        break;
                    default:
                        throw new Error('Unknown role. Please contact support.');
                }
            } else {
                loginStatus.innerText = 'Login Failed: ' + data.message;
                loginStatus.style.color = 'red';
            }
        } catch (error) {
            console.error('Login error:', error);
            loginStatus.innerText =
                'Error logging in: ' + (error.message || 'Unknown error occurred');
            loginStatus.style.color = 'red';
        } finally {
            submitButton.disabled = false; // Re-enable button
        }
    });
    
});
