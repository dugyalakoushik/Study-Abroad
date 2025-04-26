import { getSession, refreshTokens, logout, initSessionChecker } from './session.js';

// Define API endpoint
const API_ENDPOINT = 'https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/classes';

// Time frame for active groups (in milliseconds) - 1 month
const ACTIVE_THRESHOLD = 30 * 24 * 60 * 60 * 1000;

// Global variables to store classes fetched from the API
let allGroups = [];
let currentGroups = [];

document.addEventListener('DOMContentLoaded', async () => {
    const { idToken, userRole } = getSession();

    if (!idToken || userRole !== 'admin') {
        logout();
        window.location.href = 'login.html';
        return;
    }

    // Session check
    initSessionChecker();

    await fetchAndPopulateClasses();
    setupSeeAllButtons();
    setupCreateGroupButton();
    setupNavigation();

    const desktopLogoutBtn = document.getElementById('desktopLogoutBtn');
    if (desktopLogoutBtn) {
        desktopLogoutBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to log out?')) {
                logout();
            }
        });
    }
});

async function fetchAndPopulateClasses() {
    try {
        const response = await fetch(`${API_ENDPOINT}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('idToken')}`
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.message}`);
        }

        allGroups = await response.json();

        const now = new Date();
        currentGroups = allGroups.filter(group => new Date(group.createdOn).getTime() > (now.getTime() - ACTIVE_THRESHOLD));

        populateGroups();

    } catch (error) {
        console.error('Failed to fetch classes:', error);
        alert(`Failed to load classes: ${error.message}`);
    }
}

function populateGroups() {
    const currentGroupsContainer = document.querySelector('.current-groups');

    currentGroupsContainer.innerHTML = '';

    currentGroups.forEach((group, index) => {
        const card = createCard(group);
        if (index >= 3) {
            card.classList.add('row-hidden');
        }
        currentGroupsContainer.appendChild(card);
    });

    const currentSeeAllBtn = document.querySelector('.see-all-btn[data-section="current"]');
    currentSeeAllBtn.classList.toggle('hidden', currentGroups.length <= 3);
}

function createCard(group) {
    const card = document.createElement('div');
    card.className = 'card';
    card.setAttribute('data-id', group.classId);

    const createdOnDate = new Date(group.createdOn).toLocaleDateString();

    card.innerHTML = `
        <h3>${group.name}</h3>
        <div class="card-info">
            <p>Faculty: <span>${group.faculty}</span></p>
            <p>Created On: <span>${createdOnDate}</span></p>
        </div>
    `;

    card.addEventListener('click', () => handleCardClick(group));

    return card;
}

function handleCardClick(group) {
    console.log(`Clicked group: ${group.name}`);
    window.location.href = `class-details.html?classId=${group.classId}`;
}

function setupSeeAllButtons() {
    const seeAllButtons = document.querySelectorAll('.see-all-btn');

    seeAllButtons.forEach(button => {
        button.addEventListener('click', () => {
            const section = button.getAttribute('data-section');
            const container = document.querySelector(`.${section}-groups`);
            const hiddenCards = container.querySelectorAll('.row-hidden');

            hiddenCards.forEach(card => {
                card.classList.remove('row-hidden');
            });

            button.classList.add('hidden');
        });
    });
}

function setupCreateGroupButton() {
    const createGroupBtn = document.querySelector('.create-group-btn');

    if (createGroupBtn) {
        createGroupBtn.addEventListener('click', () => {
            showAddClassModal();
        });
    }
}

function showAddClassModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <h2>Add New Class</h2>
            <form id="addClassForm">
                <input type="text" id="className" placeholder="Class Name" required>
                <input type="text" id="facultyName" placeholder="Faculty Name" required>
                <button type="submit">Add Class</button>
                <button type="button" class="cancel">Cancel</button>
            </form>
        </div>
    `;
    document.body.appendChild(modal);

    const form = modal.querySelector('#addClassForm');
    form.addEventListener('submit', handleAddClass);

    const cancelBtn = modal.querySelector('.cancel');
    cancelBtn.addEventListener('click', () => {
        document.body.removeChild(modal);
    });
}

const handleAddClass = async (event) => {
    event.preventDefault();

    const className = document.getElementById('className').value;
    const facultyName = document.getElementById('facultyName').value;

    try {
        const response = await fetch(`${API_ENDPOINT}/add`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('idToken')}`
            },
            body: JSON.stringify({
                className,
                facultyName
                // createdOn should be added server-side for integrity
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.message}`);
        }

        const newClass = await response.json();

        allGroups.push({
            classId: newClass.classId,
            name: newClass.name,
            faculty: newClass.faculty,
            createdOn: newClass.createdOn
        });

        const now = new Date();
        currentGroups = allGroups.filter(group => new Date(group.createdOn).getTime() > (now.getTime() - ACTIVE_THRESHOLD));

        populateGroups();
        document.querySelector('.modal').remove();
    } catch (error) {
        console.error('Error adding class:', error);
        alert(`Failed to add class: ${error.message}`);
    }
};

