document.querySelectorAll(".unfollow-btn").forEach(button => {
    button.addEventListener("click", function() {
        let user_id = this.getAttribute("follower-id");  // Get the user_id from the clicked button

        fetch("http://127.0.0.1:5000/unfollow/" + user_id, {  // Assuming your server is configured to handle this path
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        })
        .then(response => {
            if (response.ok) {
                this.textContent = "Follow";  // Change the text of this specific button
                return response.json();
            } else {
                throw new Error("Network response was not ok.");
            }
        })
        .then(data => {
            if (data && data.message) {
                console.log(data.message);
            } else {
                throw new Error("Invalid response data");
            }
        })
        .catch(error => {
            console.error(error);
        });
    });
});
