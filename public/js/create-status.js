document.addEventListener('DOMContentLoaded', function () {
    const createStatusBtn = document.getElementById('createStatusBtn');

    if (createStatusBtn) {
        createStatusBtn.addEventListener('click', function () {
            showStatusModal();
        });
    }

    function showStatusModal() {
        const modal = document.createElement('div');
        modal.className = 'modal';

        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>New Check-in Status</h2>
                </div>
                <form id="statusForm">
                    <div class="form-group">
                        <label for="newStatus">Status Name</label>
                        <input type="text" id="newStatus" name="newStatus" placeholder="e.g., Safe, In Transit" required />
                    </div>
                    <div class="modal-buttons">
                        <button type="submit">Save</button>
                        <button type="button" class="cancel">Cancel</button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);

        const form = modal.querySelector('#statusForm');
        const input = modal.querySelector('#newStatus');

        form.addEventListener('submit', async function (e) {
            e.preventDefault();

            const newStatus = input.value.trim();
            const facultyName = localStorage.getItem('name');

            if (!newStatus || !facultyName) {
                alert('Invalid input. Please ensure you\'re logged in and the status is not empty.');
                return;
            }

            try {
                const res = await fetch("https://cso6luevsi.execute-api.us-east-1.amazonaws.com/prod/faculty/create-status", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        facultyName,
                        status: newStatus
                    })
                });

                if (!res.ok) throw new Error(`Request failed: ${res.status}`);
                alert("Status added successfully!");
            } catch (err) {
                console.error("Error creating status:", err);
                alert("Something went wrong. Please try again later.");
            }

            document.body.removeChild(modal);
        });

        modal.querySelector('.cancel').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        input.focus();
    }
});