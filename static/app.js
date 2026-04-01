const DRAFT_STORAGE_KEY = "movie-form-draft";
const isDesktopMode = new URLSearchParams(window.location.search).get("desktop") === "1";
const today = new Date();
const currYear = today.getFullYear();
const month = String(today.getMonth() + 1).padStart(2, "0");
const day = String(today.getDate()).padStart(2, "0");
const DEFAULT_DATE = `${currYear}-${month}-${day}`;
const DEFAULT_RATING = 4.0;
const DEFAULT_QUALITY = "1080p";

async function postData(url, data, keepalive = false) {
    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data),
            keepalive
        });

        let responseData = null;
        try {
            responseData = await response.json();
        } catch (error) {
            throw new Error("Server returned invalid JSON.");
        }

        if (!response.ok) {
            const errorMessage =
                responseData?.message || `HTTP error! Status: ${response.status}`;
            throw new Error(errorMessage);
        }

        console.log("responseData:", responseData);
        return responseData;
    } catch (error) {
        console.error("Fetch error:", error);
        throw error;
    }
}

async function pingBackend() {
    try {
        await fetch("/api/client-ping", {
            method: "POST",
            keepalive: true
        });
    } catch (error) {
        console.error("Heartbeat error:", error);
    }
}

function loadLocalDraft() {
    try {
        const draft = localStorage.getItem(DRAFT_STORAGE_KEY);
        return draft ? JSON.parse(draft) : {};
    } catch (error) {
        console.error("Load local draft error:", error);
        return {};
    }
}

async function loadServerDraft() {
    try {
        const response = await fetch("/api/load");
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Load server draft error:", error);
        return {};
    }
}

function hasDraftData(data) {
    return Boolean(
        data && Object.values(data).some((value) => value !== "" && value !== null && value !== undefined)
    );
}

function getDefaultFormData() {
    return {
        sheetname: String(currYear),
        date: DEFAULT_DATE,
        url: "",
        name: "",
        director: "",
        year: "",
        image: "",
        quality: DEFAULT_QUALITY,
        rating: DEFAULT_RATING,
        comments: ""
    };
}

function isDefaultDraft(data) {
    const defaults = getDefaultFormData();

    return (
        (data?.date ?? defaults.date) === defaults.date &&
        (data?.url ?? "") === defaults.url &&
        (data?.name ?? "") === defaults.name &&
        (data?.director ?? "") === defaults.director &&
        String(data?.year ?? "") === String(defaults.year) &&
        (data?.image ?? "") === defaults.image &&
        (data?.quality ?? defaults.quality) === defaults.quality &&
        Number(data?.rating ?? defaults.rating) === defaults.rating &&
        (data?.comments ?? "") === defaults.comments
    );
}

function buildFormData() {
    const selectedQuality = qualitySelect.value;
    const customQuality = otherQualityInput.value.trim();

    return {
        sheetname: String(currYear),
        date: dateInput.value,
        url: urlInput.value.trim(),
        name: parsedMovieData?.name ?? "",
        director: parsedMovieData?.director ?? "",
        year: parsedMovieData?.year ?? "",
        image: parsedMovieData?.image ?? "",
        quality: selectedQuality === "Other" ? customQuality : selectedQuality,
        rating: Number(ratingInput.value),
        comments: commentsInput.value.trim()
    };
}

async function saveServerDraft(data) {
    try {
        await postData("/api/save", data, true);
    } catch (error) {
        console.error("Save server draft error:", error);
    }
}

function saveLocalDraft(data) {
    try {
        localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(data));
    } catch (error) {
        console.error("Save local draft error:", error);
    }
}

function saveDraft() {
    const draft = buildFormData();
    if (isDefaultDraft(draft)) {
        void clearDraft();
        return;
    }
    saveLocalDraft(draft);
    if (isDesktopMode) {
        void saveServerDraft(draft);
    }
}

function clearLocalDraft() {
    try {
        localStorage.removeItem(DRAFT_STORAGE_KEY);
    } catch (error) {
        console.error("Clear local draft error:", error);
    }
}

function clearDraft() {
    clearLocalDraft();
    if (isDesktopMode) {
        return saveServerDraft({});
    }
    return Promise.resolve();
}

function applyDraft(data) {
    const draft = hasDraftData(data) ? data : getDefaultFormData();

    dateInput.value = draft.date || DEFAULT_DATE;
    urlInput.value = draft.url ?? "";
    ratingInput.value = draft.rating ?? DEFAULT_RATING;
    commentsInput.value = draft.comments ?? "";

    const loadedQuality = draft.quality ?? DEFAULT_QUALITY;
    const isPresetQuality = Array.from(qualitySelect.options).some(
        (option) => option.value === loadedQuality
    );
    qualitySelect.value = isPresetQuality ? loadedQuality : "Other";
    otherQualityInput.value = isPresetQuality ? "" : loadedQuality;
    otherInput.style.display = qualitySelect.value === "Other" ? "block" : "none";

    name.textContent = draft.name ?? "";
    director.textContent = draft.director ?? "";
    year.textContent = draft.year ?? "";

    parsedMovieData = draft.name
        ? {
            name: draft.name ?? "",
            director: draft.director ?? "",
            year: draft.year ?? "",
            image: draft.image ?? ""
        }
        : null;

    movieInfo.style.display = draft.name ? "block" : "none";
}

