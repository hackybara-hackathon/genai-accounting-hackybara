// Session check for sidebar_mobile page
fetch('/api/auth/current', { credentials: 'include' })
  .then(res => res.json())
  .then(data => {
    if (!data.user) {
      window.location.href = 'login.html';
    }
  })
  .catch(() => {
    window.location.href = 'login.html';
  });
