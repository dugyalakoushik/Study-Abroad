// Time frame for active groups (in milliseconds) - 1 month
/*export const ACTIVE_THRESHOLD = 30 * 24 * 60 * 60 * 1000;

// Function to populate groups with initial 3 visible
export function populateGroups(currentGroups, previousGroups, handleCardClick) {
    const currentGroupsContainer = document.querySelector('.current-groups');
    const previousGroupsContainer = document.querySelector('.previous-groups');

    // Clear existing content
    currentGroupsContainer.innerHTML = '';
    previousGroupsContainer.innerHTML = '';

    // Function to append groups to a container
    function appendGroups(groups, container) {
        groups.forEach((group, index) => {
            const card = createCard(group, handleCardClick);

            // Hide groups after first 3
            if (index >= 3) {
                card.classList.add('row-hidden');
            }

            container.appendChild(card);
        });
    }

    // Add current groups (initially first 3)
    appendGroups(currentGroups, currentGroupsContainer);

    // Add previous groups (initially first 3)
    appendGroups(previousGroups, previousGroupsContainer);

    //  Visibility of "See All" buttons
    const currentSeeAllBtn = document.querySelector('.see-all-btn[data-section="current"]');
    const previousSeeAllBtn = document.querySelector('.see-all-btn[data-section="previous"]');

    currentSeeAllBtn.classList.toggle('hidden', currentGroups.length <= 3);
    previousSeeAllBtn.classList.toggle('hidden', previousGroups.length <= 3);
}

// Function to create a card element
function createCard(group, handleCardClick) {
    const card = document.createElement('div');
    card.className = 'card';
    card.setAttribute('data-id', group.classId); // Changed to classId

    card.innerHTML = `
        <h3>${group.name}</h3>
        <div class="card-info">
            <p>Members: <span>${group.members}</span></p>
            <p>Faculty: <span>${group.faculty}</span></p>
            <p>Last Active: <span>${group.lastActive}</span></p>
        </div>
    `;

    card.addEventListener('click', () => handleCardClick(group));

    return card;
}

// Setup see all buttons functionality
export function setupSeeAllButtons() {
    const seeAllButtons = document.querySelectorAll('.see-all-btn');

    seeAllButtons.forEach(button => {
        button.addEventListener('click', () => {
            const section = button.getAttribute('data-section');
            const container = document.querySelector(`.${section}-groups`);
            const hiddenCards = container.querySelectorAll('.row-hidden');

            // Show all hidden cards
            hiddenCards.forEach(card => {
                card.classList.remove('row-hidden');
            });

            // Hide the "See All" button after it's clicked
            button.classList.add('hidden');
        });
    });
}

// Setup create group button functionality
export function setupCreateGroupButton(showAddClassModal) {
    const createGroupBtn = document.querySelector('.create-group-btn');

    if (createGroupBtn) {
        createGroupBtn.addEventListener('click', () => {
            showAddClassModal();
        });
    }
}
*/