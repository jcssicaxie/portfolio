console.log("hellowww");

const menuButton = document.querySelector("nav button");
const navLinks = document.getElementById("nav-links");
const nav = document.querySelector("nav");

function toggleMenu() {
    // navLinks.classList.toggle("toonMenu");
    nav.classList.toggle("toonMenu");
}

// Toggle menu on button click
menuButton.addEventListener("click", toggleMenu);

// Close menu when clicking outside
document.addEventListener("click", (event) => {
    if (!nav.contains(event.target)) {
        // navLinks.classList.remove("toonMenu");
        nav.classList.remove("toonMenu");
    }
});