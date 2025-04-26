document.addEventListener('DOMContentLoaded', function() {
    const editProfileBtn = document.getElementById('editProfileBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const saveBtn = document.getElementById('saveBtn');
    const formActions = document.querySelector('.form-actions');
    const formInputs = document.querySelectorAll('#profileForm input');
    const profileForm = document.getElementById('profileForm');
    
    // Store original values to revert changes on cancel
    const originalValues = {};
    formInputs.forEach(input => {
        originalValues[input.id] = input.value;
    });

    // Enable editing
    editProfileBtn.addEventListener('click', function() {
        formInputs.forEach(input => {
            input.disabled = false;
        });
        formActions.style.display = 'flex';
        editProfileBtn.style.display = 'none';
    });

    // Cancel editing
    cancelBtn.addEventListener('click', function() {
        formInputs.forEach(input => {
            input.disabled = true;
            input.value = originalValues[input.id];
            // Remove any error styling
            input.classList.remove('input-error');
            
            // Remove any error messages
            const errorElement = input.parentElement.querySelector('.error-message');
            if (errorElement) {
                errorElement.remove();
            }
        });
        formActions.style.display = 'none';
        editProfileBtn.style.display = 'flex';
    });

    // Form submission with validation
    profileForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Clear previous error messages
        document.querySelectorAll('.error-message').forEach(el => el.remove());
        document.querySelectorAll('.input-error').forEach(el => el.classList.remove('input-error'));
        
        let isValid = true;
        
        // Validate required fields
        const firstName = document.getElementById('firstName');
        const lastName = document.getElementById('lastName');
        
        if (!firstName.value.trim()) {
            isValid = false;
            showError(firstName, 'First name is required');
        }
        
        if (!lastName.value.trim()) {
            isValid = false;
            showError(lastName, 'Last name is required');
        }
        
        if (isValid) {
            // Save new values as original values
            formInputs.forEach(input => {
                originalValues[input.id] = input.value;
                input.disabled = true;
            });
            
            formActions.style.display = 'none';
            editProfileBtn.style.display = 'flex';
            
            // Here you would typically send the data to the server
            // For demonstration purposes, we'll just show an alert
            alert('Profile information saved successfully!');
        }
    });
    
    // Helper function to show validation errors
    function showError(inputElement, message) {
        inputElement.classList.add('input-error');
        
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        
        inputElement.parentElement.appendChild(errorElement);
    }
});