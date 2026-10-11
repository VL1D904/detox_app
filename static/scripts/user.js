const logoutButton = document.getElementById('logout');
const usernameField = document.getElementById('username');

var logoutShow = false;

usernameField.addEventListener('click', () => {
    if (!logoutShow){
        logoutButton.style.display = 'block';
        logoutShow = true;
    }
    else {
        logoutButton.style.display = 'none';
        logoutShow = false;
    }
});