var pageName = window.location.pathname.split("/").pop().split(".")[0];
if (pageName == "") pageName = "index";

fetch("./header.html")
  .then(response => {
      return response.text()
    })
  .then(data => {
      document.querySelector("pageheader").innerHTML = data;
      document.querySelector(".menu-li-"+pageName).classList.add("active");
      document.querySelector(".menu-a-"+pageName).classList.add("active");
      document.querySelector(".menu-a-"+pageName).innerHTML += '<span class="sr-only">current</span>';
    });

fetch("./footer.html")
  .then(response => {
    return response.text()
  })
  .then(data => {
    document.querySelector("pagefooter").innerHTML = data;
  });
