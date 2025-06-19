document.addEventListener('DOMContentLoaded', () => {
    const resultContainer = document.getElementById('result-container');
    const form = document.getElementById('result-form');

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        const studentName = document.getElementById('student-name').value;
        const studentScore = document.getElementById('student-score').value;

        if (studentName && studentScore) {
            displayResult(studentName, studentScore);
            form.reset();
        } else {
            alert('Please enter both name and score.');
        }
    });

    function displayResult(name, score) {
        const resultElement = document.createElement('div');
        resultElement.classList.add('result');
        resultElement.textContent = `${name}: ${score}`;
        resultContainer.appendChild(resultElement);
    }
});