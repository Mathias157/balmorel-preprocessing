// Initial values
var output_type = ['countries', 'regions', 'areas'];
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
        let firstId = document.getElementById(window.to_be_connected[0])
        firstId.style.backgroundColor = 'rgb(185, 185, 185)';
        console.log(`Connection made between ${window.to_be_connected[1]} and ${this.parentNode.id}`)
        window.to_be_connected = [];
    }
}