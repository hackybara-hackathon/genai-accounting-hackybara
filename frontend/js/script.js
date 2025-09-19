//AUTHENTICATION - LOAD CURRENT USER AND ORGANIZATION NAME
document.addEventListener('DOMContentLoaded', () => {
  loadCurrentUser();
  document.getElementById('logoutBtn').addEventListener('click', logout);
});

async function loadCurrentUser() {
  try {
    const response = await fetch('/api/auth/current', { credentials: 'include' });
    if (!response.ok) {
      window.location.href = 'login.html';
      return null;
    }
    const data = await response.json();
    document.getElementById('userName').textContent = data.user.name;
    //document.getElementById('userNameInput').value = data.user.name;
    document.getElementById('organizationName').textContent = data.user.organization_name;
    document.getElementById('userRole').textContent = data.user.role;
  } catch (err) {
    console.error(err);
    window.location.href = 'login.html';
  }
}

async function logout() {
  try {
    await fetch('/api/logout', { method: 'POST', credentials: 'include' });
    window.location.href = 'login.html';
  } catch (err) {
    console.error(err);
    window.location.href = 'login.html';
  }
}


//SIDE NAVIGATION BAR
function openNav() {
      document.getElementById("mySidenav").style.width = "220px";
    }

function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
}

// Fetch and display all users in a table
async function loadUsers() {
  try {
    const response = await fetch('/api/settings/user', { credentials: 'include' });
    const users = await response.json();

    const userTableBody = document.getElementById("userTableBody");
    userTableBody.innerHTML = ""; // Clear existing rows

    users.forEach(user => {
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

// Delete user
async function deleteUser(id) {
  await fetch(`/api/users/${id}`, { method: 'DELETE' });
  loadUsers();
}

// Edit user
async function editUser(id, currentName, currentEmail) {
  const name = prompt("Edit name:", currentName);
  const email = prompt("Edit email:", currentEmail);

  if (name && email) {
    await fetch(`/api/users/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email })
    });
    loadUsers();
  }
}


// Create user
document.getElementById("userForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const name = document.getElementById("name").value;
  const email = document.getElementById("email").value;

  await fetch('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email })
  });

  document.getElementById("userForm").reset();
  loadUsers();
}); 

// Load users on page load
window.onload = loadUsers;
