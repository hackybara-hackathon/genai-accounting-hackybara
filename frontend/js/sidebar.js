// Authentication is handled by navbar.js, so no need to check here
// Update sidebar business name from localStorage
const userSession = localStorage.getItem('userSession');
const currentUser = localStorage.getItem('currentUser');
if (userSession && currentUser) {
    try {
        const user = JSON.parse(currentUser);
        const orgNameEl = document.getElementById('organizationName');
        if (orgNameEl) orgNameEl.textContent = user.organization_name || 'My Business';
    } catch (error) {
        console.error('Error loading user data:', error);
    }
}
