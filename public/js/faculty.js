import { getSession, refreshTokens, logout, initSessionChecker } from './session.js';

document.addEventListener('DOMContentLoaded', async function () {
    // Get session data
    const { idToken, userRole, tokenExpiresAt } = getSession();

    // Check if session is expired or invalid
    if (!idToken || userRole !== 'faculty') {
        logout();
        return;
    }

    // Initialize session checker
    initSessionChecker();

    // DOM Elements
    const navItems = document.querySelectorAll('.nav-item');
    const mainContent = document.querySelector('.main-content');
    const desktopLogoutBtn = document.getElementById('desktopLogoutBtn');
    const mobileLogoutBtn = document.getElementById('mobileLogoutBtn');
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('backdrop');

    // Store initial dashboard content and student data
    const initialDashboardContent = document.getElementById('dashboardContent').innerHTML;
    let studentData = null;

    // Profile HTML content
    const profileContent = `
        <div class="profile-section">
            <div class="profile-header">
                <div class="profile-title">
                    <i class="fas fa-user"></i>
                    <h1>Profile Information</h1>
                </div>
                <button id="editProfileBtn" class="edit-btn">
                    <i class="fas fa-edit"></i> Edit Profile
                </button>
            </div>
            <form id="profileForm">
                <div class="form-row">
                    <div class="form-group">
                        <label for="firstName">First Name <span class="required">*</span></label>
                        <input type="text" id="firstName" name="firstName" value="John" disabled required>
                    </div>
                    <div class="form-group">
                        <label for="lastName">Last Name <span class="required">*</span></label>
                        <input type="text" id="lastName" name="lastName" value="Doe" disabled required>
                    </div>
                </div>
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" value="johndoe" disabled>
                </div>
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" value="john.doe@example.com" disabled>
                </div>
                <div class="form-group">
                    <label for="phone">Phone Number</label>
                    <input type="tel" id="phone" name="phone" value="+1 (555) 123-4567" disabled>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" value="•••••••" disabled>
                </div>
                <div class="form-actions" style="display: none;">
                    <button type="button" id="cancelBtn" class="cancel-btn">Cancel</button>
                    <button type="submit" id="saveBtn" class="save-btn">Save</button>
                </div>
            </form>
        </div>
    `;

    // Help HTML content with embedded FAQs
    const helpContent = `
        <div class="help-section">
            <h1>Help & Support</h1>
            <div class="faq-container">
                <h2>Frequently Asked Questions</h2>
                <div id="faqContent">
                    <h3>1. How do I view the current locations of my students?</h3>
                    <p>Click the "Refresh Student Locations" button on the dashboard to fetch and display the latest check-in data, including student names, addresses, dates, times, and map links.</p>
                    <h3>2. How can I notify students to check in for a required event?</h3>
                    <p>Use the "Notify Students to Check-in" button on the dashboard. This sends a notification to all students in your class, prompting them to submit their current location and status.</p>
                    <h3>3. What does auditing student locations mean, and how do I do it?</h3>
                    <p>Auditing involves verifying student locations against their reported check-ins. After refreshing student locations, review the "Real-time Student Locations" and "Additional Details" tables to ensure the data aligns with expected locations.</p>
                    <h3>4. How do I create a new check-in status for students to select?</h3>
                    <p>Click the "Create New Check-in Status" button to open a form where you can define a custom status. Enter the status name and any additional fields, then submit to make it available for students.</p>
                    <h3>5. What should I do if no student data appears after refreshing locations?</h3>
                    <p>Ensure you are connected to the internet and your faculty name is correctly set in the system. If the issue persists, contact the administrator to verify the class setup and API connectivity.</p>
                    <h3>6. Can I customize notifications sent to students?</h3>
                    <p>Currently, notifications are standardized. To request custom notification options, please contact the system administrator with your requirements.</p>
                    <h3>7. How often should I refresh student locations?</h3>
                    <p>Refresh as needed, typically before or during required check-in events. The system fetches the latest data each time you click "Refresh Student Locations."</p>
                    <h3>8. Who do I contact for technical support?</h3>
                    <p>Reach out to the study abroad program administrator via email at support@tamu-studyabroad.edu or through the university's IT helpdesk.</p>
                </div>
            </div>
        </div>
    `;

    // Function to fetch and display student details
    async function fetchStudentDetails(container, table) {
        try {
            const facultyName = localStorage.getItem('name');
            if (!facultyName) {
                throw new Error("Faculty name not found in local storage.");
            }

            const payload = { facultyName };

            const response = await fetch(
                'https://s4rruk7vn6.execute-api.us-east-1.amazonaws.com/prod/LocationFaculty',
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                }
            );

            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);

            const rawData = await response.json();
            console.log("Raw API Response:", rawData);

            let studentDetails;
            try {
                studentDetails =
                    typeof rawData.body === "string"
                        ? JSON.parse(rawData.body)
                        : rawData.body || rawData;
            } catch (err) {
                throw new Error("Failed to parse API response");
            }

            if (!Array.isArray(studentDetails)) throw new Error("Invalid data format");

            studentData = studentDetails; // Store the data
            displayStudentDetails(studentDetails, container);
            displayAdditionalDetails(studentDetails, table);
            
        } catch (error) {
            console.error(error);
            container.innerHTML =
                '<p class="error-message">Error loading student data. Please try again later.</p>';
            table.innerHTML =
                '<tr><td colspan="7" class="error-message">Error loading additional details. Please try again later.</td></tr>';
        }
    }

    // Function to attach or re-attach event listeners for dashboard buttons
    function attachDashboardEventListeners() {
        const getStudentDetailsBtn = document.getElementById('getStudentDetailsBtn');
        const studentDetailsContainer = document.getElementById('studentDetailsContainer');
        const additionalDetailsTable = document.getElementById('additionalDetailsTable');

        if (getStudentDetailsBtn && studentDetailsContainer && additionalDetailsTable) {
            // Remove existing listeners to prevent duplicates
            getStudentDetailsBtn.replaceWith(getStudentDetailsBtn.cloneNode(true));
            const newGetStudentDetailsBtn = document.getElementById('getStudentDetailsBtn');
            
            newGetStudentDetailsBtn.addEventListener('click', () => {
                fetchStudentDetails(studentDetailsContainer, additionalDetailsTable);
            });
        }
    }

    // Function to attach Profile event listeners
    function attachProfileEventListeners() {
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
        if (editProfileBtn) {
            editProfileBtn.addEventListener('click', function() {
                formInputs.forEach(input => {
                    input.disabled = false;
                });
                formActions.style.display = 'flex';
                editProfileBtn.style.display = 'none';
            });
        }

        // Cancel editing
        if (cancelBtn) {
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
        }

        // Form submission with validation
        if (profileForm) {
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
                    
                    // Show success message
                    alert('Profile information saved successfully!');
                }
            });
        }

        // Helper function to show validation errors
        function showError(inputElement, message) {
            inputElement.classList.add('input-error');
            
            const errorElement = document.createElement('div');
            errorElement.className = 'error-message';
            errorElement.textContent = message;
            
            inputElement.parentElement.appendChild(errorElement);
        }
    }

    // Navigation Menu Active State
    navItems.forEach(item => {
        item.addEventListener('click', function () {
            navItems.forEach(nav => nav.classList.remove('active'));
            this.classList.add('active');

            const pageType = this.getAttribute('data-page');
            if (pageType === 'dashboard') {
                // Restore original dashboard content
                mainContent.innerHTML = `<div id="dashboardContent">${initialDashboardContent}</div>`;
                // Restore student data if available
                const studentDetailsContainer = document.getElementById('studentDetailsContainer');
                const additionalDetailsTable = document.getElementById('additionalDetailsTable');
                if (studentData && studentDetailsContainer && additionalDetailsTable) {
                    displayStudentDetails(studentData, studentDetailsContainer);
                    displayAdditionalDetails(studentData, additionalDetailsTable);
                }
                // Re-attach event listeners
                attachDashboardEventListeners();
            } else if (pageType === 'profile') {
                mainContent.innerHTML = profileContent;
                attachProfileEventListeners();
            } else if (pageType === 'help') {
                mainContent.innerHTML = helpContent;
            }
            mainContent.style.display = 'block';
            sidebar.classList.remove('active');
            backdrop.classList.remove('active');
        });
    });

    // Hamburger Menu Toggle
    if (hamburgerBtn) {
        hamburgerBtn.addEventListener('click', function () {
            sidebar.classList.toggle('active');
            backdrop.classList.toggle('active');
        });
    }

    // Backdrop Click to Close Menu
    if (backdrop) {
        backdrop.addEventListener('click', function () {
            sidebar.classList.remove('active');
            backdrop.classList.remove('active');
        });
    }

    // Logout Buttons
    [desktopLogoutBtn, mobileLogoutBtn].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', function () {
                if (confirm('Are you sure you want to log out?')) {
                    logout();
                    sidebar.classList.remove('active');
                    backdrop.classList.remove('active');
                }
            });
        }
    });

    function checkNotifications() {
        console.log('Checking for new notifications...');
    }

    setInterval(checkNotifications, 300000);

    // Initial event listener setup
    attachDashboardEventListeners();

    function displayStudentDetails(details, container) {
        if (!Array.isArray(details) || details.length === 0) {
            container.innerHTML =
                '<p class="no-data">No student check-ins found.</p>';
            return;
        }

        container.innerHTML =
            '<table class="student-details-table"><thead><tr><th>Name</th><th>Address</th><th>Date</th><th>Time</th><th>Latitude</th><th>Longitude</th><th>Maps Link</th></tr></thead><tbody>' +
            details.map(student => `
                    <tr>
                        <td>${student.name || "N/A"}</td>
                        <td>${student.address || "N/A"}</td>
                        <td>${student.date || "N/A"}</td>
                        <td>${student.time || "N/A"}</td>
                        <td>${student.latitude?.toFixed(6) || "N/A"}</td>
                        <td>${student.longitude?.toFixed(6) || "N/A"}</td>
                        <td><a href="${student.mapsLink}" target="_blank">View Map</a></td>
                    </tr>`).join("") +
            '</tbody></table>';
    }

    function displayAdditionalDetails(details, table) {
        if (!Array.isArray(details) || details.length === 0) {
            table.innerHTML =
                '<tr><td colspan="7" class="no-data">No additional details found.</td></tr>';
            return;
        }

        table.innerHTML = details.map(student => `
            <tr>
                <td>${student.name || "N/A"}</td>
                <td>${student.peers || "None"}</td>
                <td>${student.place || "N/A"}</td>
                <td>${student.studentStatus || "None"}</td>
                <td>${student.comments || "N/A"}</td>
                <td>${student.emergency ? "Yes" : "No"}</td>
                <td>${student.emergencyDetails || "N/A"}</td>
            </tr>`).join("");
    }
});