//REGISTER NEW USER
document.addEventListener('DOMContentLoaded', function() {
    const signupForm = document.getElementById("signupForm");
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const businessName = document.getElementById('businessName').value;
        const userName = document.getElementById('userName').value;
        const email = document.getElementById('signupEmail').value;
        const password = document.getElementById('signupPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        if (password !== confirmPassword) {
            alert('Passwords do not match');
            return;
        }

        try {
            const data = await API.apiCall('register', {
                method: 'POST',
                body: JSON.stringify({ 
                    name: userName,
                    organization: businessName, 
                    email, 
                    password
                })
            });

            if (data.success) {
                alert(data.message || 'Registration successful!');
                signupForm.reset();
                window.location.href = 'login.html';
            } else {
                throw new Error(data.error || 'Registration failed');
            }
        } catch (error) {
            console.error('Registration error:', error);
            alert('Registration failed: ' + error.message);
        }
    });
});