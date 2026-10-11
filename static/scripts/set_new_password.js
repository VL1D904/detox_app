const form = document.querySelector('form');
const button = document.getElementById('updatePassword');


button.addEventListener('click', (event) => {
    event.preventDefault();

    var empty = checkEmptyInputs();
    var passwords = checkPasswords();
    var safePassword = checkSafePassword();

    Promise.all([empty, passwords, safePassword])
    .then(() => {
        form.submit();
    })
})


async function checkEmptyInputs(){
    return new Promise((resolve, reject) => {
        var errors = document.querySelectorAll('.error');
        var inputs = document.querySelectorAll('input');  
        var isError = false;
        for (let i = 0; i < errors.length; i++){
            if (!inputs[i].value.trim()){
                errors[i].style.display = 'block';
                isError = true;
            }
            else{
                errors[i].style.display = 'none';
            }
        }
        if (isError){
            reject();
        }
        else{
            resolve();
        }
    })   
}


async function checkPasswords() {
    return new Promise((resolve, reject) => {
        var password = document.getElementById('password').value;
        var checkPassword = document.getElementById('checkPassword').value;
        var error = document.getElementById('checkPasswordError');
        if (password != checkPassword){
            error.style.display = 'block';
            reject();
        }
        else {
            error.style.display = 'none';
            resolve();
        }
    })
}


async function checkSafePassword() {
    return new Promise((resolve, reject) => {
        var error = document.getElementById('passwordSafeError')
        var password = document.getElementById('password').value
        if (password.length < 8){
            error.style.display = 'block';
            reject();
        }
        else{
            error.style.display = 'none';
            resolve();
        }
    })
} 