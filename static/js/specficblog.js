var like = document.getElementById("like");
var blog_id = like.getAttribute("blog-id");
var blog_like = parseInt(like.getAttribute("blog-like"));
var isClicked = false;
var icon = document.getElementById("icon");
var numlike = document.getElementById("numlike");
numlike.textContent = blog_like;

like.addEventListener("click", function() {
    fetch("http://127.0.0.1:5000/addoremovelike/" + blog_id, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
    })
    .then(function(response) {
        if (response.ok) {
            if(isClicked) {
                blog_like -= 1;
                icon.style.color= "black";
                isClicked = false;
            } else {
                blog_like += 1;
                icon.style.color= "blue";
                isClicked = true;
            }
            numlike.textContent = blog_like; // Update numlike text content
            return response.json();
        } else {
            throw new Error("Error: " + response.status);
        }
    })
    .then(function(data) {
        if (data && data.message) {
            // Handle message if needed
        } else {
            throw new Error("Invalid response data");
        }
    })
    .catch(function(error) {
        console.error(error);
    });
});
