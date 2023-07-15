window.addEventListener('pageshow', (event) => {
    // If the page was loaded from the cache
    if(event.persisted) {
        // Hide the loader
        document.getElementById('loader-overlay').style.display = 'none';
    }
});


let isTyping = false;

const formFields = {
    model: 'model_input'
};

const generateButton = document.getElementById('generate-button');
const message = document.getElementById('message-1');
const modelInput = document.getElementById('model_input');
const loaderOverlay = document.getElementById("loader-overlay");
const promptForm = document.getElementById('prompt_form');

function selectItem(fieldName, itemName) {
    updateHiddenField(fieldName, itemName);
    updateButtonText(fieldName, itemName);
}

function updateHiddenField(fieldName, itemName) {
    document.getElementById(formFields[fieldName]).value = itemName;
}

function updateButtonText(fieldName, itemName) {
    let button = document.querySelector(`.${fieldName}-dropdown .dropdown-toggle`);
    let updatedText = itemName.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase());
    button.innerText = updatedText;
}

function toggleGenerateButton(state) {
    generateButton.disabled = state;
}

function typeWriter(text, elementId, delay = 100) {
    if (!text.length) {
        isTyping = false;
        toggleGenerateButton(false);
        return;
    }
    message.value += text.charAt(0);
    text = text.slice(1);
    setTimeout(() => typeWriter(text, elementId, delay), delay);
}

function generateRandomPrompt() {
    if (isTyping) return;
    const selectedModel = modelInput.value;
    toggleGenerateButton(true);
    fetch(`/random-prompt?model=${selectedModel}`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        message.value = '';
        console.log(data.prompt)
        isTyping = true;
        typeWriter(data.prompt, 'message-1', 20);
    })
    .catch(error => {
        console.error('Error:', error);
        toggleGenerateButton(false);
    });
}

window.onload = () => {
    generateButton.addEventListener('click', function() {
        if (message.value.trim() !== "") loaderOverlay.style.display = "flex";
    });
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.dropdown-menu .dropdown-item').forEach((item) => {
        item.addEventListener('click', (e) => {
            e.target.closest('.dropdown').querySelector('.dropdown-toggle').textContent = e.target.textContent;
        });
    });
});