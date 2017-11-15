function parseJsonResponse(jsonResponse) {
	var displayHtml = "";
	var messages = []
	for (var key in jsonResponse) {
		if (jsonResponse.hasOwnProperty(key)) {
			displayHtml = ("<p>"+jsonResponse[key]["sender"]+ ": "+jsonResponse[key]["text"]+"</p>");
			messages.push(displayHtml)
		}
	}
	displayHtml = "";
	while (messages.length > 0) {
		displayHtml += messages.pop();
	}
	return displayHtml;
}

window.onload = function() {
	
	var chatHistory = document.getElementById("history");
	var req = new XMLHttpRequest(); 
	
	var headerText = document.getElementById("header").innerHTML;
	req.open("GET", "/get_messages/"+headerText);
	req.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
	req.onreadystatechange = function() {
		if (req.readyState == 4) 
		{
			if (req.status != 200) 
			{
				//error handling code here
			} else {
				var response = JSON.parse(req.responseText);
				chatHistory.innerHTML = parseJsonResponse(response);
			}
		}
	}
	
	req.send();
	return false;
}