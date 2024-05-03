document.querySelectorAll(".unfollow-btn").forEach(button => {
    button.addEventListener("click", function() {
        let user_id = button.getAttribute("follower-id");

        fetch("http://127.0.0.1:5000/unfollow/" + user_id, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        })
        .then(response => {
            if (response.ok) {
                button.textContent = "Follow";
                return response.json();
            } else {
                throw new Error("Network response was not ok.");
            }
        })
        .then(data => {
            if (data && data.message) {
                console.log(data.message);
                button.textContent = "Follow";
            } else {
                throw new Error("Invalid response data");
            }
        })
        .catch(error => {
            console.error(error);
        });
    });
});
