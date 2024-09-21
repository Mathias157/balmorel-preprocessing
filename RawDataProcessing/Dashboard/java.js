function updateDisplay() {

    for (let i = 1; i <= 3; i++) {
        // Get input value
        let input = document.getElementById(`input${i}`).value;
        
        // Split by commas
        let text = input.split(',')
        
        // Get the output section
        let outputSection = document.getElementById(`outputSection${i}`);
        outputSection.innerHTML = ''; // Clear existing content
        
        // Iterate over text pieces and create divs for each one
        text.forEach(element => {
            if (element.trim()) {  // Ensure there's text after trimming whitespace
                const div = document.createElement('div');
                div.className = 'output-item';
                div.textContent = element.trim();
                outputSection.appendChild(div);
                div.style.backgroundColor = 'rgb(185, 185, 185)';

                // Add function
                div.addEventListener('click', click)
            }
        });
    }
}

function click() {
    if (this.style.backgroundColor === 'rgb(185, 185, 185)') {
        this.style.backgroundColor = 'rgb(153, 238, 154)';
    } else {
        this.style.backgroundColor = 'rgb(185, 185, 185)';
    }
}