import { getSession, refreshTokens, logout, initSessionChecker } from './session.js';

document.addEventListener('DOMContentLoaded', async () => {
    const { idToken, userRole, tokenExpiresAt } = getSession();

    const urlParams = new URLSearchParams(window.location.search);
    const classId = urlParams.get('classId');

    if (!classId) {
        alert('Class ID is missing!');
        window.location.href = 'admin.html'; // Redirect to admin page
        return;
    }
    
    initSessionChecker();

    // Fetch class details
    try {
        const classDetails = await fetchClassDetails(classId, idToken);
        document.getElementById('class-name').textContent = classDetails.name;
        document.getElementById('faculty-name').textContent = classDetails.faculty;
    } catch (error) {
        console.error("Error loading class details:", error);
        document.getElementById('class-name').textContent = "Error loading class details";
        document.getElementById('faculty-name').textContent = "Error loading faculty details";
    }

    // Populate student dropdown
    await populateStudentDropdown(idToken);

    // Populate current students list
    await populateCurrentStudentsList(classId, idToken);

    // Handle Add Student Button
    document.getElementById("addStudentForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        await addStudentToClass(classId, idToken);
    });

    // Populate faculty dropdown
    await populateFacultyDropdown(idToken);

    // Populate current faculty list
    await populateCurrentFacultyList(classId, idToken);

    // Handle Add Faculty Button
    document.getElementById("addFacultyForm").addEventListener("submit", async (event) => {
        event.preventDefault();
        await addFacultyToClass(classId, idToken);
    });

    // Navigation Buttons Event Listeners
    document.getElementById('previousBtn').addEventListener('click', () => {
        // Redirect to previous page (replace 'previous-page.html' with your actual page)
        window.location.href = 'admin.html';
    });

    document.getElementById('saveAndExitBtn').addEventListener('click', () => {
        // Redirect to previous page (replace 'previous-page.html' with your actual page)
        window.location.href = 'admin.html';
    });

    // Delete Class Functionality
    document.getElementById('deleteClassBtn').addEventListener('click', async () => {
        if (confirm('Are you sure you want to delete this class?')) {
            try {
                const deleteSuccess = await deleteClass(classId, idToken);
                if (deleteSuccess) {
                    alert('Class deleted successfully!');
                    window.location.href = 'admin.html'; // Redirect to admin page after deletion
                } else {
                    alert('Failed to delete class.');
                }
            } catch (error) {
                console.error("Error deleting class:", error);
                alert('Error deleting class. Please try again.');
            }
        }
    });
});

async function fetchClassDetails(classId, idToken) {
    const apiUrl = `https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/classes/getclassdetails`;
    try {
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${idToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ classId: classId }) // Send classId in the body
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch class details, status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Fetched class details:', data);
        return data;
    } catch (error) {
        console.error("Error fetching class details:", error);
        throw error;
    }
}

async function populateStudentDropdown(idToken) {
    const studentDropdown = document.getElementById("studentEmail");
    const apiUrl = "https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/students";

    try {
        const response = await fetch(apiUrl, {
            headers: {
                'Authorization': `Bearer ${idToken}`,
                'Content-Type': 'application/json'
            },
        });
        if (!response.ok) {
            throw new Error("Failed to fetch student data");
        }
        const students = await response.json();

        studentDropdown.innerHTML = ""; // Clear existing options
        students.forEach(student => {
            const option = document.createElement("option");
            option.value = student.name;
            option.textContent = student.name;
            studentDropdown.appendChild(option);
        });
    } catch (error) {
        console.error("Error loading students:", error);
    }
}

async function populateCurrentStudentsList(classId, idToken) {
    const studentList = document.getElementById("student-list");
    const apiUrl = `https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/students/list`;

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                 'Authorization': `Bearer ${idToken}`
            },
            body: JSON.stringify({ classId }) // Send classId in the request body
        });
        
        if (!response.ok) {
            throw new Error("Failed to fetch student data");
        }
        
        const data = await response.json();
        const students = data.studentsList || [];
        
        // Clear and populate the student list
        studentList.innerHTML = ''; 
        
        students.forEach(student => {
            const li = document.createElement("li");
            li.className = "student-item";
            
            // Create a container for student name
            const nameSpan = document.createElement("span");
            nameSpan.textContent = student;
            nameSpan.className = "student-name";
            li.appendChild(nameSpan);
            
            // Create remove button
            const removeBtn = document.createElement("button");
            removeBtn.textContent = "Remove";
            removeBtn.className = "remove-btn";
            removeBtn.addEventListener("click", () => removeStudentFromClass(classId, student, idToken));
            li.appendChild(removeBtn);
            
            studentList.appendChild(li);
        });
    } catch (error) {
        console.error("Error fetching students list:", error);
        studentList.innerHTML = '<li>Failed to load students</li>';
    }
}

async function addStudentToClass(classId, idToken) {
    const studentDropdown = document.getElementById("studentEmail");
    const selectedStudent = studentDropdown.value;

    if (!selectedStudent) {
        alert("Please select a student.");
        return;
    }

    const apiUrl = "https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/students/add";

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                'Authorization': `Bearer ${idToken}`
            },
            body: JSON.stringify({
                student: selectedStudent,
                classId: classId  // Sending classId in the request body
            })
        });

        if (!response.ok) {
            throw new Error("Failed to add student to class.");
        }

        alert("Student added successfully!");
        
        // Refresh student list
        await populateCurrentStudentsList(classId, idToken);

    } catch (error) {
        console.error("Error adding student:", error);
    }
}

