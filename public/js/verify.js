document.getElementById('verifyForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const verificationCode = document.getElementById('verificationCode').value;
    const userRole = document.getElementById('role').value;

    if (!username) {
        alert('Username is missing!');
        return;
    }
    
    if (!userRole) {
        alert('User role is missing!');
        return;
    }

    try {
        const response = await fetch('https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                action: 'confirm',
                username: username,
                verificationCode: verificationCode,
                userRole: userRole
            })
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
            window.location.href = 'login.html'; // Redirect to login page
        } else {
            alert(`Error verifying account: ${result.message}`);
        }
    } catch (error) {
        console.error('Error during account verification:', error);
        alert('An unexpected error occurred.');
    }
});