function toggle() {
  var x = document.getElementById("myTopnav");
  if (x.className === "topnav") {
    x.className += " responsive";
  } else {
    x.className = "topnav";
  }
}

function smoothScroll(event) {
  event.preventDefault();
  const targetId = event.target.getAttribute("href");
  const target = document.querySelector(targetId);
  target.scrollIntoView({ behavior: "smooth" });

  if (window.innerWidth <= 900) {
    toggle();
    console.log('toggle');
  }
}

export { toggle, smoothScroll };

