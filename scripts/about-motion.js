const aboutMotionStage = document.querySelector("[data-about-motion]");

if (aboutMotionStage) {
    const aboutImages = [
        "images/aboutimgs/about.jpg",
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
        "images/aboutimgs/about12.HEIC.png"
    ];

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
