// Initial values
var output_type = ['countries', 'regions', 'areas'];
var consoleOutput = document.getElementById('consoleOutput');
window.to_be_connected = [];
updateDisplay()

function updateDisplay() {

    for (let i = 1; i <= 3; i++) {
        // Get input value
        let input = document.getElementById(`input${i}`).value;
        
        // Split by commas
        let text = input.split(',')
        
        // Get the output section
        let outputSection = document.getElementById(output_type[i-1]);
        outputSection.innerHTML = ''; // Clear existing content
        
        // Iterate over text pieces and create divs for each one
        text.forEach(element => {
            if (element.trim()) {  // Ensure there's text after trimming whitespace
                const div = document.createElement('div');
                div.className = 'output-item';
                div.id = element.trim().replace(/\s+/g, '_');
                div.textContent = element.trim().replace(/\s+/g, '_');
                outputSection.appendChild(div);
                div.style.backgroundColor = 'rgb(185, 185, 185)';

                // Add function
                div.addEventListener('click', click)
            }
        });
    }
}

// Add event listeners to inputs to trigger updateDisplay on every keystroke
for (let i = 1; i <= 3; i++) {
    document.getElementById(`input${i}`).addEventListener('input', updateDisplay);
}

function click() {
    if (window.to_be_connected.length === 0) {
        // If nothing selected, make this node active
        this.style.backgroundColor = 'rgb(153, 238, 154)';
        window.to_be_connected = [this.id, this.parentNode.id];
    } else if (window.to_be_connected[0] === this.id) {
        // If this node is selected, make it inactive 
        this.style.backgroundColor = 'rgb(185, 185, 185)';
        window.to_be_connected = [];
    } else {
        // Check if connection is valid
        let firstId = document.getElementById(window.to_be_connected[0]);
        let firstType = window.to_be_connected[1];
        let thisType = this.parentNode.id;
        if (firstType === thisType) {
            firstId.style.backgroundColor = 'rgb(185, 185, 185)';
            consoleOutput.innerHTML = `<br>Can't make connections between ${firstType} and ${thisType}<br>`;
            consoleOutput.style.color = 'red';
            window.to_be_connected = [];
        } else if ((firstType === 'countries' & thisType === 'areas') | (firstType === 'areas' & thisType === 'countries')) {
            firstId.style.backgroundColor = 'rgb(185, 185, 185)';
            consoleOutput.innerHTML = `<br>Can't make connections between countries and areas<br>`;
            consoleOutput.style.color = 'red';
            window.to_be_connected = [];
        } else {
            firstId.style.backgroundColor = 'rgb(185, 185, 185)';
            consoleOutput.innerHTML = `<br>Connection made!<br>`;
            consoleOutput.style.color = 'green';
            window.to_be_connected = [];
        }
    }
}