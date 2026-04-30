const menuButton = document.querySelector("nav button:not(.mobile-menu-toggle)");
const nav = document.querySelector("nav");
const MENU_STATE_KEY = "menuIsOpen";

function initializeMenu() {
    if (!nav) {
        return;
    }

    const isMenuOpen = localStorage.getItem(MENU_STATE_KEY) === "true";
    if (isMenuOpen) {
        nav.classList.add("toonMenu");
    }
}

function toggleMenu() {
    if (!nav) {
        return;
    }

    nav.classList.toggle("toonMenu");
    localStorage.setItem(MENU_STATE_KEY, nav.classList.contains("toonMenu"));
}

if (menuButton && nav) {
    initializeMenu();
    menuButton.addEventListener("click", toggleMenu);
}

const mobileMenuToggle = document.querySelector(".mobile-menu-toggle");
const mobileMenu = mobileMenuToggle ? mobileMenuToggle.closest("nav") : null;

if (mobileMenuToggle && mobileMenu) {
    mobileMenuToggle.addEventListener("click", () => {
        const isOpen = mobileMenu.classList.toggle("is-mobile-menu-open");
        mobileMenuToggle.setAttribute("aria-expanded", String(isOpen));
    });
}

const projectDescription = document.querySelector(".project-description-panel");
const projectLocation = document.querySelector("[data-project-location]");
const projectYear = document.querySelector("[data-project-year]");
const projectSections = Array.from(document.querySelectorAll(".project-page section[id]"));
const projectSeriesLinks = Array.from(document.querySelectorAll(".photo-series-nav a[href^=\"#\"]"));

function setActiveProject(section) {
    if (!section || !projectDescription) {
        return;
    }

    const template = section.querySelector(".project-description-template");
    if (template) {
        projectDescription.replaceChildren(template.content.cloneNode(true));
    } else {
        const details = Array.from(section.children).filter(child => child.matches("p, a"));
        projectDescription.replaceChildren(...details.map(child => child.cloneNode(true)));
    }

    if (projectLocation) {
        projectLocation.textContent = section.dataset.location || "";
    }

    if (projectYear) {
        projectYear.textContent = section.dataset.year || "";
    }

    projectSeriesLinks.forEach(link => {
        const isActive = link.getAttribute("href") === "#" + section.id;
        if (isActive) {
            link.setAttribute("aria-current", "page");
        } else {
            link.removeAttribute("aria-current");
        }
    });
}

if (projectDescription && projectSections.length) {
    const initialSection = projectSections.find(section => "#" + section.id === window.location.hash) || projectSections[0];
    setActiveProject(initialSection);

    projectSeriesLinks.forEach(link => {
        link.addEventListener("click", () => {
            const target = document.querySelector(link.getAttribute("href"));
            setActiveProject(target);
        });
    });

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setActiveProject(entry.target);
                }
            });
        }, {
            rootMargin: "-35% 0px -45% 0px",
            threshold: 0
        });

        projectSections.forEach(section => observer.observe(section));
    }
}

const figmaHeaderLinks = Array.from(document.querySelectorAll(".about-figma-header a[href]"));

function navigateHeaderLink(link) {
    const href = link.getAttribute("href");

    if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("http")) {
        return;
    }

    window.location.href = new URL(href, window.location.href).href;
}

figmaHeaderLinks.forEach(link => {
    link.addEventListener("pointerdown", event => {
        const isModifiedClick = event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0;

        if (isModifiedClick) {
            return;
        }

        event.preventDefault();
        navigateHeaderLink(link);
    });

    link.addEventListener("keydown", event => {
        if (event.key !== "Enter") {
            return;
        }

        event.preventDefault();
        navigateHeaderLink(link);
    });

    link.addEventListener("click", event => {
        const href = link.getAttribute("href");
        const isModifiedClick = event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0;

        if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("http") || isModifiedClick) {
            return;
        }

        event.preventDefault();
        navigateHeaderLink(link);
    });
});

const projectIndexes = Array.from(document.querySelectorAll(".portfolio-project-index, .ui-project-index"));

