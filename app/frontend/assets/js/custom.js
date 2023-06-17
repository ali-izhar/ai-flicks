let isTyping = false;

const formFields = {
    model: 'model_input',
    tsize: 'tshirtSelectedSize',
    tcolor: 'tshirtSelectedColor',
    hsize: 'hoodieSelectedSize',
    hcolor: 'hoodieSelectedColor',
};

const generateButton = document.getElementById('generate-button');
const message = document.getElementById('message-1');
const modelInput = document.getElementById('model_input');
const loaderOverlay = document.getElementById("loader-overlay");

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
            this.closest('.dropdown').querySelector('.dropdown-toggle').textContent = this.textContent;
        });
    });
});

$(document).ready(() => {
    $('.dropdown-item').on('click', function() {
        const text = $(this).text();
        const parentDropdown = $(this).closest('.dropdown');
        let dropdownType = parentDropdown[0].classList[1];
        let fieldName = dropdownType.split('-')[0];
        const productType = parentDropdown.closest('form').find('input[name="selectedProduct"]').val();
    
        if (productType === 'tshirt') {
            if (fieldName === 'size') fieldName = 'tsize';
            else if (fieldName === 'color') fieldName = 'tcolor';
        } else if (productType === 'hoodie') {
            if (fieldName === 'size') fieldName = 'hsize';
            else if (fieldName === 'color') fieldName = 'hcolor';
        }
    
        $('#' + formFields[fieldName]).val(text);
        parentDropdown.find('.dropdown-toggle').text(text);
    });          

    $('#generate-button').on('click', function() {
        if (message.value.trim() !== "") loaderOverlay.style.display = "flex";
    });
});