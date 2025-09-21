// Session check for navbar page using localStorage
function checkAuthentication() {
  const userSession = localStorage.getItem('userSession');
  const currentUser = localStorage.getItem('currentUser');
  
  if (!userSession || !currentUser) {
    window.location.href = 'login.html';
    return;
  }
  
  try {
    const session = JSON.parse(userSession);
    const user = JSON.parse(currentUser);
    
    // Check if session is expired
    if (session.exp && session.exp < Date.now() / 1000) {
      localStorage.removeItem('userSession');
      localStorage.removeItem('currentUser');
      window.location.href = 'login.html';
      return;
    }
    
    // Update navbar user info
    const userNameEl = document.getElementById('userName');
    const userRoleEl = document.getElementById('userRole');
    if (userNameEl) userNameEl.textContent = user.name;
    if (userRoleEl) userRoleEl.textContent = user.role || 'User';
    
  } catch (error) {
    console.error('Authentication error:', error);
    localStorage.removeItem('userSession');
    localStorage.removeItem('currentUser');
    window.location.href = 'login.html';
  }
}

// Run authentication check
checkAuthentication();
