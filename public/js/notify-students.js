document.addEventListener('DOMContentLoaded', () => {
    const notifyStudentsBtn = document.getElementById('notifyStudentsBtn');

    if (notifyStudentsBtn) {
        notifyStudentsBtn.addEventListener('click', async () => {
            try {
                // Get faculty name from local storage
                const facultyName = localStorage.getItem('name');
                if (!facultyName) {
                    throw new Error("Faculty name not found in local storage.");
                }

                // Prepare request payload
                const payload = { facultyName };

                // Call the Lambda function to trigger SNS notifications
                const response = await fetch(
                    'https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/faculty/notify-students', // Replace with your Lambda API endpoint for SNS
                    {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    }
                );
                console.log('Payload:', JSON.stringify({ facultyName }));

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                const result = await response.json();
                alert(result.message); // Show success or error message

            } catch (error) {
                console.error(error);
                alert('Failed to notify students. Please try again later.');
            }
        });
    }
});