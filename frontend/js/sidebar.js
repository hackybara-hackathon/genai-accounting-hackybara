// Session check for sidebar page
fetch('/api/auth/current', { credentials: 'include' })
  .then(res => res.json())
  .then(data => {
    if (!data.user) {
      window.location.href = 'login.html';
    }
    // Update sidebar business name
    const orgNameEl = document.getElementById('organizationName');
    if (orgNameEl) orgNameEl.textContent = data.user.organization_name;
  })
  .catch(() => {
    window.location.href = 'login.html';
  });
