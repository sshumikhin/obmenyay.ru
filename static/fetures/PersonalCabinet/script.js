import { personal_things as originalPersonalThings } from '../../../static/data/personal_things.js';

let personal_things = JSON.parse(localStorage.getItem('personal_things')) || [...originalPersonalThings];

const initializeEventListeners = () => {
    const button = document.querySelector('.add_thing_button');
    if (button) {
        button.addEventListener('click', () => {
            addNewThing();
        });
    }


    const fileInput = document.getElementById('file_input');
    if (fileInput) {
        fileInput.addEventListener('change', previewImage);
    }
};

const previewImage = (event) => {
    const file = event.target.files[0];
    const imagePreview = document.getElementById('image_preview');
    const errorMessage = document.getElementById('error_message');

    errorMessage.textContent = '';

    if (file) {
        const reader = new FileReader();

        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';
        };

        reader.onerror = () => {
            errorMessage.textContent = 'Ошибка загрузки изображения.';
        };

        reader.readAsDataURL(file);
    } else {
        imagePreview.style.display = 'none';
    }
};

const addNewThing = () => {
    const thing_name = document.getElementById('thing_name').value.trim();
    const thing_desription = document.getElementById('thing_desription').value.trim();
    const form = document.getElementById('add_thing_form');
    const errorMessage = document.getElementById('error_message');
    const fileInput = document.getElementById('file_input');

    if (!thing_name || !thing_desription || !fileInput.files[0]) {
        alert('Пожалуйста, заполните все поля и выберите изображение.');
        return;
    }

    if (thing_name.length > 20) {
        errorMessage.textContent = 'Название не должно превышать 20 символов.';
        return;
    }

    const file = fileInput.files[0];
    const reader = new FileReader();

    reader.onload = (e) => {
        const newThing = {
            id: personal_things.length + 1,
            name: thing_name,
            description: thing_desription,
            image: e.target.result
        };

        personal_things.push(newThing);
        localStorage.setItem('personal_things', JSON.stringify(personal_things));
        console.log(personal_things);
        renderThings();
        window.myDialog.close();
        form.reset();
        document.getElementById('image_preview').style.display = 'none';
    };

    reader.onerror = () => {
        errorMessage.textContent = 'Ошибка загрузки изображения.';
    };

    reader.readAsDataURL(file);
};

document.querySelector('.close_modal').addEventListener('click', () => {
    const form = document.getElementById('add_thing_form');
    renderThings();
    window.myDialog.close();
    form.reset();
    document.getElementById('image_preview').style.display = 'none';
});

const deleteThing = (id) => {
    personal_things = personal_things.filter(thing => thing.id !== id);
    localStorage.setItem('personal_things', JSON.stringify(personal_things));
    console.log(personal_things);
    renderThings();
};
const highlightSelectedThings = () => {
    const selectedThings = JSON.parse(localStorage.getItem('selectedThings')) || [];
    const buttons = document.querySelectorAll('.button_trash');
    buttons.forEach(button => {
        const id = parseInt(button.dataset.id);
        console.log(button);
        if (selectedThings.includes(`${id}`)) {
            button.parentElement.classList.add('selected');
        }
    });
};
const renderThings = () => {
    const thingList = document.getElementById('thing_list');
    thingList.innerHTML = '';

    personal_things.forEach(thing => {
        const thingElement = document.createElement('button');
        thingElement.classList.add('button_container');
        thingElement.innerHTML = `
                            ${thing.name}
                <button class="button_trash" data-id="${thing.id}">
                    <img src="../../../static/icon/persobnalCabinet/trash.svg" alt="крестик">
                </button>
        `;
        thingList.appendChild(thingElement);
    });


    const trashButtons = document.querySelectorAll('.button_trash');
    trashButtons.forEach(button => {
        button.addEventListener('click', (event) => {
            const id = parseInt(event.target.closest('.button_trash').dataset.id);
            deleteThing(id);
        });
    });

    const button_container = document.querySelectorAll('.button_container');
    button_container.forEach(button => {
        button.addEventListener('click', (event) => {
            console.log(button);
            const id = parseInt(button.querySelector('.button_trash').dataset.id);
            let selectedThings = JSON.parse(localStorage.getItem('selectedThings')) || [];

            if (selectedThings.includes(`${id}`)) {
                selectedThings = selectedThings.filter(item => item !== `${id}`);
                button.classList.remove('selected');
            }
            localStorage.setItem('selectedThings', JSON.stringify(selectedThings));
        });
    });

    highlightSelectedThings();
};


initializeEventListeners();

renderThings();