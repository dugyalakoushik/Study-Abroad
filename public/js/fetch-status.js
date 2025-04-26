document.addEventListener('DOMContentLoaded', () => {
    const customStatusDropdown = document.getElementById('customStatusInput');
    
    if (customStatusDropdown) {
        // Fetch and populate when page loads
        fetchAndPopulateCustomStatuses();
    }
});

async function fetchAndPopulateCustomStatuses() {
        // Get student name from local storage
        const studentName = localStorage.getItem('name');
        if (!studentName) {
            throw new Error("Student name not found in local storage.");
        }

        // Prepare request payload
        const payload = { student_name: studentName };

        // Call the Lambda function to get custom statuses
        const response = await fetch(
            'https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/students/fetch-status',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            }
        );

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const result = await response.json();
        
        // Clear existing options
        const select = document.getElementById('customStatusInput');
        select.innerHTML = '<option value="None">None</option>';
        
        // Populate dropdown
        result.customstatus.forEach(status => {
            const option = document.createElement('option');
            option.value = status;
            option.textContent = status;
            select.appendChild(option);
        });

}
