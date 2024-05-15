

var search = document.getElementById("search");

search.addEventListener("click", function()
{

var text = document.getElementById("text").value;

if(text)
{
event.preventDefault();



 window.location.href = "http://127.0.0.1:5000/searchblog/" + text;
}
else{
event.preventDefault();
}

});
