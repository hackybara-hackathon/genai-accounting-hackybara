// Session check for settings page
fetch('/api/auth/current', { credentials: 'include' })
  .then(res => res.json())
  .then(data => {
    if (!data.user) {
      window.location.href = 'login.html';
    }
    // Optionally, update UI with user info
  })
  .catch(() => {
    window.location.href = 'login.html';
  });
