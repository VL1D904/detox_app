// Основные компоненты главной страницы
const button = document.getElementById("sendMessage");
const input = document.getElementById("toxInput");
const helloElem = document.getElementById("hello");
const chat = document.getElementById("chatDetoxic");
const url = '/inference';
const scrollButton = document.getElementById('scrollButton');
const textLength = document.getElementById('textLength');

// Переменные и контроллер для взаимодействия с полем для ответа модели
var textField;
var spinBar;
var controller = new AbortController();
var stopAnimate = false;
export var stopDetox = false;

// Переменные кнопки прокрутки
var scrolled = false;
var scrollUp = true;


input.addEventListener('input', () => {
    textLength.textContent = `${input.value.length}/150 символов`;
    if (input.value.length === 150){
        textLength.style.color = 'red';
    }
    else {
        textLength.style.color = 'gray';
    }
})

scrollButton.addEventListener('click', () => {
    if (scrollUp){
        scrollUp = false;
        chat.scrollTop = 0;
        scrollButton.animate([{transform: "rotate(180deg)"}], {duration: 300, fill: 'forwards'});
    }
    else {
        scrollUp = true;
        chat.scrollTop = chat.scrollHeight;
        scrollButton.animate([{transform: "rotate(360deg)"}], {duration: 300, fill: 'forwards'});
    }
})


// Обратка нажатия на кнопку отправки
button.addEventListener('click', async () => {
    
    if (!stopDetox){
        if (input.value.trim()){
            var toxicText = {
                'task': 'detox',
                'text': input.value
            };
            changeDetoxicState();            

            // Вызов функции создания и добавления элемента сообщения
            await addUserMessage(input.value);

            // Сброс значения поля ввода
            input.value = "";
            textLength.textContent = `${input.value.length}/150 символов`;
            textLength.style.color = 'gray';

            // Вызов фунции создания и добавления элемента ответа
            await addModelAnswer();

            // Обращение к модели для получения детоксицированного текста
            fetch(url, {
                method: 'POST',
                signal: controller.signal,
                headers: {
                'Content-Type': 'application/json;charset=utf-8'
                },
                body: JSON.stringify(toxicText)
            })
                .then(response => {
                    if (response.ok) {
                        return response.json()
                    }
                    else {
                        throw new Error(`Server error ${response.status}`);
                    }
                })
                .then(jsonData => {
                    document.querySelector('.spinner').remove();
                    animateAnswer(jsonData['text']).then(() => {
                        switch (jsonData['source']) {
                            case 'model':
                                analizeText(jsonData['text'], toxicText['text']);
                                break;
                            case 'cache':
                                saveMessage();
                                changeDetoxicState();
                                showAnswerStatus("Ответ получен");
                                break;
                            default:
                                showAnswerStatus("Ошибка");
                                changeDetoxicState();
                        }
                    });
                })
                .catch(error => {
                    document.querySelector('.spinner').remove();
                    if (error.name != "AbortError"){
                        textField.textContent = "Произошла ошибка, повторите попытку позже";
                        showAnswerStatus("Ошибка");
                        changeDetoxicState();
                    }
                    else {
                        showAnswerStatus("Ответ прерван");
                        
                    }
                })
        }
    }
    else {
        
        changeDetoxicState();
        controller.abort();
        controller = new AbortController();
    }
});


export function changeDetoxicState(){
    if (!stopDetox) {
        // Смена секций
        helloElem.style.display = "none";
        chat.style.display = "flex";

        // Смена визуала кнопки
        button.textContent = '■';
        button.style.paddingBottom = '1.35em';

        // Смена логических состояний детоксикации и анимации
        stopDetox = true;
        stopAnimate = false;
    }
    else{
        // Смена логических состояний детоксикации и анимации
        stopAnimate = true;
        stopDetox = false;

        // Смена визуала кнопки
        button.textContent = "↑";
        button.style.paddingBottom = "0";
    }
}


export function showAnswerStatus(text){
    var answersStatus = document.querySelectorAll(".answerStatus");
    var lastAnswerStatus = answersStatus[answersStatus.length - 1];
    lastAnswerStatus.textContent = text;
}

