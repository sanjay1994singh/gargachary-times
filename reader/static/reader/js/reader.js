(function () {
    const pages = JSON.parse(document.getElementById("pagesData").textContent);
    const editions = JSON.parse(document.getElementById("editionsData").textContent);
    const paperFrame = document.getElementById("paperFrame");
    const paperImage = document.getElementById("paperImage");
    const pageSelect = document.getElementById("pageSelect");
    const datePicker = document.getElementById("editionDatePicker");
    const pagesDrawer = document.getElementById("pagesDrawer");
    const utilityDrawer = document.getElementById("utilityDrawer");
    const toast = document.getElementById("readerToast");
    const clipBox = document.getElementById("clipBox");
    const bookmarkList = document.getElementById("bookmarkList");
    const thumbnails = Array.from(document.querySelectorAll(".thumbnail"));

    const bookmarkKey = "epaper-bookmarks";
    let pageIndex = Math.max(0, pageSelect.selectedIndex);
    let zoom = 1;
    let clipMode = false;
    let clipStart = null;

    function showToast(message) {
        toast.textContent = message;
        toast.hidden = false;
        window.clearTimeout(showToast.timer);
        showToast.timer = window.setTimeout(() => {
            toast.hidden = true;
        }, 2400);
    }

    function getBookmarks() {
        try {
            return JSON.parse(window.localStorage.getItem(bookmarkKey)) || [];
        } catch (error) {
            return [];
        }
    }

    function saveBookmarks(bookmarks) {
        window.localStorage.setItem(bookmarkKey, JSON.stringify(bookmarks));
    }

    function renderBookmarks() {
        const bookmarks = getBookmarks();
        if (bookmarks.length === 0) {
            bookmarkList.innerHTML = "<h3>Bookmarks</h3><p>No bookmarked pages yet.</p>";
            return;
        }

        const buttons = bookmarks
            .map((bookmark) => (
                `<button type="button" data-bookmark-page="${bookmark.index}">${bookmark.label}</button>`
            ))
            .join("");
        bookmarkList.innerHTML = `<h3>Bookmarks</h3>${buttons}`;
    }

    function renderPage() {
        if (!paperImage || pages.length === 0) {
            return;
        }

        const page = pages[pageIndex];
        paperImage.src = page.image;
        paperImage.alt = `${page.title} newspaper page`;
        pageSelect.selectedIndex = pageIndex;
        thumbnails.forEach((thumb, index) => {
            thumb.classList.toggle("is-active", index === pageIndex);
        });
        hideClipBox();
    }

    function setPage(nextIndex) {
        if (pages.length === 0) {
            return;
        }
        pageIndex = Math.max(0, Math.min(pages.length - 1, nextIndex));
        renderPage();
    }

    function setZoom(nextZoom) {
        zoom = Math.max(0.65, Math.min(2.2, nextZoom));
        paperFrame.style.transform = `scale(${zoom})`;
        showToast(`Zoom ${Math.round(zoom * 100)}%`);
    }

    function fitPage() {
        setZoom(1);
        document.querySelector(".page-stage").scrollIntoView({ block: "start", behavior: "smooth" });
    }

    function toggleBookmark() {
        if (pages.length === 0) {
            return;
        }

        const page = pages[pageIndex];
        const bookmarks = getBookmarks();
        const exists = bookmarks.some((bookmark) => bookmark.index === pageIndex);
        const nextBookmarks = exists
            ? bookmarks.filter((bookmark) => bookmark.index !== pageIndex)
            : bookmarks.concat([{ index: pageIndex, label: page.title }]);

        saveBookmarks(nextBookmarks);
        renderBookmarks();
        showToast(exists ? `${page.title} removed from bookmarks` : `${page.title} bookmarked`);
    }

    function toggleClipMode(button) {
        clipMode = !clipMode;
        document.body.classList.toggle("clip-mode", clipMode);
        button.classList.toggle("is-active-tool", clipMode);
        hideClipBox();
        showToast(clipMode ? "Drag over the page to clip an area" : "Clip mode off");
    }

    function hideClipBox() {
        if (!clipBox) {
            return;
        }
        clipBox.hidden = true;
        clipBox.style.cssText = "";
    }

    function updateClipBox(start, current) {
        const left = Math.min(start.x, current.x);
        const top = Math.min(start.y, current.y);
        const width = Math.abs(current.x - start.x);
        const height = Math.abs(current.y - start.y);

        clipBox.hidden = false;
        clipBox.style.left = `${left}px`;
        clipBox.style.top = `${top}px`;
        clipBox.style.width = `${width}px`;
        clipBox.style.height = `${height}px`;
    }

    function pointOnImage(event) {
        const imageRect = paperImage.getBoundingClientRect();
        return {
            x: (event.clientX - imageRect.left) / zoom,
            y: (event.clientY - imageRect.top) / zoom,
        };
    }

    function downloadClip(start, end) {
        const left = Math.min(start.x, end.x);
        const top = Math.min(start.y, end.y);
        const width = Math.abs(end.x - start.x);
        const height = Math.abs(end.y - start.y);

        if (width < 24 || height < 24) {
            hideClipBox();
            showToast("Clip area is too small");
            return;
        }

        const ratioX = paperImage.naturalWidth / paperImage.clientWidth;
        const ratioY = paperImage.naturalHeight / paperImage.clientHeight;
        const canvas = document.createElement("canvas");
        canvas.width = Math.round(width * ratioX);
        canvas.height = Math.round(height * ratioY);

        const context = canvas.getContext("2d");
        context.drawImage(
            paperImage,
            Math.round(left * ratioX),
            Math.round(top * ratioY),
            canvas.width,
            canvas.height,
            0,
            0,
            canvas.width,
            canvas.height
        );

        const link = document.createElement("a");
        link.download = `epaper-page-${pageIndex + 1}-clip.png`;
        link.href = canvas.toDataURL("image/png");
        link.click();
        hideClipBox();
        showToast("Clip downloaded");
    }

    function shareTo(platform) {
        const url = encodeURIComponent(window.location.href);
        const text = encodeURIComponent(document.title);
        const shareUrl = platform === "facebook"
            ? `https://www.facebook.com/sharer/sharer.php?u=${url}`
            : `https://twitter.com/intent/tweet?url=${url}&text=${text}`;
        window.open(shareUrl, "_blank", "noopener,noreferrer,width=720,height=520");
    }

    async function copyReaderLink() {
        try {
            await navigator.clipboard.writeText(window.location.href);
            showToast("Reader link copied");
        } catch (error) {
            showToast(window.location.href);
        }
    }

    function findEditionForDate(dateValue) {
        if (!dateValue) {
            return null;
        }

        const city = datePicker.dataset.city;
        const section = datePicker.dataset.section;
        return editions.find((edition) => (
            edition.date === dateValue
            && edition.city === city
            && edition.section === section
        )) || editions.find((edition) => (
            edition.date === dateValue
            && edition.city === city
        )) || editions.find((edition) => edition.date === dateValue);
    }

    function openDatePicker() {
        if (!datePicker) {
            return;
        }

        if (typeof datePicker.showPicker === "function") {
            datePicker.showPicker();
        } else {
            datePicker.focus();
            datePicker.click();
        }
    }

    document.addEventListener("click", (event) => {
        const bookmarkButton = event.target.closest("[data-bookmark-page]");
        if (bookmarkButton) {
            setPage(Number(bookmarkButton.dataset.bookmarkPage));
            utilityDrawer.hidden = true;
            return;
        }

        const actionButton = event.target.closest("[data-action]");
        if (!actionButton) {
            return;
        }

        const action = actionButton.dataset.action;
        if (action === "previous") {
            setPage(pageIndex - 1);
        } else if (action === "next") {
            setPage(pageIndex + 1);
        } else if (action === "first") {
            setPage(0);
        } else if (action === "last") {
            setPage(pages.length - 1);
        } else if (action === "zoom-in") {
            setZoom(zoom + 0.15);
        } else if (action === "zoom-out") {
            setZoom(zoom - 0.15);
        } else if (action === "fit") {
            fitPage();
        } else if (action === "bookmark") {
            toggleBookmark();
        } else if (action === "clip") {
            toggleClipMode(actionButton);
        } else if (action === "pages") {
            pagesDrawer.hidden = false;
        } else if (action === "close-pages") {
            pagesDrawer.hidden = true;
        } else if (action === "menu") {
            renderBookmarks();
            utilityDrawer.hidden = false;
        } else if (action === "close-menu") {
            utilityDrawer.hidden = true;
        } else if (action === "date") {
            openDatePicker();
        } else if (action === "share-facebook") {
            shareTo("facebook");
        } else if (action === "share-x") {
            shareTo("x");
        } else if (action === "copy-link") {
            copyReaderLink();
        }
    });

    pageSelect.addEventListener("change", () => {
        setPage(pageSelect.selectedIndex);
    });

    if (datePicker) {
        datePicker.addEventListener("change", () => {
            const matchingEdition = findEditionForDate(datePicker.value);
            if (matchingEdition) {
                window.location.href = matchingEdition.url;
                return;
            }

            showToast("No e-paper uploaded for this date");
        });
    }

    thumbnails.forEach((thumbnail) => {
        thumbnail.addEventListener("click", () => {
            setPage(Number(thumbnail.dataset.page));
            pagesDrawer.hidden = true;
        });
    });

    if (paperImage) {
        paperImage.addEventListener("pointerdown", (event) => {
            if (!clipMode) {
                return;
            }
            event.preventDefault();
            paperImage.setPointerCapture(event.pointerId);
            clipStart = pointOnImage(event);
            updateClipBox(clipStart, clipStart);
        });

        paperImage.addEventListener("pointermove", (event) => {
            if (!clipMode || !clipStart) {
                return;
            }
            updateClipBox(clipStart, pointOnImage(event));
        });

        paperImage.addEventListener("pointerup", (event) => {
            if (!clipMode || !clipStart) {
                return;
            }
            const clipEnd = pointOnImage(event);
            downloadClip(clipStart, clipEnd);
            clipStart = null;
        });
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "ArrowLeft") {
            setPage(pageIndex - 1);
        } else if (event.key === "ArrowRight") {
            setPage(pageIndex + 1);
        } else if (event.key === "+" || event.key === "=") {
            setZoom(zoom + 0.15);
        } else if (event.key === "-") {
            setZoom(zoom - 0.15);
        } else if (event.key === "Escape") {
            pagesDrawer.hidden = true;
            utilityDrawer.hidden = true;
            clipMode = false;
            document.body.classList.remove("clip-mode");
            document.querySelector('[data-action="clip"]')?.classList.remove("is-active-tool");
            hideClipBox();
        }
    });

    renderBookmarks();
    renderPage();
})();
