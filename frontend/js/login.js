//LOGIN
const loginForm = document.getElementById('loginForm');
loginForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('loginEmail').value.trim();
  const password = document.getElementById('loginPassword').value;

  const response = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type':'application/json' },
    body: JSON.stringify({ email, password }),
    credentials: 'include'
  });

  const data = await response.json();
  if (response.ok) {
  window.location.href = 'index.html';
  } else {
    alert(data.error);
  }
});