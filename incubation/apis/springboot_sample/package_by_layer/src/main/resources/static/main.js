
async function fetchGuess(inputText) {
    const url = `http://localhost:8080/guess/${encodeURIComponent(inputText)}`;
    
    try {
        console.log(`The guess was "${inputText}"\nFetching: ${url}`);
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.text();
        console.log('Response:', data);
        document.getElementById("result").textContent = data;
    } catch (error) {
        console.error('There was a problem with the fetch operation:', error);
        document.getElementById("result").textContent = 'An error occurred: ' + error.message;
    }
}

function addFormSumbitListener() {
    document.getElementById("guessForm").addEventListener("submit", async function(event) {
        event.preventDefault();
        
        const inputText = document.getElementById("inputText").value;
        
        await fetchGuess(inputText);
    });
}

addFormSumbitListener();
