// 📥 DOM Content Loaded Handler
window.addEventListener("DOMContentLoaded", function () {
    // 🌙 Light/Dark Mode Toggle
    const themeToggle = document.getElementById("theme-toggle");
    if (themeToggle) {
        themeToggle.addEventListener("click", function () {
            document.body.classList.toggle("dark-mode");
            const isDark = document.body.classList.contains("dark-mode");
            localStorage.setItem("theme", isDark ? "dark" : "light");
        });

        if (localStorage.getItem("theme") === "dark") {
            document.body.classList.add("dark-mode");
        }
    }

    // 📸 Profile Picture Upload
    const pictureInput = document.getElementById("upload-picture");
    if (pictureInput) {
        pictureInput.addEventListener("change", function () {
            const file = this.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append("profile_picture", file);

            fetch("http://127.0.0.1:5000/client/upload_picture", {
                method: "POST",
                headers: {
                    "Authorization": "Bearer " + localStorage.getItem("token")
                },
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    const profilePic = document.getElementById("profile-pic");
                    if (profilePic && data.picture_url) {
                        profilePic.src = data.picture_url;
                    }
                })
                .catch(error => console.error("Error uploading picture:", error));
        });
    }

    // 🧾 Downloadable Receipt
    const paymentHistory = document.getElementById("payment-history");
    if (paymentHistory) {
        paymentHistory.addEventListener("click", function (event) {
            const target = event.target;
            if (target.classList.contains("download-receipt")) {
                const paymentId = target.getAttribute("data-id");
                if (paymentId) {
                    window.open(`http://127.0.0.1:5000/client/download_receipt/${paymentId}`, "_blank");
                }
            }
        });
    }

    // 📦 Display Payment History
    window.displayPaymentHistory = function (payments) {
        const paymentHistory = document.getElementById("payment-history");
        if (!paymentHistory) return;
        paymentHistory.innerHTML = "";
        payments.forEach(payment => {
            const paymentItem = document.createElement("li");
            paymentItem.innerHTML = `
                Property: ${payment.property_name}, Amount: $${payment.amount}, Date: ${payment.date}
                <button class="download-receipt" data-id="${payment.id}">Download Receipt</button>
            `;
            paymentHistory.appendChild(paymentItem);
        });
    };

    // 🧮 Dashboard Summary Cards
    function fetchDashboardSummary() {
        fetch("http://127.0.0.1:5000/client/dashboard_summary", {
            headers: {
                "Authorization": "Bearer " + localStorage.getItem("token")
            }
        })
            .then(response => response.json())
            .then(data => {
                const total = document.getElementById("total-properties");
                const pending = document.getElementById("pending-payments");
                const completed = document.getElementById("completed-payments");
                if (total) total.textContent = data.total_properties;
                if (pending) pending.textContent = data.pending_payments;
                if (completed) completed.textContent = data.completed_payments;
            })
            .catch(error => console.error("Error fetching dashboard summary:", error));
    }

    // 📬 Fetch Upcoming Payment Reminders
    function fetchReminders() {
        fetch("http://127.0.0.1:5000/client/reminders", {
            headers: {
                "Authorization": "Bearer " + localStorage.getItem("token")
            }
        })
            .then(response => response.json())
            .then(data => {
                const reminderList = document.getElementById("reminder-list");
                if (!reminderList) return;
                reminderList.innerHTML = "";
                data.forEach(reminder => {
                    const item = document.createElement("li");
                    item.textContent = `Upcoming payment for ${reminder.property_name} due on ${reminder.due_date}`;
                    reminderList.appendChild(item);
                });
            })
            .catch(error => console.error("Error fetching reminders:", error));
    }

    // 💬 Support Chat
    const chatForm = document.getElementById("chat-form");
    if (chatForm) {
        chatForm.addEventListener("submit", function (event) {
            event.preventDefault();
            const messageInput = document.getElementById("chat-message");
            if (!messageInput) return;
            const message = messageInput.value.trim();
            if (!message) return;

            fetch("http://127.0.0.1:5000/client/send_message", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + localStorage.getItem("token")
                },
                body: JSON.stringify({ message })
            })
                .then(response => response.json())
                .then(data => {
                    appendChatMessage("You", message);
                    messageInput.value = "";
                })
                .catch(error => console.error("Error sending message:", error));
        });
    }

    function appendChatMessage(sender, message) {
        const chatBox = document.getElementById("chat-box");
        if (!chatBox) return;
        const messageItem = document.createElement("div");
        messageItem.classList.add("chat-message");
        messageItem.innerHTML = `<strong>${sender}:</strong> ${message}`;
        chatBox.appendChild(messageItem);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function fetchChatMessages() {
        fetch("http://127.0.0.1:5000/client/get_messages", {
            headers: {
                "Authorization": "Bearer " + localStorage.getItem("token")
            }
        })
            .then(response => response.json())
            .then(messages => {
                const chatBox = document.getElementById("chat-box");
                if (!chatBox) return;
                chatBox.innerHTML = "";
                messages.forEach(msg => appendChatMessage(msg.sender, msg.message));
            })
            .catch(error => console.error("Error fetching messages:", error));
    }

    // 🚀 Initial Data Load
    fetchReminders();
    fetchDashboardSummary();
    fetchChatMessages();
});
hChatMessages();
