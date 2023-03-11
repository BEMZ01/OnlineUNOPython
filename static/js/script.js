// https://kinsta.com/knowledgebase/javascript-http-request/
// Frontend script to update the HTML of the page depending on the state of the game.
// This script should be called every second to update the page.

// Get the current state of the game
var request = new XMLHttpRequest();
request.open('GET', 'http://localhost:8080/game', true);