// Navigation Logic
function setupNavigation() {
    const navButtons = document.querySelectorAll('.nav-menu button');
    const mainContent = document.getElementById('mainContent');
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('backdrop');

    // Create a template for dashboard content
    const dashboardTemplate = document.querySelector('.dashboard-content').cloneNode(true);
    let currentPage = 'dashboard';

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
                        <input type="text" id="firstName" name="firstName" value="Admin" disabled required>
                    </div>
                    <div class="form-group">
                        <label for="lastName">Last Name <span class="required">*</span></label>
                        <input type="text" id="lastName" name="lastName" value="User" disabled required>
                    </div>
                </div>
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" name="username" value="adminuser" disabled>
                </div>
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" value="admin@example.com" disabled>
                </div>
                <div class="form-group">
                    <label for="phone">Phone Number</label>
                    <input type="tel" id="phone" name="phone" value="+1 (555) 987-6543" disabled>
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

    // Help HTML content with admin-specific FAQs
    const helpContent = `
        <div class="help-section">
            <h1>Help & Support</h1>
            <div class="faq-container">
                <h2>Frequently Asked Questions</h2>
                <div id="faqContent">
                    <h3>1. How do I add a new class?</h3>
                    <p>Click the "Create Group" button on the dashboard, enter the class name and faculty name in the modal, and click "Add Class" to create a new class.</p>
                    <h3>2. How can I add a student to a class?</h3>
                    <p>Click on a class from the dashboard to view its details, then use the "Add Student" option to include a student in that class.</p>
                    <h3>3. How do I add a faculty member to a class?</h3>
                    <p>Click on a class from the dashboard to view its details, then use the "Add Faculty" option to assign a faculty member to that class.</p>
                    <h3>4. How can I deploy the system for a new semester?</h3>
                    <p>The system is designed for quick deployment. Contact the IT support team at support@tamu-studyabroad.edu to set up a new installation each semester.</p>
                    <h3>5. How do I view usage statistics?</h3>
                    <p>Usage statistics are available through the admin dashboard. Check the class details page for data on faculty and student activity to assess system value.</p>
                </div>
            </div>
        </div>
    `;

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

    // Navigation Buttons
    navButtons.forEach(button => {
        button.addEventListener('click', function () {
            navButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            const page = this.getAttribute('data-page');

            if (page !== currentPage) {
                if (page === 'profile') {
                    mainContent.innerHTML = profileContent;
                    attachProfileEventListeners();
                } else if (page === 'help') {
                    mainContent.innerHTML = helpContent;
                } else if (page === 'dashboard') {
                    mainContent.innerHTML = dashboardTemplate.innerHTML;
                    setupSeeAllButtons();
                    setupCreateGroupButton();
                    populateGroups();
                }
                currentPage = page;
                sidebar.classList.remove('active');
                if (backdrop) backdrop.classList.remove('active');
            }
        });
    });

    // Initialize default active page
    document.querySelector('[data-page="dashboard"]').classList.add('active');
}