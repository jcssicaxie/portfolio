console.log("hellowww");

const menuButton = document.querySelector("nav button");
const navLinks = document.getElementById("nav-links");
const nav = document.querySelector("nav");

function toggleMenu() {
    // navLinks.classList.toggle("toonMenu");
    nav.classList.toggle("toonMenu");
}

menuButton.addEventListener("click", toggleMenu);

document.addEventListener("click", (event) => {
    if (!nav.contains(event.target)) {
        // navLinks.classList.remove("toonMenu");
        nav.classList.remove("toonMenu");
    }
});

// picture zoom
document.querySelectorAll('.webdesign img').forEach(img => {
    img.classList.add('zoomable');
    img.addEventListener('click', () => {
      document.getElementById('overlay-img').src = img.src;
      document.getElementById('overlay').style.display = 'flex';
    });
  });

  function closeOverlay() {
    document.getElementById('overlay').style.display = 'none';
  }

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      closeOverlay();
    }
  });