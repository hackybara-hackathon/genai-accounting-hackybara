//SIDE NAVIGATION BAR
function openNav() {
      document.getElementById("mySidenav").style.width = "220px";
    }

function closeNav() {
    document.getElementById("mySidenav").style.width = "0";
}

//LOGOUT
function logout() {
    // Clear user session or authentication tokens here
    window.location.href = "login.html"; // Redirect to login page
}