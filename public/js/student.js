import { getSession, refreshTokens, logout, initSessionChecker } from './session.js';

document.addEventListener('DOMContentLoaded', async function () {
    // Get session data
    const { idToken, userRole, tokenExpiresAt, name } = getSession();

    // Check if session is expired or invalid
    if (!idToken || userRole !== 'student') {
        logout();
        return;
    }

    // Initialize session checker
    initSessionChecker(); // Note: If the "Failed to load custom statuses" message persists, check this function in session.js for any status-fetching logic.

    // DOM Elements
    let getLocationBtn = document.getElementById('getLocation');
    let coordinatesDisplay = document.getElementById('coordinates');
    let addressDisplay = document.getElementById('addressDisplay');
    let withWhomInput = document.getElementById('withWhomInput');
    let currentPlaceInput = document.getElementById('currentPlaceInput');
    let commentsInput = document.getElementById('commentsInput');
    let checkInBtn = document.getElementById('checkInBtn');
    let mapsLink = document.getElementById('mapsLink');
    const navButtons = document.querySelectorAll('.nav-menu button');
    const desktopLogoutBtn = document.getElementById('desktopLogoutBtn');
    const mobileLogoutBtn = document.getElementById('mobileLogoutBtn');
    let sosButton = document.getElementById('sosButton');
    let emergencyForm = document.getElementById('emergencyForm');
    let emergencyDetails = document.getElementById('emergencyDetails');
    let submitEmergencyDetails = document.getElementById('submitEmergencyDetails');
    let skipEmergencyDetails = document.getElementById('skipEmergencyDetails');
    const hamburgerBtn = document.getElementById('hamburgerBtn');
    const sidebar = document.getElementById('sidebar');
    const backdrop = document.getElementById('backdrop');
    const mainContent = document.getElementById('mainContent');

    // API Configuration
    const API_ENDPOINT = 'https://y4p26puv7l.execute-api.us-east-1.amazonaws.com/locations/locations';
    const GEOAPIFY_API_KEY = 'f6a76cacf081475897b4d70fd23f3d62';

    // Get user name from local storage
    const userName = localStorage.getItem('name');

    // Track location data
    let currentLocation = {
        latitude: null,
        longitude: null,
        address: null
    };

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
                    <h3>1. How do I check in with my location?</h3>
                    <p>Click "Get Current Location" to fetch your coordinates and address, fill in the check-in details, and click "Check In" to submit.</p>
                    <h3>2. How can I see my current check-in status?</h3>
                    <p>After checking in, your latest location and details are displayed under "Current Location" and "Address" on the dashboard.</p>
                    <h3>3. How do I include peers in my check-in?</h3>
                    <p>In the "My Peers" dropdown, hold Ctrl/Cmd to select multiple peers you're with, then submit your check-in.</p>
                    <h3>4. What should I do if I feel unsafe?</h3>
                    <p>Click the "SOS" button to send an emergency signal. You can add details about your situation or skip to send immediately.</p>
                    <h3>5. What happens after I check in?</h3>
                    <p>Your location and details are sent to your faculty member, and a Google Maps link is generated for your check-in location.</p>
                    <h3>6. Who can see my check-in information?</h3>
                    <p>Your faculty member can view your check-in details to ensure your safety.</p>
                    <h3>7. What if I can’t get my location?</h3>
                    <p>Ensure location services are enabled on your device. If the issue persists, contact support at support@tamu-studyabroad.edu.</p>
                </div>
            </div>
        </div>
    `;

    // Function to get address from coordinates using Geoapify Reverse Geocoding API
    async function getAddressFromCoordinates(lat, lon) {
        const reverseGeocodingUrl = `https://api.geoapify.com/v1/geocode/reverse?lat=${lat}&lon=${lon}&apiKey=${GEOAPIFY_API_KEY}`;
        try {
            const response = await fetch(reverseGeocodingUrl);
            if (!response.ok) throw new Error('Failed to fetch address');
            const data = await response.json();
            if (data.features && data.features.length > 0) {
                return data.features[0].properties.formatted;
            } else {
                throw new Error('No address found');
            }
        } catch (error) {
            console.error('Error fetching address:', error);
            return 'Address not found';
        }
    }

    // Function to get current position
    async function getCurrentPosition() {
        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            });
        });
    }

    // Function to send check-in data
    async function sendCheckInData(isEmergency = false, emergencyMessage = '') {
        if (!currentLocation.latitude || !currentLocation.longitude) {
            alert('Please get your current location first.');
            return false;
        }

        try {
            const selectedPeers = Array.from(withWhomInput.selectedOptions)
                .map(option => option.value)
                .filter(value => value !== "None")
                .join(", ");
            const selectedStatus = document.getElementById('customStatusInput').value;

            const payload = {
                id: idToken,
                latitude: currentLocation.latitude,
                longitude: currentLocation.longitude,
                address: currentLocation.address,
                name: userName,
                peers: selectedPeers || 'None',
                place: currentPlaceInput.value,
                comments: commentsInput.value,
                emergency: isEmergency,
                emergencyDetails: emergencyMessage,
                studentStatus: selectedStatus
            };

            console.log('Payload being sent to API:', payload);

            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${idToken}`
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error('API request failed');

            const responseData = await response.json();
            console.log('Check-in data sent successfully:', responseData);

            if (responseData.mapsLink) {
                mapsLink.textContent = 'View on Google Maps';
                mapsLink.href = responseData.mapsLink;
                mapsLink.classList.remove('hidden');
            }

            return true;
        } catch (error) {
            console.error("Error sending check-in data:", error);
            alert(error.message || "Unable to process check-in");
            return false;
        }
    }

    // Initialize event listeners
    function initializeEventListeners() {
        getLocationBtn.addEventListener('click', async function () {
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Getting location...';

            try {
                const position = await getCurrentPosition();

                const latitude = position.coords.latitude.toFixed(6);
                const longitude = position.coords.longitude.toFixed(6);
                const coords = `${latitude},${longitude}`;
                
                coordinatesDisplay.textContent = coords;

                const address = await getAddressFromCoordinates(latitude, longitude);
                addressDisplay.textContent = address;

                currentLocation = {
                    latitude,
                    longitude,
                    address
                };

                mapsLink.href = `https://www.google.com/maps?q=${coords}`;
                mapsLink.classList.remove('hidden');

            } catch (error) {
                console.error("Error:", error);
                alert(error.message || "Unable to get location");
            } finally {
                getLocationBtn.disabled = false;
                getLocationBtn.innerHTML = 'Get Current Location';
            }
        });

        checkInBtn.addEventListener('click', async function() {
            this.disabled = true;
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

            try {
                const success = await sendCheckInData();
                if (success) {
                    alert('Check-in successful!');
                    commentsInput.value = '';
                    withWhomInput.value = 'None';
                    currentPlaceInput.value = '';
                }
            } catch (error) {
                console.error("Error:", error);
            } finally {
                this.disabled = false;
                this.innerHTML = originalText;
            }
        });

        sosButton.addEventListener('click', async function () {
            this.disabled = true;
            const originalText = this.textContent;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

            try {
                if (!currentLocation.latitude || !currentLocation.longitude) {
                    const position = await getCurrentPosition();
                    
                    const latitude = position.coords.latitude.toFixed(6);
                    const longitude = position.coords.longitude.toFixed(6);
                    const coords = `${latitude},${longitude}`;
                    
                    coordinatesDisplay.textContent = coords;

                    const address = await getAddressFromCoordinates(latitude, longitude);
                    addressDisplay.textContent = address;

                    currentLocation = {
                        latitude,
                        longitude,
                        address
                    };

                    mapsLink.href = `https://www.google.com/maps?q=${coords}`;
                    mapsLink.classList.remove('hidden');
                }

                emergencyForm.classList.remove('hidden');

            } catch (error) {
                console.error("Error:", error);
                alert(error.message || "Unable to send emergency signal");
            } finally {
                this.disabled = false;
                this.textContent = originalText;
            }
        });

        submitEmergencyDetails.addEventListener('click', async function () {
            const detailsText = emergencyDetails.value;
            emergencyForm.classList.add('hidden');
            
            const success = await sendCheckInData(true, detailsText);
            if (success) {
                alert('Emergency signal sent successfully with details.');
            }
        });

        skipEmergencyDetails.addEventListener('click', async function () {
            emergencyForm.classList.add('hidden');
            
            const success = await sendCheckInData(true, '');
            if (success) {
                alert('Emergency signal sent successfully.');
            }
        });

        document.querySelectorAll('.copy-btn').forEach(button => {
            button.addEventListener('click', function () {
                const textToCopy = this.previousElementSibling?.textContent || '';
                if (textToCopy) {
                    navigator.clipboard.writeText(textToCopy)
                        .then(() => {
                            const icon = this.querySelector('i');
                            icon.className = 'fas fa-check copy-success';
                            setTimeout(() => {
                                icon.className = 'fas fa-copy';
                            }, 1000);
                        })
                        .catch(err => {
                            console.error('Failed to copy text:', err);
                            alert('Failed to copy text to clipboard');
                        });
                }
            });
        });

        mapsLink.addEventListener('click', function (e) {
            e.preventDefault();
            const coordinates = coordinatesDisplay.textContent;
            if (coordinates) {
                window.open(`https://www.google.com/maps?q=${coordinates}`, '_blank');
            }
        });

        if (commentsInput) {
            commentsInput.addEventListener('input', function () {
                this.style.height = 'auto';
                this.style.height = `${this.scrollHeight}px`;
            });
        }

        if (emergencyDetails) {
            emergencyDetails.addEventListener('input', function () {
                this.style.height = 'auto';
                this.style.height = `${this.scrollHeight}px`;
            });
        }

        hamburgerBtn.addEventListener('click', function () {
            sidebar.classList.toggle('active');
            backdrop.classList.toggle('active');
        });

        backdrop.addEventListener('click', function () {
            sidebar.classList.remove('active');
            backdrop.classList.remove('active');
        });

        // Handle "My Peers" dropdown to prevent selecting "None" with other options
        withWhomInput.addEventListener('change', function () {
            const selectedOptions = Array.from(this.selectedOptions).map(option => option.value);
            const noneIndex = selectedOptions.indexOf('None');
            
            if (noneIndex !== -1 && selectedOptions.length > 1) {
                // If "None" is selected along with other options, deselect "None"
                this.options[0].selected = false;
            } else if (noneIndex === -1 && selectedOptions.length > 0) {
                // If other options are selected, ensure "None" is deselected
                this.options[0].selected = false;
            }
        });
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

    // Populate student dropdown
    async function populateStudentDropdown() {
        const currentUserName = localStorage.getItem('name');
        if (!currentUserName) {
            console.error("User name not found in session");
            return;
        }
    
        const apiUrl = "https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/classes/studentsinsideclass";
    
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${idToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    userName: currentUserName
                })
            });
            
            if (!response.ok) {
                throw new Error("Failed to fetch student data");
            }
            
            const students = await response.json();
    
            withWhomInput.innerHTML = "";
            withWhomInput.setAttribute('multiple', 'true');
            withWhomInput.size = Math.min(5, students.length + 1);
            
            const noneOption = document.createElement("option");
            noneOption.value = "None";
            noneOption.textContent = "None";
            withWhomInput.appendChild(noneOption);
            
            students.forEach(student => {
                if (student.name !== currentUserName) {
                    const option = document.createElement("option");
                    option.value = student.name;
                    option.textContent = student.name;
                    withWhomInput.appendChild(option);
                }
            });
            
        } catch (error) {
            console.error("Error loading students:", error);
        }
    }

    // Navigation Buttons
    navButtons.forEach(button => {
        button.addEventListener('click', function () {
            navButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            const page = this.getAttribute('data-page');

            if (page !== currentPage) {
                // Save current state before switching
                const currentState = {
                    currentPlace: currentPlaceInput.value,
                    comments: commentsInput.value,
                    selectedPeers: Array.from(withWhomInput.selectedOptions).map(option => option.value),
                    coordinates: coordinatesDisplay.textContent,
                    address: addressDisplay.textContent,
                    locationFetched: currentLocation.latitude && currentLocation.longitude
                };

                if (page === 'profile') {
                    mainContent.innerHTML = profileContent;
                    attachProfileEventListeners();
                } else if (page === 'help') {
                    mainContent.innerHTML = helpContent;
                } else if (page === 'dashboard') {
                    // Restore dashboard content
                    mainContent.innerHTML = dashboardTemplate.innerHTML;

                    // Reinitialize DOM elements
                    getLocationBtn = document.getElementById('getLocation');
                    coordinatesDisplay = document.getElementById('coordinates');
                    addressDisplay = document.getElementById('addressDisplay');
                    withWhomInput = document.getElementById('withWhomInput');
                    currentPlaceInput = document.getElementById('currentPlaceInput');
                    commentsInput = document.getElementById('commentsInput');
                    checkInBtn = document.getElementById('checkInBtn');
                    mapsLink = document.getElementById('mapsLink');
                    sosButton = document.getElementById('sosButton');
                    emergencyForm = document.getElementById('emergencyForm');
                    emergencyDetails = document.getElementById('emergencyDetails');
                    submitEmergencyDetails = document.getElementById('submitEmergencyDetails');
                    skipEmergencyDetails = document.getElementById('skipEmergencyDetails');

                    // Restore state
                    currentPlaceInput.value = currentState.currentPlace;
                    commentsInput.value = currentState.comments;
                    coordinatesDisplay.textContent = currentState.coordinates;
                    addressDisplay.textContent = currentState.address;
                    if (currentState.locationFetched) {
                        currentLocation = {
                            latitude: currentLocation.latitude,
                            longitude: currentLocation.longitude,
                            address: currentState.address
                        };
                        mapsLink.href = `https://www.google.com/maps?q=${currentState.coordinates}`;
                        mapsLink.classList.remove('hidden');
                    }

                    // Restore selected peers
                    withWhomInput.innerHTML = "";
                    const noneOption = document.createElement("option");
                    noneOption.value = "None";
                    noneOption.textContent = "None";
                    withWhomInput.appendChild(noneOption);
                    populateStudentDropdown().then(() => {
                        currentState.selectedPeers.forEach(peer => {
                            const options = withWhomInput.options;
                            for (let i = 0; i < options.length; i++) {
                                if (options[i].value === peer) {
                                    options[i].selected = true;
                                    break;
                                }
                            }
                        });
                    });

                    initializeEventListeners();
                }
                currentPage = page;
                sidebar.classList.remove('active');
                backdrop.classList.remove('active');
            }
        });
    });

    // Initialize data and set default active page
    initializeEventListeners();
    populateStudentDropdown();
    document.querySelector('[data-page="dashboard"]').classList.add('active');

    // Attach logout event listeners to both buttons
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
});