// Функция анализа синтезированного текста на токсичность и смысловую схожесть
async function analizeText(detox, toxic){
    var modelAnswers = document.querySelectorAll(".modelAnswer");
    var lastModelAnswer = modelAnswers[modelAnswers.length - 1];
    spinBar = document.createElement('div');
    spinBar.className = "spinner";
    lastModelAnswer.append(spinBar);

    var stop = false;
    
    // Содержимое для запросов к модели
    var detoxic = {
        'task': 'classifier',
        'text': detox
    }
    var similarity = {
        'task': 'similarity',
        'toxicText': toxic,
        'detoxText': detox
    }
    var toxicClassifier, textsSimilarity;

    // Запрос к модели для классификации токсичности
    var classifierPromise = fetch(url, {
        method: 'POST',
        signal: controller.signal,
        headers: {
            'Content-Type': 'application/json;charset=utf-8'
        },
        body: JSON.stringify(detoxic)
    })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            else {
                throw new Error(`Server error ${response.status}`);
            }
        })
        .then(jsonData => {
            toxicClassifier = `\nТоксичность синтезированного сообщения: ${jsonData['percent']}%`;
        })
        .catch(error => {
            if (error.name === "AbortError"){
                stop = true;
            }
            else {
                throw error;
            }
        })

    // Запрос к модели для оценки смысловой схожести
    var similarityPromise = fetch(url, {
        method: 'POST',
        signal: controller.signal,
        headers: {
            'Content-Type': 'application/json;charset=utf-8'
        },
        body: JSON.stringify(similarity)
    })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            else {
                throw new Error(`Server error ${response.status}`);
            }
        })
        .then(jsonData => {
            textsSimilarity = `\nСмысловая схожесть: ${jsonData['percent']}%`;
        })
        .catch(error => {
            if (error.name === "AbortError"){
                stop = true;
            }
            else {
                throw error;
            }
        })

    // Отображение результатов от 2-х моделей
    Promise.all([classifierPromise, similarityPromise])
    .then(() => {
        animateAnswer(toxicClassifier + textsSimilarity).then(() => {
            saveMessage();
            changeDetoxicState();
            showAnswerStatus("Ответ получен");
        }).catch(() => {
            showAnswerStatus('Ответ прерван');          
        });  
    })
    .catch(() => {
        if (!stop){
            textField.textContent += "\nНе удалось получить токсичность и смысловую схожесть";
            showAnswerStatus('Ошибка'); 
            changeDetoxicState(); 
        }
        else{
            showAnswerStatus('Ответ прерван');  
        }
    })
}   
    

// Функция отображения блока пользовательского сообщения
export async function addUserMessage(text) {
    var userMessage = document.createElement("article");
    userMessage.className = "userMessage";
    var toxicText = document.createElement('pre');
    toxicText.className = 'toxicText';
    toxicText.textContent = text;
    userMessage.append(toxicText);
    chat.append(userMessage);

    // Прокрутка вниз
    chat.scrollTop = chat.scrollHeight;

    // Выпадающая кнопка прокрутки вверх\вниз
    if (chat.clientHeight < chat.scrollHeight && !scrolled){
        scrolled = true;
        scrollButton.animate([{opacity: 1, transform: "translateY(0)"}],
            {duration: 500, fill: "forwards"}
        );
    }
}


// Функция отображения блока ответа модели и переход в режим ожидания
export async function addModelAnswer() {
    // Блок ответа
    var modelMessage = document.createElement("article");
    modelMessage.className = "modelMessage";
    // Логотип
    var logo = document.createElement('img');
    logo.src = "/static/images/logo.png";
    modelMessage.append(logo);
    // Содержимое
    var modelAnswer = document.createElement('article');
    modelAnswer.className = "modelAnswer";
    var title = document.createElement('h5');
    title.textContent = "Детоксик";
    // Спинбар
    spinBar = document.createElement('div');
    spinBar.className = "spinner";
    // Поле ответа
    textField = document.createElement('pre');
    textField.className = "modelText";
    let answerStatus = document.createElement('span');
    answerStatus.className = 'answerStatus';
    // Добавление элементов
    modelAnswer.append(title);
    modelAnswer.append(spinBar);
    modelAnswer.append(textField);
    modelAnswer.append(answerStatus);
    modelMessage.append(modelAnswer);
    chat.append(modelMessage);

    // Прокрутка вниз
    chat.scrollTop = chat.scrollHeight;

    // Выпадающая кнопка прокрутки вверх\вниз
    if (chat.clientHeight < chat.scrollHeight && !scrolled){
        scrolled = true;
        scrollButton.animate([{opacity: 1, transform: "translateY(0)"}],
            {duration: 500, fill: "forwards"}
        );
    }
}


// Побуквенная анимация текста модели
export function animateAnswer(text) {
    return new Promise((resolve) => {
        spinBar.remove();
        let timeouts = []
        text.split('').forEach((element, index) => {
            let timeout = setTimeout(() => {
                textField.textContent += element;
                if (stopAnimate){
                    showAnswerStatus("Ответ прерван");
                    timeouts.forEach(clearTimeout);
                    return;
                }
                if (index === text.length - 1) {
                    resolve();
                }
            }, index * 100);
            timeouts.push(timeout);
        });
    })
}


async function saveMessage(){
    var url = '/save_detoxic_message';
    var userMessages = document.querySelectorAll('.toxicText');
    var lastUserMessagess = userMessages[userMessages.length - 1].textContent;
    var detoxic_context = textField.textContent

    if (button.dataset.user !== "None") {
        await insertMessage(lastUserMessagess, detoxic_context);
    }

    var data = {
        'toxic_context': lastUserMessagess,
        'detoxic_context': detoxic_context
    }
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json;charset=utf-8'
        },
        body: JSON.stringify(data)
    })
}


async function insertMessage(toxic_context, detoxic_context){
    const historyTitle = document.getElementById('historyTitle');

    var message = document.createElement("p");
    message.className = "messageHistory";
    message.textContent = toxic_context;
    message.dataset.answer = detoxic_context;
    historyTitle.after(message);
}
