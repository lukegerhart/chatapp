/*
Parse response from server into HTML for chat history
*/
function parseJsonResponse(jsonResponse) {
	var displayHtml = "";
	for (var key in jsonResponse) {
		if (jsonResponse.hasOwnProperty(key)) {
			displayHtml += ("<p>"+jsonResponse[key]["sender"]+ ": "+jsonResponse[key]["text"]+"</p>");
		}
	}
	return displayHtml;
	
}

/*
Get the entire history of chat messages
*/
function getMessages() {
	chatHistory = document.getElementById("history");
	var headerText = document.getElementById("header").innerHTML;
	
	var req = new XMLHttpRequest(); 
	req.open("GET", "/get_messages/"+headerText);
	req.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	req.onreadystatechange = function() {
		if (req.readyState == 4) 
		{
			if (req.status != 200) 
			{
				
			} else {
				try {
					var response = JSON.parse(req.responseText);
				} catch (SyntaxError) {
					//This response means that the room was deleted, redirect
					window.location.replace(req.responseText);
				}
				chatHistory.innerHTML = parseJsonResponse(response);
				chatHistory.scrollTop = chatHistory.scrollHeight;
			}
		}
	}
	
	req.send();
	return false;
}

/*
Set listener to load chat history when first entering a chatroom
*/
window.onload = getMessages;

/*
Function to send post a message to the server
*/
function sendMessage(e) {
	var key = e.keyCode || e.which;
	if (key == 13) {
		
		txtArea = document.getElementById("typing")
		message = txtArea.value;
		txtArea.value = "";
		e.preventDefault();
		txtArea.focus();
		
		var req = new XMLHttpRequest();
		req.open("POST", "/post_message/");
		req.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
		req.onreadystatechange = function() {
			if (req.readyState == 4) 
			{
				if (req.status != 200) 
				{
					
				} else {
					var response = JSON.parse(req.responseText);
					//add the message to the history on the bottom
					var history = document.getElementById("history");
					history.innerHTML = history.innerHTML + ("<p>"+response+": "+message+"</p>");
					history.scrollTop = history.scrollHeight;
				}
			}
		}
		var postVars = "chatroom="+document.getElementById("header").innerHTML+"&message="+message;
		req.send(postVars);
	}
}

/*
Poll the server every second for updates
*/
window.setInterval(getMessages, 1000);