document.addEventListener("DOMContentLoaded", () => {
    const messageInput = document.getElementById("messageInput");
    const sendButton = document.querySelector(".message-input button");
    const chatMessages = document.getElementById("chatMessages");
    const senderName = document.getElementById("senderName").value;

    // Load messages from server
    function loadMessages() {
        fetch("http://127.0.0.1:5000/community/messages")
            .then(res => res.json())
            .then(data => {
                chatMessages.innerHTML = ""; // Clear before reload
                data.forEach(msg => {
                    const isOutgoing = msg.sender_id === senderName;
                    const messageEl = document.createElement("div");
                    messageEl.classList.add("message", isOutgoing ? "outgoing" : "incoming");

                    const info = document.createElement("div");
                    info.classList.add("message-info");

                    const nameEl = document.createElement("strong");
                    nameEl.innerText = isOutgoing ? "You" : msg.sender_id;

                    const timeEl = document.createElement("span");
                    timeEl.classList.add("timestamp");
                    timeEl.innerText = new Date(msg.sent_at).toLocaleTimeString();

                    info.appendChild(nameEl);
                    info.appendChild(timeEl);

                    const textEl = document.createElement("p");
                    textEl.innerText = msg.message;

                    messageEl.appendChild(info);
                    messageEl.appendChild(textEl);
                    chatMessages.appendChild(messageEl);
                });

                chatMessages.scrollTop = chatMessages.scrollHeight; // Auto-scroll
            })
            .catch(err => console.error("Failed to load messages", err));
    }

    // Send message
    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        fetch("http://127.0.0.1:5000/community/send", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                sender: senderName,
                message: text
            })
        })
        .then(res => res.json())
        .then(data => {
            messageInput.value = "";
            loadMessages(); // Refresh chat after sending
        })
        .catch(err => console.error("Message failed to send", err));
    }

    // Send on click
    sendButton.addEventListener("click", sendMessage);

    // Send on Enter key
    messageInput.addEventListener("keypress", e => {
        if (e.key === "Enter") sendMessage();
    });

    // Initial load
    loadMessages();

    // Auto-refresh every 5s
    setInterval(loadMessages, 5000);
});
