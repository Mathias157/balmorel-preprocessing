function updateDisplay() {
    // Get input values
    const input1 = document.getElementById('input1').value;
    const input2 = document.getElementById('input2').value;
    const input3 = document.getElementById('input3').value;

    // Combine input values and split by commas
    const textPieces = (input1 + ',' + input2 + ',' + input3).split(',');

    // Get the output section
    const outputSection = document.getElementById('outputSection');
    outputSection.innerHTML = ''; // Clear existing content

    // Iterate over text pieces and create divs for each one
    textPieces.forEach(text => {
        if (text.trim()) {  // Ensure there's text after trimming whitespace
            const div = document.createElement('div');
            div.className = 'output-item';
            div.textContent = text.trim();
            outputSection.appendChild(div);
        }
    });
}