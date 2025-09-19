//REGISTER NEW USER
const signupForm = document.getElementById("signupForm");
signupForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const businessName = document.getElementById('businessName').value;
  const userName = document.getElementById('userName').value;
  const email = document.getElementById('signupEmail').value;
  const password = document.getElementById('signupPassword').value;
  const confirmPassword = document.getElementById('confirmPassword').value;

  const response = await fetch('/api/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ businessName, userName, email, password, confirmPassword })
  });

  const data = await response.json();
  if (response.ok) {
    alert(data.message);
    signupForm.reset();
    window.location.href = 'login.html';
  } else {
    alert(data.error);
  }
});