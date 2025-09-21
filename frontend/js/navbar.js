// Session check for navbar page
fetch('/api/auth/current', { credentials: 'include' })
  .then(res => res.json())
  .then(data => {
    if (!data.user) {
      window.location.href = 'login.html';
    }
  // Update navbar user info
  const userNameEl = document.getElementById('userName');
  const userRoleEl = document.getElementById('userRole');
    userNameEl.textContent = data.user.name;
    userRoleEl.textContent = data.user.role;
  })
  .catch(() => {
    window.location.href = 'login.html';
  });
