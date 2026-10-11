const form = document.querySelector('form');
const button = document.getElementById('signUpButton');


button.addEventListener('click', (event) => {
    event.preventDefault();

    var empty = checkEmptyInputs();
    var passwords = checkPasswords();
    var safePassword = checkSafePassword();
    var loginExist = checkLogin();
    var emailExist = checkEmail();
    var systemLogin = checkSystemLogin();

    Promise.all([empty, passwords, safePassword, loginExist, emailExist, systemLogin])
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


async function checkLogin() {
    return new Promise((resolve, reject) => {
        var login = document.getElementById("login").value;
        var error = document.getElementById("loginExist");
        const url = `/check_login?login=${login}`;
        if (login.trim()){
            fetch(url, {
                method: 'GET',
            })
            .then(response => {
                if (response.ok){
                    return response.text();
                }
                else {
                    throw new Error(`Server error ${response.status}`)
                }
            })
            .then((answer) => {
                switch (answer){
                    case 'Логин существует':
                        error.style.display = 'block';
                        break;
                    case "Логин не существует":
                        error.style.display = 'none';
                        break;
                }
            })
            .catch((error) => {
                alert(error);
            });
        }
        else{
            reject();
        }
    })
}


async function checkEmail() {
    return new Promise((resolve, reject) => {
        var email = document.getElementById("email").value;
        var error = document.getElementById("emailExist");
        const url = `/check_email?email=${email}`;
        if (email.trim()){
            fetch(url, {
                method: 'GET',
            })
            .then(response => {
                    if (response.ok){
                        return response.text();
                    }
                    else {
                        throw new Error(`Server error ${response.status}`)
                    }
                })
            .then((answer) => {
                switch (answer){
                    case 'Почта существует':
                        error.style.display = 'block';
                        break;
                    case "Почты не существует":
                        error.style.display = 'none';
                        break;
                }
            })
            .catch((error) => {
                alert(error);
            });
        }
        else{
            reject();
        }
    })
}


async function checkSystemLogin() {
    return new Promise((resolve, reject) => {
        var login = document.getElementById("login").value;
        var error = document.getElementById('systemLogin');
        var is_error = false;
        systemPrefix = ['google_', 'yandex_', 'github_'];
        for (let index = 0; index < systemPrefix.length && !is_error; index++){
            if (login.startsWith(systemPrefix[index])){
                is_error = true;
                break;
            }
        }
        if (is_error){
            error.style.display = 'block';
            reject();
        }
        else{
            error.style.display = 'none';
            resolve()
        }
    })
}