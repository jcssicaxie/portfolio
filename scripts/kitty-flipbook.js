(function () {
    const flipbook = document.querySelector("[data-kitty-flipbook]");

    if (!flipbook) {
        return;
    }

    const pageCount = 41;
    const pageSources = [
        "../images/magazine/kittycouture/KCkaft.png",
        ...Array.from({ length: pageCount }, (_, index) => {
            const pageNumber = String(index + 1).padStart(4, "0");
            return `../images/magazine/kittycouture/kittycouturepages/passieprojectkittycouture_page-${pageNumber}.jpg`;
        }),
        "../images/magazine/kittycouture/KCkaft2.png"
    ];

    const leftImage = flipbook.querySelector("[data-kitty-left]");
    const rightImage = flipbook.querySelector("[data-kitty-right]");
    const turnPage = flipbook.querySelector("[data-kitty-turn]");
    const turnImage = flipbook.querySelector("[data-kitty-turn-image]");
    const previousButton = document.querySelector("[data-kitty-prev]");
    const nextButton = document.querySelector("[data-kitty-next]");
    const currentCount = document.querySelector("[data-kitty-current]");
    const totalCount = document.querySelector("[data-kitty-total]");
    const singlePageQuery = window.matchMedia("(max-width: 44rem)");
    const flipbookSection = flipbook.closest(".kitty-flipbook-section");
    const asciiCursor = document.querySelector(".site-ascii-cursor");
    const defaultCursorText = asciiCursor ? asciiCursor.textContent : "";
    const turnDuration = 480;
    const coverIndex = 0;
    const firstContentIndex = 1;
    const backCoverIndex = pageSources.length - 1;

    let spreadStart = 0;
    let isTurning = false;
    let queuedTurns = 0;

    function formatCount(number) {
        return String(number).padStart(2, "0");
    }

    function setPageImage(image, source, pageNumber) {
        if (!source) {
            image.hidden = true;
            image.removeAttribute("src");
            image.alt = "";
            return;
        }

        image.hidden = false;
        image.src = source;
        image.alt = `Kitty Couture page ${pageNumber}`;
    }

    function getNextSpreadStart(direction) {
        if (singlePageQuery.matches) {
            return spreadStart + direction;
        }

        if (direction > 0) {
            if (spreadStart === coverIndex) {
                return firstContentIndex;
            }

            const nextSpread = spreadStart + 2;
            return nextSpread >= backCoverIndex ? backCoverIndex : nextSpread;
        }

        if (spreadStart === backCoverIndex) {
            return backCoverIndex - 1;
        }

        if (spreadStart <= firstContentIndex) {
            return coverIndex;
        }

        return spreadStart - 2;
    }

    function renderPages() {
        const isSinglePage = singlePageQuery.matches;
        const isSingleCover = !isSinglePage && spreadStart === coverIndex;
        flipbook.classList.toggle("is-cover-spread", isSingleCover);

        if (isSinglePage) {
            setPageImage(leftImage, null, null);
            setPageImage(rightImage, pageSources[spreadStart], spreadStart + 1);
            currentCount.textContent = spreadStart === coverIndex
                ? "Cover"
                : spreadStart === backCoverIndex
                    ? "Back"
                    : formatCount(spreadStart);
        } else {
            if (spreadStart === coverIndex) {
                setPageImage(leftImage, null, null);
                setPageImage(rightImage, pageSources[coverIndex], 1);
                currentCount.textContent = "Cover";
            } else if (spreadStart === backCoverIndex) {
                setPageImage(leftImage, pageSources[backCoverIndex - 1], backCoverIndex - 1);
                setPageImage(rightImage, pageSources[backCoverIndex], backCoverIndex + 1);
                currentCount.textContent = "Back";
            } else if (spreadStart === backCoverIndex - 1) {
                setPageImage(leftImage, pageSources[spreadStart], spreadStart);
                setPageImage(rightImage, pageSources[backCoverIndex], backCoverIndex + 1);
                currentCount.textContent = `${formatCount(spreadStart)}-Back`;
            } else {
                setPageImage(leftImage, pageSources[spreadStart], spreadStart);
                setPageImage(rightImage, pageSources[spreadStart + 1], spreadStart + 1);
                currentCount.textContent = `${formatCount(spreadStart)}-${formatCount(spreadStart + 1)}`;
            }
        }

        totalCount.textContent = formatCount(pageCount);
        previousButton.disabled = spreadStart === 0;
        nextButton.disabled = getNextSpreadStart(1) >= pageSources.length;
    }

    function animateTurn(direction) {
        if (isTurning) {
            queuedTurns = Math.max(-8, Math.min(8, queuedTurns + direction));
            return;
        }

        const nextIndex = getNextSpreadStart(direction);

        if (nextIndex < 0 || nextIndex >= pageSources.length) {
            return;
        }

        isTurning = true;
        const turningPageIndex = direction > 0 && !singlePageQuery.matches
            ? Math.min(spreadStart + 1, pageSources.length - 1)
            : spreadStart;

        turnImage.src = pageSources[turningPageIndex];
        turnImage.alt = "";
        turnPage.classList.remove("is-turning-next", "is-turning-prev");

        spreadStart = nextIndex;
        renderPages();

        void turnPage.offsetWidth;
        window.requestAnimationFrame(() => {
            turnPage.classList.add(direction > 0 ? "is-turning-next" : "is-turning-prev");
        });

        window.setTimeout(() => {
            turnPage.classList.remove("is-turning-next", "is-turning-prev");
            isTurning = false;

            if (queuedTurns !== 0) {
                const nextDirection = queuedTurns > 0 ? 1 : -1;
                queuedTurns -= nextDirection;
                window.requestAnimationFrame(() => animateTurn(nextDirection));
            }
        }, turnDuration);
    }

    previousButton.addEventListener("click", () => animateTurn(-1));
    nextButton.addEventListener("click", () => animateTurn(1));

    if (flipbookSection && asciiCursor) {
        flipbookSection.addEventListener("pointerenter", () => {
            asciiCursor.textContent = "*CLICK*";
            asciiCursor.classList.add("is-click-cursor");
        });

        flipbookSection.addEventListener("pointerleave", () => {
            asciiCursor.textContent = defaultCursorText;
            asciiCursor.classList.remove("is-click-cursor");
        });
    }

    flipbook.addEventListener("click", (event) => {
        const bounds = flipbook.getBoundingClientRect();
        const isRightSide = event.clientX > bounds.left + (bounds.width / 2);
        animateTurn(isRightSide ? 1 : -1);
    });

    window.addEventListener("keydown", (event) => {
        if (event.key === "ArrowLeft") {
            animateTurn(-1);
        }

        if (event.key === "ArrowRight") {
            animateTurn(1);
        }
    });

    singlePageQuery.addEventListener("change", () => {
        if (!singlePageQuery.matches) {
            if (spreadStart > firstContentIndex && spreadStart < backCoverIndex && spreadStart % 2 === 0) {
                spreadStart -= 1;
            }
        }

        renderPages();
    });

    renderPages();
})();
