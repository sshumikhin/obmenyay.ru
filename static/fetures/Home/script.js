import { things } from '../../data/things.js';

const cardContainer = document.getElementById('card_container');
let currentIndex = 0;

import { personal_things as originalPersonalThings } from '../../../static/data/personal_things.js';

let personal_things = JSON.parse(localStorage.getItem('personal_things')) || [...originalPersonalThings];

function renderThings() {
    if (currentIndex < things.length) {
        const thing = things[currentIndex];
        const card = document.createElement('div');
        card.setAttribute('name', 'thing_card_name');
        card.setAttribute('id', `card_${thing.id}`);
        card.classList.add('card');
        card.innerHTML = `
      <img src="${thing.img}" alt="thing_photo">
      <span>${thing.name}</span>
      <p>${thing.description}</p>
    `;
        cardContainer.appendChild(card);
    }
}

function removeCard() {
    const card = document.querySelector('.card');
    if (!card) return;

    card.classList.add('fade-out');

    card.addEventListener('transitionend', () => {
        cardContainer.removeChild(card);
        currentIndex++;
        if (currentIndex < things.length) {
            renderThings();
        } else {
            const message = document.createElement('div');
            message.textContent = 'Нет больше предметов для отображения.';
            cardContainer.appendChild(message);
        }
    });
}


const renderPersonalThings = () => {
    const thingList = document.getElementById('exchange_thing_list');
    thingList.innerHTML = '';

    if (personal_things.length === 0) {
        alert('Нет вещей для обмена.');
        return;
    }

    personal_things.forEach(thing => {
        const thingElement = document.createElement('div');
        thingElement.classList.add('button_container');
        thingElement.innerHTML = `
            <button type="button" data-id="${thing.id}" class="exchange_btn">
                ${thing.name}
            </button>
        `;
        thingList.appendChild(thingElement);
    });


    highlightSelectedThings();
};


const highlightSelectedThings = () => {
    const selectedThings = JSON.parse(localStorage.getItem('selectedThings')) || [];
    const buttons = document.querySelectorAll('#exchange_thing_list button');

    buttons.forEach(button => {
        const id = button.getAttribute('data-id');
        if (selectedThings.includes(id)) {
            button.classList.add('selected');
        }
    });
};

document.getElementById('exchange_thing_list').addEventListener('click', (event) => {
    if (event.target.tagName === 'BUTTON') {
        const button = event.target;
        const id = button.getAttribute('data-id');
        let selectedThings = JSON.parse(localStorage.getItem('selectedThings')) || [];

        if (selectedThings.includes(id)) {

            selectedThings = selectedThings.filter(item => item !== id);
            button.classList.remove('selected');
        } else {

            selectedThings.push(id);
            button.classList.add('selected');
        }

        localStorage.setItem('selectedThings', JSON.stringify(selectedThings));
    }
});

document.querySelector('.button_skip').addEventListener('click', () => {
    alert('Вы отменили предмет');
    removeCard('left');
});

document.querySelector('.button_trade').addEventListener('click', () => {
    const selectedThings = JSON.parse(localStorage.getItem('selectedThings')) || [];


    if (selectedThings.length === personal_things.length) {
        alert('Все вещи уже выбраны для обмена.');
        return;
    }

    renderPersonalThings();
    window.exchange_modal.showModal();
});

document.querySelector('.close_modal').addEventListener('click', () => {
    window.exchange_modal.close();
});

document.querySelector('.success_btn').addEventListener('click', () => {
    window.exchange_modal.close();
    removeCard('right');
});

renderThings();