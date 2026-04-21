console.log("hellowww");

const menuButton = document.querySelector("nav button");
const navLinks = document.getElementById("nav-links");
const nav = document.querySelector("nav");

// Menu persistence using localStorage
const MENU_STATE_KEY = "menuIsOpen";

// Check if menu should be open on page load
function initializeMenu() {
    const isMenuOpen = localStorage.getItem(MENU_STATE_KEY) === "true";
    if (isMenuOpen) {
        nav.classList.add("toonMenu");
    }
}

function toggleMenu() {
    nav.classList.toggle("toonMenu");
    // Save the menu state to localStorage
    const isNowOpen = nav.classList.contains("toonMenu");
    localStorage.setItem(MENU_STATE_KEY, isNowOpen);
}

// Initialize menu on page load
initializeMenu();

// Only toggle on button click - removed the document click listener
menuButton.addEventListener("click", toggleMenu);

// picture zoom
document.querySelectorAll('.webdesign img').forEach(img => {
    img.classList.add('zoomable');
    img.addEventListener('click', () => {
        const overlay = document.getElementById('overlay');
        const overlayImg = document.getElementById('overlay-img');
      
        overlayImg.src = img.src;
        overlay.style.display = 'flex';
      
        overlay.classList.remove('starsync-overlay', 'neworder-first-overlay');
      
        if (img.closest('.starsyncimg')) {
          overlay.classList.add('starsync-overlay');
        }
      
        const neworderContainer = img.closest('.neworderimg');
        if (neworderContainer && neworderContainer.firstElementChild === img) {
          overlay.classList.add('neworder-first-overlay');
        }
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

