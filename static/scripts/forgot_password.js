const resetButton = document.getElementById('resetPassword');
const emailField = document.getElementById('email');
const emailError = document.getElementById('emailError');
const form = document.querySelector('form');


resetButton.addEventListener('click', (event) => {
    event.preventDefault();
    if (emailField.value.trim()) {
        form.submit();
    }
    else{
        emailError.style.display = 'block';
    }
})