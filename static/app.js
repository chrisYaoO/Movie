async function postData(url, data) {
    try {
        const response = await fetch(url, {
            method: 'POST', // *METHOD* set to POST
            headers: {
                'Content-Type': 'application/json' // *HEADERS* tell the server how to interpret the body
            },
            body: JSON.stringify(data) // *BODY* data is stringified
        });

        let responseData = null;
        try {
            responseData = await response.json();
        } catch (error) {
            throw new Error("Server returned invalid JSON.");
        }

        if (!response.ok) {
            const errorMessage = responseData?.message || `HTTP error! Status: ${response.status}`;
            throw new Error(errorMessage);
        }

        console.log('responseData:', responseData);
        return responseData;

    } catch (error) {
        console.error('Fetch error:', error); // *ERROR HANDLING*
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

// Usage
// const apiEndpoint = 'https://jsonplaceholder.typicode.com/posts'; // Example API endpoint
// const myData = {
//   title: 'My new post',
//   body: 'This is the content of my post.',
//   userId: 1
// };

// postData(apiEndpoint, myData);


async function loadData() {
    try {
        const response = await fetch("/api/load");
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
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
        quality: selectedQuality === "Other" ? customQuality : selectedQuality,
        rating: Number(ratingInput.value),
        comments: commentsInput.value.trim(),
    };
}

function saveDraft() {
    const savedData = buildFormData();

    fetch("/api/save", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(savedData),
        keepalive: true
    }).catch((error) => {
        console.error("Save draft error:", error);
    });
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
let parsedMovieData = null;

pingBackend();
setInterval(pingBackend, 2000);


// Default date set to today using local time.
const today = new Date();
const currYear = today.getFullYear();
const month = String(today.getMonth() + 1).padStart(2, "0");
const day = String(today.getDate()).padStart(2, "0");
dateInput.value = `${currYear}-${month}-${day}`;

// Rating input limitation.
ratingInput.addEventListener("input", () => {
    const rating = parseFloat(ratingInput.value);
    if (rating > 5) {
        ratingInput.value = 5;
    } else if (rating < 0) {
        ratingInput.value = 0;
    }
});
ratingInput.value = 4.0;

// Show custom quality input when needed.
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
    document.getElementById("movieInfo").style.display = "none";
    scheduleDraftSave();
});

dateInput.addEventListener("input", scheduleDraftSave);
ratingInput.addEventListener("input", scheduleDraftSave);
otherQualityInput.addEventListener("input", scheduleDraftSave);
commentsInput.addEventListener("input", scheduleDraftSave);

// Parse URL button.
parseBtn.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    const movieInfo = document.getElementById("movieInfo");
    const name = document.getElementById("name");
    const director = document.getElementById("director");
    const year = document.getElementById("year");

    if (!url) {
        messageBox.textContent = "Please enter a movie URL before parsing.";
        movieInfo.style.display = "none";
        return;
    }

    const apiEndpoint = "/api/movie";
    const myData = {
        title: 'parse url',
        url: url,
        userId: 1
    };

    messageBox.textContent = "Parsing movie information...";
    resultBox.style.display = "none";

    try {
        const data = await postData(apiEndpoint, myData);
        console.log("returned data:", data);
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

    // console.log(url);
});

// Submit button.
submitBtn.addEventListener("click", async () => {
    const submission = buildFormData();
    const { date, url, quality, rating } = submission;
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

    const apiEndpoint = "/api/submit";
    messageBox.textContent = "Submitting...";
    resultBox.textContent = JSON.stringify(submission, null, 2);
    resultBox.style.display = "block";

    try {
        const response = await postData(apiEndpoint, submission);
        messageBox.textContent = "Submitted";
        resultBox.style.display = "none";
        console.log(response);

    } catch (error) {
        messageBox.textContent = error.message || "Failed to submit.";
        resultBox.style.display = "none";
        console.error(error);

    }

    console.log(submission);
});

window.addEventListener("DOMContentLoaded", async () => {
    let data = {};

    try {
        data = await loadData();
        console.log(data);
    } catch (error) {
        messageBox.textContent = error.message || "Failed to load data.";
        console.error(error);
        return;
    }

    dateInput.value = data.date ?? "";
    urlInput.value = data.url ?? "";
    ratingInput.value = data.rating ?? 4.0;
    commentsInput.value = data.comments ?? "";

    const loadedQuality = data.quality ?? "";
    const isPresetQuality = Array.from(qualitySelect.options).some(
        (option) => option.value === loadedQuality
    );
    qualitySelect.value = isPresetQuality ? loadedQuality : "Other";
    otherQualityInput.value = isPresetQuality ? "" : loadedQuality;
    otherInput.style.display = qualitySelect.value === "Other" ? "block" : "none";

    document.getElementById("name").textContent = data.name ?? "";
    document.getElementById("director").textContent = data.director ?? "";
    document.getElementById("year").textContent = data.year ?? "";

    parsedMovieData = {
        name: data.name ?? "",
        director: data.director ?? "",
        year: data.year ?? "",
    };

    if (data.name) {
        document.getElementById("movieInfo").style.display = "block";
    }
    else {
        document.getElementById("movieInfo").style.display = "none";
    }
});

window.addEventListener("pagehide", saveDraft);
window.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
        saveDraft();
    }
});
