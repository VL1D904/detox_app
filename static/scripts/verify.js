const timer = document.getElementById('timer');
const resendButton = document.getElementById('resend');
const form = document.querySelector('form')

const email = form.dataset.email;

var timeout = false;

async function updateTimer() {
    var time = parseInt(timer.textContent);

    function tick(){
        if (time){
            time--;
            timer.textContent = time.toString().padStart(2, 0)
            setTimeout(tick, 1000)
        }
        else {
            resendButton.style.cursor = 'pointer';
            resendButton.style.color = 'rgb(69, 69, 69)';
            timeout = true;
        }
    }

    tick();
}


resendButton.addEventListener('click', () => {
    if (timeout) {
        var url = "/set_message";
        fetch(url, {
            method: 'POST',
            headers: {
                "Content-Type": 'application/json;charset=utf-8'
            },
            body: JSON.stringify({'email': email})
        })
        .then(response => {
            if (response.ok){
                timer.textContent = '59';
                timeout = false;
                resendButton.style.cursor = 'auto';
                resendButton.style.color = 'gray';
            }
        })
    }
});

updateTimer();