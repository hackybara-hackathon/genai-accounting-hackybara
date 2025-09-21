//LOGIN using Lambda functions
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('loginEmail').value.trim();
            const password = document.getElementById('loginPassword').value;
            
            console.log('Attempting login with:', email);
            
            try {
                // Show loading state
                const submitButton = e.target.querySelector('button[type="submit"]');
                const originalText = submitButton.textContent;
                submitButton.textContent = 'Logging in...';
                submitButton.disabled = true;
                
                // Make direct fetch call for better error handling
                const response = await fetch(API.getEndpoint('login'), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ email, password })
                });
                
                console.log('Login response status:', response.status);
                console.log('Login response headers:', [...response.headers.entries()]);
                
                const responseText = await response.text();
                console.log('Login response text:', responseText);
                
                if (!response.ok) {
                    throw new Error(`Login failed: ${response.status} - ${responseText}`);
                }
                
                const data = JSON.parse(responseText);
                
                // Store session data in localStorage
                localStorage.setItem('userSession', JSON.stringify(data.session));
                localStorage.setItem('currentUser', JSON.stringify(data.user));
                
                console.log('Login successful, redirecting...');
                
                // Redirect to dashboard
                window.location.href = 'index.html';
                
            } catch (error) {
                console.error('Login error:', error);
                
                // Reset button
                const submitButton = e.target.querySelector('button[type="submit"]');
                submitButton.textContent = 'Login to Account';
                submitButton.disabled = false;
                
                // Show error message
                alert(`Login failed: ${error.message}`);
            }
        });
    } else {
        console.error('Login form not found!');
    }
});