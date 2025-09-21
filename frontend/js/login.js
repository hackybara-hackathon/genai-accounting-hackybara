//LOGIN using Lambda functions
const loginForm = document.getElementById('loginForm');
loginForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;

  try {
    const data = await API.apiCall('login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });

    // Store session data in localStorage
    localStorage.setItem('userSession', JSON.stringify(data.session));
    localStorage.setItem('currentUser', JSON.stringify(data.user));
    
    // Redirect to dashboard (layout folder is now served as root)
    window.location.href = 'index.html';
    
  } catch (error) {
    alert(error.message || 'Login failed');
  }
});