projectIndexes.forEach(index => {
    const links = Array.from(index.querySelectorAll("a[href]"));
    const sectionLinks = links.filter(link => link.getAttribute("href").startsWith("#"));
    const sections = sectionLinks
        .map(link => document.querySelector(link.getAttribute("href")))
        .filter(Boolean);
    const projectContainer = index.closest("main");
    const trackedSections = sections.length
        ? sections
        : Array.from(projectContainer ? projectContainer.querySelectorAll(".portfolio-project[id], .ui-project[id]") : []);
    const usesFixedProjectNote = document.body.classList.contains("graphic-design-page")
        && projectContainer
        && projectContainer.classList.contains("portfolio-showcase");
    const fixedProjectNote = usesFixedProjectNote ? document.createElement("aside") : null;
    const category = projectContainer
        ? projectContainer.getAttribute("aria-label").replace(/\s+(projects|collections)$/i, "")
        : "";
    const metaIndex = document.createElement("aside");
    metaIndex.className = "project-meta-index";
    metaIndex.setAttribute("aria-label", "Current project details");
    metaIndex.innerHTML = `
        <p class="project-index-count"><span data-meta-current>01</span> / <span data-meta-total>01</span></p>
        <dl>
            <div>
                <dt>Category</dt>
                <dd data-meta-category></dd>
            </div>
            <div>
                <dt>Location</dt>
                <dd data-meta-location></dd>
            </div>
            <div data-meta-camera-row hidden>
                <dt>Shot on</dt>
                <dd data-meta-camera></dd>
            </div>
            <div>
                <dt>Year</dt>
                <dd data-meta-year></dd>
            </div>
        </dl>
    `;

    index.insertAdjacentElement("afterend", metaIndex);

    if (fixedProjectNote) {
        fixedProjectNote.className = "portfolio-project-note graphic-fixed-project-note";
        fixedProjectNote.setAttribute("aria-live", "polite");
        projectContainer.insertAdjacentElement("afterend", fixedProjectNote);
    }

    function getProjectYear(section) {
        const activeLink = links.find(link => link.getAttribute("href") === "#" + section.id)
            || links.find(link => link.getAttribute("aria-current") === "page");
        const yearMatch = activeLink ? activeLink.textContent.trim().match(/^\d{4}/) : null;
        return section.dataset.year || (yearMatch ? yearMatch[0] : "-");
    }

    function updateMetaIndex(section) {
        const metaList = metaIndex.querySelector("dl");
        const metaCategory = metaIndex.querySelector("[data-meta-category]");
        const metaLocation = metaIndex.querySelector("[data-meta-location]");
        const metaCamera = metaIndex.querySelector("[data-meta-camera]");
        const metaCameraRow = metaIndex.querySelector("[data-meta-camera-row]");
        const metaYear = metaIndex.querySelector("[data-meta-year]");
        const metaCurrent = metaIndex.querySelector("[data-meta-current]");
        const metaTotal = metaIndex.querySelector("[data-meta-total]");
        const currentCategory = section.dataset.category || category || "-";
        const camera = currentCategory.toLowerCase() === "photography" ? section.dataset.camera || "" : "";
        const activeIndex = Math.max(trackedSections.indexOf(section), 0);
        const formatCount = number => String(number).padStart(2, "0");

        metaCategory.textContent = currentCategory;
        metaLocation.textContent = section.dataset.location || "-";
        metaCamera.textContent = camera;
        metaCameraRow.hidden = !camera;
        metaYear.textContent = getProjectYear(section);
        metaCurrent.textContent = formatCount(activeIndex + 1);
        metaTotal.textContent = formatCount(trackedSections.length);

        metaList.querySelectorAll("[data-project-detail-row]").forEach(row => row.remove());

        section.querySelectorAll(".project-details > div").forEach(detail => {
            const term = detail.querySelector("dt");
            const description = detail.querySelector("dd");

            if (!term || !description) {
                return;
            }

            const row = document.createElement("div");
            const dt = document.createElement("dt");
            const dd = document.createElement("dd");

            row.dataset.projectDetailRow = "";
            dt.textContent = term.textContent;
            dd.textContent = description.textContent;
            row.append(dt, dd);
            metaList.append(row);
        });
    }

    function updateFixedProjectNote(section) {
        if (!fixedProjectNote) {
            return;
        }

        const sourceNote = section.querySelector(".portfolio-project-note");
        if (!sourceNote) {
            fixedProjectNote.replaceChildren();
            return;
        }

        fixedProjectNote.replaceChildren(...Array.from(sourceNote.children).map(child => child.cloneNode(true)));
    }

    function setActiveIndexLink(section) {
        sectionLinks.forEach(link => {
            const isActive = link.getAttribute("href") === "#" + section.id;
            if (isActive) {
                link.setAttribute("aria-current", "page");
            } else {
                link.removeAttribute("aria-current");
            }
        });

        updateMetaIndex(section);
        updateFixedProjectNote(section);
    }

    if (!trackedSections.length) {
        return;
    }

    const initialSection = trackedSections.find(section => "#" + section.id === window.location.hash) || trackedSections[0];
    setActiveIndexLink(initialSection);

    sectionLinks.forEach(link => {
        link.addEventListener("click", () => {
            const target = document.querySelector(link.getAttribute("href"));
            if (target) {
                setActiveIndexLink(target);
            }
        });
    });

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setActiveIndexLink(entry.target);
                }
            });
        }, {
            rootMargin: "-30% 0px -55% 0px",
            threshold: 0
        });

        trackedSections.forEach(section => observer.observe(section));
    }
});
