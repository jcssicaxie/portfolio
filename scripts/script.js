console.log("hellowww");

const menuButton = document.querySelector("nav button");
const navLinks = document.getElementById("nav-links");
const nav = document.querySelector("nav");

function toggleMenu() {
    nav.classList.toggle("toonMenu");
}

menuButton.addEventListener("click", toggleMenu);

document.addEventListener("click", (event) => {
    if (!nav.contains(event.target)) {
        nav.classList.remove("toonMenu");
    }
});

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