// session.js - Centralized Session Management

// Set session data in localStorage
function setSession(data) {
    
    if (data.idToken) localStorage.setItem('idToken', data.idToken);
    if (data.accessToken) localStorage.setItem('accessToken', data.accessToken);
    if (data.refreshToken) localStorage.setItem('refreshToken', data.refreshToken);
    if (data.role) localStorage.setItem('userRole', data.role);
    if (data.expiresIn) {
        localStorage.setItem('tokenExpiresAt', Date.now() + data.expiresIn * 1000); // Set token expiration to the correct time
        //localStorage.setItem('tokenExpiresAt', Date.now() + 3 * 60 * 1000); // Simulate token expiration in 3 minutes
   
    }
}

// Get session data from localStorage
function getSession() {
    const sessionData = {
        email: localStorage.getItem('email'),
        idToken: localStorage.getItem('idToken'),
        accessToken: localStorage.getItem('accessToken'),
        refreshToken: localStorage.getItem('refreshToken'),
        userRole: localStorage.getItem('userRole'),
        tokenExpiresAt: parseInt(localStorage.getItem('tokenExpiresAt'), 10),
    };
    return sessionData;
}

// Check if session is expired
function isSessionExpired() {
    const tokenExpiresAt = getSession().tokenExpiresAt;
    return tokenExpiresAt && Date.now() > tokenExpiresAt;
}

// Refresh tokens
async function refreshTokens() {
    const { email, refreshToken } = getSession();
    if (!refreshToken) {
        console.error('No refresh token available');
        return false; // No refresh token available
    }

    try {
        console.log('Attempting to refresh tokens with:', { email, refreshToken });

        const response = await fetch(
            'https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/auth/refresh',
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, refreshToken, action: 'refresh' }),
            }
        );

        const data = await response.json();
        console.log('Refresh token response:', data);

        if (data.success) {
            setSession(data); // Store new session tokens
            return true; // Successfully refreshed tokens
        } else {
            console.error('Failed to refresh tokens:', data.message);
            return false; // Failed to refresh tokens
        }
    } catch (error) {
        console.error('Error refreshing tokens:', error);
        return false; // Error during refresh
    }
}

// Logout and clear session data
function logout() {
    localStorage.clear();
    window.location.href = 'login.html'; // Redirect to login page after logout
}

// Periodically check token expiration and refresh tokens if needed
async function initSessionChecker() {
    setInterval(async () => {
        const session = getSession();
        const { tokenExpiresAt } = session;
        if (tokenExpiresAt && Date.now() >= tokenExpiresAt - 60 * 1000) {
            console.log('Refreshing tokens...');
            const refreshSuccess = await refreshTokens();
            if (!refreshSuccess) {
                console.log('Failed to refresh token');
                logout(); // Log the user out if refresh fails
            }
        }
    }, 1 * 60 * 1000); // Check every minute
}

export { setSession, getSession, isSessionExpired, refreshTokens, logout, initSessionChecker };