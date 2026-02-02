// Mouse-based CSS variables
document.addEventListener("mousemove", (e) => {
  document.documentElement.style.setProperty("--x", e.clientX + "px");
  document.documentElement.style.setProperty("--y", e.clientY + "px");
});

// Elements
const rebuildBtn = document.getElementById("rebuildBtn");
const rebuildStatus = document.getElementById("rebuildStatus");

const searchBtn = document.getElementById("searchBtn");
const searchStatus = document.getElementById("searchStatus");
const imageInput = document.getElementById("imageInput");

const loader = document.getElementById("loader");
const resultsDiv = document.getElementById("results");

const previewWrap = document.getElementById("previewWrap");
const uploadedPreview = document.getElementById("uploadedPreview");

const chooseBtn = document.getElementById("chooseBtn");
const fileName = document.getElementById("fileName");

// Show/hide loader
function showLoader(show) {
  if (!loader) return;
  loader.classList.toggle("hidden", !show);
}

// Clear previous search results
function clearUI() {
  if (!resultsDiv || !previewWrap || !searchStatus) return;
  resultsDiv.innerHTML = "";
  previewWrap.classList.add("hidden");
  searchStatus.innerText = "";
}

// ---------------- Rebuild Database ----------------
if (rebuildBtn) {
  rebuildBtn.onclick = async () => {
    if (!rebuildStatus) return;
    rebuildStatus.innerText = "Rebuilding... ⏳";
    rebuildBtn.disabled = true;

    try {
      const res = await fetch("/api/rebuild_db", { method: "POST" });
      const data = await res.json();

      rebuildStatus.innerText = data.ok
        ? `✅ Done! Saved: ${data.count || 0}, Skipped: ${data.skipped || 0}`
        : "❌ Rebuild failed";
    } catch (e) {
      rebuildStatus.innerText = "❌ Server error";
    }

    rebuildBtn.disabled = false;
  };
}

// ---------------- Search ----------------
if (searchBtn) {
  searchBtn.onclick = async () => {
    clearUI();

    if (!imageInput || !imageInput.files.length) {
      if (searchStatus) searchStatus.innerText = " Select an image first.";
      return;
    }

    showLoader(true);
    searchBtn.disabled = true;
    if (rebuildBtn) rebuildBtn.disabled = true;
    if (searchStatus) searchStatus.innerText = "Ultra matcher running......... ";

    const formData = new FormData();
    formData.append("image", imageInput.files[0]);

    try {
      const res = await fetch("/api/search", { method: "POST", body: formData });
      const data = await res.json();

      showLoader(false);

      if (!data.ok) {
        if (searchStatus) searchStatus.innerText = "❌ " + (data.error || "Unknown error");
        searchBtn.disabled = false;
        if (rebuildBtn) rebuildBtn.disabled = false;
        return;
      }

      // Preview uploaded image
      if (uploadedPreview && previewWrap) {
        uploadedPreview.src = data.uploaded_url || "";
        previewWrap.classList.remove("hidden");
      }

      if (!data.results || !data.results.length) {
        if (searchStatus) searchStatus.innerText = "❌ No strong match found.";
        if (resultsDiv) resultsDiv.innerHTML = `
          <div class="result-card">
            <p><b>No match found.</b></p>
            <p class="muted">Try clear front face photo with good light.</p>
          </div>
        `;
        searchBtn.disabled = false;
        if (rebuildBtn) rebuildBtn.disabled = false;
        return;
      }

      if (searchStatus) searchStatus.innerText = "✅ Top matches found!";

      data.results.forEach((r, i) => {
        const verifiedTag =
          r.verified === true ? `<span class="tag green">Verified ✅</span>` :
          r.verified === false ? `<span class="tag red">Not Verified ❌</span>` : "";

        const distanceTag =
          (r.distance !== null && r.distance !== undefined)
            ? `<span class="tag blue">Dist: ${r.distance.toFixed(3)}</span>` : "";

        const scoreText = (r.score !== null && r.score !== undefined) ? r.score.toFixed(4) : "N/A";

        const card = document.createElement("div");
        card.className = "result-card reveal";
        card.style.animationDelay = `${i * 0.08}s`;

        card.innerHTML = `
          <img class="thumb" src="${r.db_image_url || ''}" alt="${r.filename || 'image'}"/>
          <div class="meta">
            <h4>${r.filename || 'Unknown'}</h4>
            <p>Similarity: <b>${scoreText}</b></p>
            <div class="tags">${verifiedTag}${distanceTag}</div>
          </div>
        `;

        if (resultsDiv) resultsDiv.appendChild(card);
      });

    } catch (e) {
      showLoader(false);
      if (searchStatus) searchStatus.innerText = "❌ Server error while matching.";
    }

    searchBtn.disabled = false;
    if (rebuildBtn) rebuildBtn.disabled = false;
  };
}

// ---------------- Choose Image Button ----------------
if (chooseBtn && imageInput) {
  chooseBtn.onclick = () => imageInput.click();

  imageInput.addEventListener("change", () => {
    if (imageInput.files.length > 0) {
      if (fileName) fileName.innerText = "Selected: " + imageInput.files[0].name;
    } else {
      if (fileName) fileName.innerText = "";
    }
  });
}
