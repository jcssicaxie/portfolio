const aboutImages = [
    "images/aboutimgs/about12.png",
    "images/aboutimgs/about2.JPEG",
    "images/aboutimgs/about3.jpg",
    "images/aboutimgs/about4.png",
    "images/aboutimgs/about5.png",
    "images/aboutimgs/about6.png",
    "images/aboutimgs/about7.png",
    "images/aboutimgs/about8.png",
    "images/aboutimgs/about9.png",
    "images/aboutimgs/about10.png",
    "images/aboutimgs/about11.jpg",
    "images/aboutimgs/about.jpg"
];

const aboutMotionStage = document.querySelector("[data-about-motion]");

if (aboutMotionStage) {
    const tiles = aboutImages.map((source, index) => {
        const tile = document.createElement("div");
        const image = document.createElement("img");

        tile.className = "about-motion-photo";
        tile.dataset.aboutImageIndex = String(index);

        image.src = source;
        image.alt = "";
        image.loading = "eager";
        image.decoding = "async";

        tile.appendChild(image);
        return tile;
    });

    aboutMotionStage.replaceChildren(...tiles);
    document.body.classList.add("about-motion-ready");
}

// Hero background on mobile: the same photo set as the About "hover to
// reveal" effect above, but laid out in a fixed grid and auto-animated in
// an alternating checkerboard flicker (see the matching @keyframes and
// breakpoint in styles/style.css) since there's no hover on a phone.
const homeMotionStage = document.querySelector("[data-home-motion]");

if (homeMotionStage) {
    const homeMotionQuery = window.matchMedia("(max-width: 54em)");
    const homeMotionColumns = 3;
    const homeMotionCycleSeconds = 6;
    let homeMotionBuilt = false;

    function buildHomeMotionTiles() {
        if (homeMotionBuilt) {
            return;
        }

        homeMotionBuilt = true;

        const tiles = aboutImages.map((source, index) => {
            const tile = document.createElement("div");
            const image = document.createElement("img");
            const row = Math.floor(index / homeMotionColumns);
            const column = index % homeMotionColumns;
            const isEvenSquare = (row + column) % 2 === 0;
            const baseDelay = isEvenSquare ? 0 : homeMotionCycleSeconds / 2;
            const jitter = Math.random() * (homeMotionCycleSeconds / 8);

            tile.className = "home-motion-photo";
            tile.style.setProperty("--home-motion-delay", `${baseDelay + jitter}s`);

            image.src = source;
            image.alt = "";
            image.loading = "eager";
            image.decoding = "async";

            tile.appendChild(image);
            return tile;
        });

        homeMotionStage.replaceChildren(...tiles);
    }

    function teardownHomeMotionTiles() {
        homeMotionBuilt = false;
        homeMotionStage.replaceChildren();
    }

    function syncHomeMotion(query) {
        if (query.matches) {
            buildHomeMotionTiles();
        } else {
            teardownHomeMotionTiles();
        }
    }

    syncHomeMotion(homeMotionQuery);

    if (homeMotionQuery.addEventListener) {
        homeMotionQuery.addEventListener("change", syncHomeMotion);
    } else if (homeMotionQuery.addListener) {
        homeMotionQuery.addListener(syncHomeMotion);
    }
}
