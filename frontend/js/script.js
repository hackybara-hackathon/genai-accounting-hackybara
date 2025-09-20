//SIMPLIFIED USER MANAGEMENT - NO AUTHENTICATION FOR MVP
document.addEventListener('DOMContentLoaded', () => {
  loadMockUser();
});

function loadMockUser() {
  // For MVP, use mock user data - replace with real auth later
  const mockUser = {
    name: 'Demo User',
    organization_name: 'Demo Organization',
    role: 'Admin'
  };
  
  // Safely update user info if elements exist
  const userNameEl = document.getElementById('userName');
  const orgNameEl = document.getElementById('organizationName');
  const userRoleEl = document.getElementById('userRole');
  
  if (userNameEl) userNameEl.textContent = mockUser.name;
  if (orgNameEl) orgNameEl.textContent = mockUser.organization_name;
  if (userRoleEl) userRoleEl.textContent = mockUser.role;
}

function logout() {
  // For MVP, just show alert - implement real logout later
  if (confirm('Are you sure you want to logout?')) {
    alert('Logout functionality will be implemented in next version');
    // window.location.href = 'login.html';
  }
}


//SIDE NAVIGATION BAR
function openNav() {
      document.getElementById("mySidenav").style.width = "220px";
    }

function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
}

// MOCK USER MANAGEMENT FOR MVP - Replace with real API calls later
async function loadUsers() {
  try {
    const userTableBody = document.getElementById("userTableBody");
    if (!userTableBody) return;

    // Mock users data for MVP
    const mockUsers = [
      { id: '1', name: 'Demo User', email: 'demo@example.com', role: 'Admin' },
      { id: '2', name: 'Test User', email: 'test@example.com', role: 'User' }
    ];

    userTableBody.innerHTML = ""; // Clear existing rows

    mockUsers.forEach(user => {
      const tr = document.createElement("tr");
      tr.classList.add("border-b", "border-gray-200", "hover:bg-gray-50");

      tr.innerHTML = `
        <td class="p-3">${user.name}</td>
        <td class="p-3">${user.email}</td>
        <td class="p-3">${user.role}</td>
        <td class="p-3 text-center">
            <button class="text-blue-600 hover:text-blue-900 mr-2" onclick="editUser('${user.id}', '${user.name}', '${user.email}')">
                <span class="material-symbols-outlined text-sm">edit</span>
            </button>
            <button class="text-red-600 hover:text-red-900" onclick="deleteUser('${user.id}')">
                <span class="material-symbols-outlined text-sm">delete</span>
            </button>
        </td>
      `;

      userTableBody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading users:", err);
  }
}

// Mock delete user - show alert for MVP
function deleteUser(id) {
  if (confirm('Delete user functionality will be implemented in next version. Continue?')) {
    alert('User would be deleted in full version');
    // For MVP, just reload to show same data
    loadUsers();
  }
}

// Mock edit user - show alert for MVP
function editUser(id, currentName, currentEmail) {
  alert('Edit user functionality will be implemented in next version');
}

// Mock create user - show alert for MVP
if (document.getElementById("userForm")) {
  document.getElementById("userForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    alert('Create user functionality will be implemented in next version');
    document.getElementById("userForm").reset();
  });
}

// Initialize mock data on page load
document.addEventListener('DOMContentLoaded', loadUsers);
