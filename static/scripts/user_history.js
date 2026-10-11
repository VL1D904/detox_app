import { stopDetox,
        addUserMessage, addModelAnswer, animateAnswer,
        changeDetoxicState, showAnswerStatus} from './detox.js';


const historySection = document.querySelector('.history');


historySection.addEventListener('click', (event) => {
    var target = event.target;
    var detoxic_context;
    if (target.className != "messageHistory"){
        return;
    }
    if (stopDetox){
        return;
    }
    var toxic_context = target.textContent;
    changeDetoxicState();
    addUserMessage(toxic_context);
    addModelAnswer();
    detoxic_context = target.dataset.answer;
    animateAnswer(detoxic_context).then(() => {
        changeDetoxicState();
        showAnswerStatus('Ответ получен');
    })
})


historySection.addEventListener('scroll', () => {
    if (historySection.scrollTop + historySection.clientHeight >= historySection.scrollHeight){
        loadMessages();
    }
})


function loadMessages(){
    var messages = document.querySelectorAll('.messageHistory');
    console.log(messages.length);
    console.log(messages)
    if (messages.length) {
        var date = messages[messages.length - 1].dataset.date;
        console.log(date)

        var url = `/load_messages?date=${date}`;
    }
    else{
        url = `/load_messages`;
    }

    fetch(url, {
        method: 'GET',
    })
    .then((response) => {
        if (response.ok){
            return response.json();
        }
        else{
            throw new Error(`server error ${response.status}`);
        }
    })
    .then((jsonMessages) => {
        showMessages(jsonMessages['messages']);
    })
    .catch((error) => {
        alert(error);
    }); 
}

function showMessages(messages){
    messages.forEach((message) => {
        var messageElement = document.createElement('p');
        messageElement.className = "messageHistory";
        messageElement.textContent = message['toxic_message'];
        messageElement.dataset.answer = message['detoxic_message'];
        messageElement.dataset.date = message['date'];
        historySection.append(messageElement);
    });
}


loadMessages();