async function removeStudentFromClass(classId, studentName, idToken) {
    if (!confirm(`Are you sure you want to remove ${studentName} from this class?`)) {
        return;
    }
    
    const apiUrl = "https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/students/remove";

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                'Authorization': `Bearer ${idToken}`
            },
            body: JSON.stringify({
                student: studentName,
                classId: classId
            })
        });

        // Refresh student list
        await populateCurrentStudentsList(classId, idToken);
        
        alert("Student removed successfully!");

    } catch (error) {
        console.error("Error removing student:", error);
        alert("Failed to remove student. Please try again or contact support.");
    }
}

async function populateFacultyDropdown(idToken) {
    const facultyDropdown = document.getElementById("facultyEmail");
    const apiUrl = "https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/faculty";

    try {
        const response = await fetch(apiUrl, {
            headers: {
                'Authorization': `Bearer ${idToken}`,
                'Content-Type': 'application/json'
            },
        });
        if (!response.ok) {
            throw new Error("Failed to fetch faculty data");
        }
        const faculty = await response.json();

        facultyDropdown.innerHTML = ""; // Clear existing options
        faculty.forEach(facultyMember => {
            const option = document.createElement("option");
            option.value = facultyMember.name;
            option.textContent = facultyMember.name;
            facultyDropdown.appendChild(option);
        });
    } catch (error) {
        console.error("Error loading faculty:", error);
    }
}

async function populateCurrentFacultyList(classId, idToken) {
    const facultyList = document.getElementById("faculty-list");

    // Check if the faculty-list or members-count element exists
    if (!facultyList) {
        console.error("faculty-list element not found in the DOM");
        return;
    }

    const apiUrl = `https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/faculty/list`;

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                'Authorization': `Bearer ${idToken}`
            },
            body: JSON.stringify({ classId }) // Send classId in the request body
        });
        
        if (!response.ok) {
            throw new Error("Failed to fetch faculty data");
        }
        
        const data = await response.json();
        const facultyMembers = data.facultyList || [];
        
        // Clear and populate the faculty list
        facultyList.innerHTML = ''; 
        
        facultyMembers.forEach(faculty => {
            const li = document.createElement("li");
            li.className = "faculty-item";
            
            // Create a container for faculty name
            const nameSpan = document.createElement("span");
            nameSpan.textContent = faculty;
            nameSpan.className = "faculty-name";
            li.appendChild(nameSpan);
            
            // Create remove button
            const removeBtn = document.createElement("button");
            removeBtn.textContent = "Remove";
            removeBtn.className = "remove-btn";
            removeBtn.addEventListener("click", () => removeFacultyFromClass(classId, faculty, idToken));
            li.appendChild(removeBtn);
            
            facultyList.appendChild(li);
        });
    } catch (error) {
        console.error("Error fetching faculty list:", error);
        facultyList.innerHTML = '<li>Failed to load faculty members</li>';
    }
}

async function addFacultyToClass(classId, idToken) {
    const facultyDropdown = document.getElementById("facultyEmail");
    const selectedFaculty = facultyDropdown.value;

    if (!selectedFaculty) {
        alert("Please select a faculty member.");
        return;
    }

    const apiUrl = "https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/faculty/add";

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                 'Authorization': `Bearer ${idToken}`
            },
            body: JSON.stringify({
                faculty: selectedFaculty,
                classId: classId  // Sending classId in the request body
            })
        });

        if (!response.ok) {
            throw new Error("Failed to add faculty to class.");
        }

        alert("Faculty added successfully!");
        
        // Refresh faculty list
        await populateCurrentFacultyList(classId, idToken);

    } catch (error) {
        console.error("Error adding faculty:", error);
    }
}

async function removeFacultyFromClass(classId, facultyName, idToken) {
    if (!confirm(`Are you sure you want to remove ${facultyName} from this class?`)) {
        return;
    }
    
    const apiUrl = "https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/faculty/remove";

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                'Authorization': `Bearer ${idToken}`
            },
            body: JSON.stringify({
                faculty: facultyName,
                classId: classId
            })
        });

        // Refresh faculty list
        await populateCurrentFacultyList(classId, idToken);
        
        alert("Faculty removed successfully!");

    } catch (error) {
        console.error("Error removing faculty:", error);
        alert("Failed to remove faculty. Please try again or contact support.");
    }
}

async function deleteClass(classId, idToken) {
    const apiUrl = `https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/classes/deleteclass`;

    try {
        const response = await fetch(apiUrl, {
            method: 'POST', // Changed to POST
            headers: {
                'Authorization': `Bearer ${idToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ classId: classId }) // Send classId in the body
        });

        if (!response.ok) {
            throw new Error(`Failed to delete class, status: ${response.status}`);
        }

        return true; // Return true on success
    } catch (error) {
        console.error("Error deleting class:", error);
        return false; // Return false on failure
    }
}