function resetFormToDefaults() {
    if (saveDraftTimer !== null) {
        clearTimeout(saveDraftTimer);
        saveDraftTimer = null;
    }

    parsedMovieData = null;
    dateInput.value = DEFAULT_DATE;
    urlInput.value = "";
    qualitySelect.value = DEFAULT_QUALITY;
    otherQualityInput.value = "";
    otherInput.style.display = "none";
    ratingInput.value = DEFAULT_RATING;
    commentsInput.value = "";
    name.textContent = "";
    director.textContent = "";
    year.textContent = "";
    movieInfo.style.display = "none";
    resultBox.style.display = "none";
}

let saveDraftTimer = null;

function scheduleDraftSave() {
    if (saveDraftTimer !== null) {
        clearTimeout(saveDraftTimer);
    }

    saveDraftTimer = setTimeout(() => {
        saveDraft();
        saveDraftTimer = null;
    }, 400);
}

const qualitySelect = document.getElementById("quality");
const otherInput = document.getElementById("otherInput");
const dateInput = document.getElementById("date");
const ratingInput = document.getElementById("rating");
const parseBtn = document.getElementById("parseBtn");
const submitBtn = document.getElementById("submitBtn");
const urlInput = document.getElementById("URL");
const otherQualityInput = document.getElementById("other");
const commentsInput = document.getElementById("comments");
const messageBox = document.getElementById("message");
const resultBox = document.getElementById("result");
const movieInfo = document.getElementById("movieInfo");
const name = document.getElementById("name");
const director = document.getElementById("director");
const year = document.getElementById("year");
let parsedMovieData = null;

pingBackend();
setInterval(pingBackend, 2000);
dateInput.value = DEFAULT_DATE;
ratingInput.value = DEFAULT_RATING;

ratingInput.addEventListener("input", () => {
    const rating = parseFloat(ratingInput.value);
    if (rating > 5) {
        ratingInput.value = 5;
    } else if (rating < 0) {
        ratingInput.value = 0;
    }
});

qualitySelect.addEventListener("change", () => {
    if (qualitySelect.value === "Other") {
        otherInput.style.display = "block";
    } else {
        otherInput.style.display = "none";
    }

    scheduleDraftSave();
});

urlInput.addEventListener("input", () => {
    parsedMovieData = null;
    movieInfo.style.display = "none";
    name.textContent = "";
    director.textContent = "";
    year.textContent = "";
    scheduleDraftSave();
});

dateInput.addEventListener("input", scheduleDraftSave);
ratingInput.addEventListener("input", scheduleDraftSave);
otherQualityInput.addEventListener("input", scheduleDraftSave);
commentsInput.addEventListener("input", scheduleDraftSave);

parseBtn.addEventListener("click", async () => {
    const url = urlInput.value.trim();

    if (!url) {
        messageBox.textContent = "Please enter a movie URL before parsing.";
        movieInfo.style.display = "none";
        return;
    }

    messageBox.textContent = "Parsing movie information...";
    resultBox.style.display = "none";

    try {
        const data = await postData("/api/movie", {
            title: "parse url",
            url,
            userId: 1
        });
        parsedMovieData = data;

        name.textContent = data.name ?? "";
        director.textContent = data.director ?? "";
        year.textContent = data.year ?? "";
        movieInfo.style.display = "block";
        messageBox.textContent = "Movie information loaded successfully.";
        scheduleDraftSave();
    } catch (error) {
        movieInfo.style.display = "none";
        messageBox.textContent = error.message || "Failed to connect to the backend.";
        console.error(error);
    }
});

submitBtn.addEventListener("click", async () => {
    const submission = buildFormData();
    const { date, url, rating } = submission;
    const selectedQuality = qualitySelect.value;
    const customQuality = otherQualityInput.value.trim();

    if (!date) {
        messageBox.textContent = "Please select a date.";
        resultBox.style.display = "none";
        return;
    }

    if (!url) {
        messageBox.textContent = "Please enter a movie URL.";
        resultBox.style.display = "none";
        return;
    }

    if (selectedQuality === "Other" && !customQuality) {
        messageBox.textContent = "Please enter a custom quality.";
        resultBox.style.display = "none";
        return;
    }

    if (Number.isNaN(rating) || rating < 0 || rating > 5) {
        messageBox.textContent = "Rating must be a number between 0 and 5.";
        resultBox.style.display = "none";
        return;
    }

    messageBox.textContent = "Submitting...";
    resultBox.textContent = JSON.stringify(submission, null, 2);
    resultBox.style.display = "block";

    try {
        await postData("/api/submit", submission);
        resetFormToDefaults();
        await clearDraft();
        messageBox.textContent = "Submitted";
    } catch (error) {
        messageBox.textContent = error.message || "Failed to submit.";
        resultBox.style.display = "none";
        console.error(error);
    }
});

window.addEventListener("DOMContentLoaded", async () => {
    let data = loadLocalDraft();

    if (!hasDraftData(data) && isDesktopMode) {
        data = await loadServerDraft();
        if (hasDraftData(data)) {
            saveLocalDraft(data);
        }
    }

    applyDraft(data);
});

window.addEventListener("pagehide", saveDraft);
window.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
        saveDraft();
    }
});
