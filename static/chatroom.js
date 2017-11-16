function parseJsonResponse(jsonResponse, element) {
	var displayHtml = "";
	//var messages = []
	for (var key in jsonResponse) {
		if (jsonResponse.hasOwnProperty(key)) {
			displayHtml += ("<p>"+jsonResponse[key]["sender"]+ ": "+jsonResponse[key]["text"]+"</p>");
			//console.log(displayHtml);
			//messages.push(displayHtml);
		}
	}
	//displayHtml = "";
	//while (messages.length > 0) {
		//displayHtml += messages.pop();
	//}
	return displayHtml;
	/*for (var key in jsonResponse) {
		if (jsonResponse.hasOwnProperty(key)) {
			var pMessage = document.createElement("p");
			
		}
	}*/
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
				chatHistory.innerHTML = parseJsonResponse(response, chatHistory);
				chatHistory.scrollTop = chatHistory.scrollHeight;
			}
		}
	}
	
	req.send();
	return false;
}

function sendMessage(e) {
	var key = e.keyCode || e.which;
	if (key == 13) {
		txtArea = document.getElementById("typing")
		message = txtArea.value;
		txtArea.value = "";
		event.preventDefault();
		txtArea.focus();
		var req = new XMLHttpRequest();
		req.open("POST", "/post_message/");
		req.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
		req.onreadystatechange = function() {
			if (req.readyState == 4) 
			{
				if (req.status != 200) 
				{
					//error handling code here
				} else {
					var response = JSON.parse(req.responseText);
					console.log(response);
					var history = document.getElementById("history");
					var pNodes = history.innerText
					history.innerHTML = history.innerHTML + ("<p>"+response+": "+message+"</p>");
					history.scrollTop = history.scrollHeight;
				}
			}
		}
		var postVars = "chatroom="+document.getElementById("header").innerHTML+"&message="+message;
		req.send(postVars);
	}
}