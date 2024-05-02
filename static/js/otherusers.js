var followbutton = document.getElementById("follow");
var follower = document.getElementById("follower");
var following = document.getElementById("following");
var user_id = followbutton.getAttribute("user-id");

if (followbutton.textContent == "Followed") {
  followbutton.addEventListener("click", function() {
    fetch("http://127.0.0.1:5000/follow/" + user_id, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then(function(response) {
        if (response.ok) {
          followbutton.textContent = "Followed";
          return response.json();
        } else {
          throw new Error("Error: " + response.status);
        }
      })
      .then(function(data) {
        if (data && data.message) {
          console.log(data.message);
        } else {
          throw new Error("Invalid response data");
        }
      })
      .catch(function(error) {
        console.error(error);
      });
  });
} else {
  followbutton.addEventListener("click", function() {
    fetch("http://127.0.0.1:5000/unfollow/" + user_id, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    })
      .then(function(response) {
        if (response.ok) {
          followbutton.textContent = "Follow";
          return response.json();
        } else {
          throw new Error("Error: " + response.status);
        }
      })
      .then(function(data) {
        if (data && data.message) {
          console.log(data.message);
        } else {
          throw new Error("Invalid response data");
        }
      })
      .catch(function(error) {
        console.error(error);
      });
  });
}