const classToSubjects = {
    'Mont': ['English', 'Math'],
    'Mont-Adv': ['English', 'Math', 'Science'],
    'KG': ['English', 'Math'],
    '1': ['English', 'Math', 'Science'],
    '2': ['English', 'Math', 'Science'],
    '3': ['English', 'Math', 'Science'],
    '4': ['English', 'Math', 'Science'],
    '5': ['English', 'Math', 'Science'],
    '6': ['English', 'Math', 'Science'],
    '7': ['English', 'Math', 'Science'],
    '8': ['English', 'Math', 'Science'],
    '9': ['Physics', 'Math'],
    '10': ['Physics', 'Math'],
    '11': ['Physics', 'Math'],
    '12': ['Physics', 'Math']
};

document.addEventListener('DOMContentLoaded', () => {
    const classSelect = document.querySelector('select[name="cls"]');
    const subjectContainer = document.querySelector('#subject-fields');

    classSelect.addEventListener('change', () => {
        const selectedClass = classSelect.value;
        subjectContainer.innerHTML = '';

        if (classToSubjects[selectedClass]) {
            classToSubjects[selectedClass].forEach(subject => {
                const fieldHTML = `
                    <div>
                        <label class="block">${subject}</label>
                        <input type="number" name="marks_${subject}" class="border w-full px-4 py-2 rounded" min="0" max="100">
                    </div>`;
                subjectContainer.innerHTML += fieldHTML;
            });
        }
    });
});