(function () {
  function setupDropzone(fieldPrefix) {
    const dropzone = document.querySelector(`.panel[data-field="${fieldPrefix}"] .dropzone`);
    const fileInput = document.getElementById(`${fieldPrefix === "resume" ? "resume" : "jd"}_file`);
    const filenameEl = document.getElementById(`${fieldPrefix === "resume" ? "resume" : "jd"}_filename`);
    const textArea = dropzone.querySelector(".paste-area");

    function showFile(file) {
      if (file) {
        filenameEl.textContent = file.name;
        textArea.value = "";
      } else {
        filenameEl.textContent = "";
      }
    }

    dropzone.addEventListener("click", (e) => {
      if (e.target === textArea) return;
      fileInput.click();
    });

    fileInput.addEventListener("change", () => {
      showFile(fileInput.files[0]);
    });

    ["dragenter", "dragover"].forEach((evt) => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });
    });

    ["dragleave", "drop"].forEach((evt) => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      const file = e.dataTransfer.files[0];
      if (file) {
        fileInput.files = e.dataTransfer.files;
        showFile(file);
      }
    });

    textArea.addEventListener("input", () => {
      if (textArea.value.trim()) {
        fileInput.value = "";
        filenameEl.textContent = "";
      }
    });
  }

  setupDropzone("resume");
  setupDropzone("jd");

  const runBtn = document.getElementById("runBtn");
  const results = document.getElementById("results");
  const errorText = document.getElementById("errorText");

  function renderKeywordTags(container, keywords, kind) {
    container.innerHTML = "";
    if (!keywords.length) {
      const empty = document.createElement("span");
      empty.className = "kw-tag";
      empty.textContent = kind === "matched" ? "No overlap found" : "Nothing missing";
      container.appendChild(empty);
      return;
    }
    keywords.forEach((kw) => {
      const tag = document.createElement("span");
      tag.className = `kw-tag ${kind}`;
      tag.textContent = kw;
      container.appendChild(tag);
    });
  }

  function scoreDescription(score) {
    if (score >= 80) return "Strong overlap — your resume speaks the job's language.";
    if (score >= 55) return "Decent overlap, but a few important terms are missing.";
    if (score >= 30) return "Noticeable gaps — worth tailoring before you apply.";
    return "Very little overlap — this resume likely needs targeted edits.";
  }

  async function runMatch() {
    errorText.hidden = true;
    const formData = new FormData();

    const resumeFile = document.getElementById("resume_file").files[0];
    const resumeText = document.getElementById("resume_text").value.trim();
    const jdFile = document.getElementById("jd_file").files[0];
    const jdText = document.getElementById("jd_text").value.trim();

    if (!resumeFile && !resumeText) {
      showError("Add a resume file or paste resume text first.");
      return;
    }
    if (!jdFile && !jdText) {
      showError("Add a job description file or paste JD text first.");
      return;
    }

    if (resumeFile) formData.append("resume_file", resumeFile);
    if (resumeText) formData.append("resume_text", resumeText);
    if (jdFile) formData.append("jd_file", jdFile);
    if (jdText) formData.append("jd_text", jdText);
    formData.append("use_ai", document.getElementById("use_ai").checked ? "true" : "false");

    runBtn.disabled = true;
    runBtn.textContent = "Matching...";

    try {
      const response = await fetch(window.MATCHLINE_RUN_URL, {
        method: "POST",
        headers: { "X-CSRFToken": window.MATCHLINE_CSRF },
        body: formData,
      });
      const data = await response.json();

      if (!response.ok) {
        showError(data.error || "Something went wrong.");
        return;
      }

      renderResults(data);
    } catch (err) {
      showError("Network error — please try again.");
    } finally {
      runBtn.disabled = false;
      runBtn.textContent = "Run the match";
    }
  }

  function showError(message) {
    results.hidden = false;
    document.querySelector(".score-row").style.display = "none";
    document.querySelector(".kw-grid").style.display = "none";
    document.getElementById("aiBlock").hidden = true;
    errorText.textContent = message;
    errorText.hidden = false;
  }

  function renderResults(data) {
    document.querySelector(".score-row").style.display = "flex";
    document.querySelector(".kw-grid").style.display = "grid";
    errorText.hidden = true;

    document.getElementById("scoreValue").textContent = data.score;
    document.getElementById("scoreDesc").textContent = scoreDescription(data.score);

    renderKeywordTags(document.getElementById("matchedList"), data.matched_keywords, "matched");
    renderKeywordTags(document.getElementById("missingList"), data.missing_keywords, "missing");

    const aiBlock = document.getElementById("aiBlock");
    if (data.ai) {
      aiBlock.hidden = false;
      document.getElementById("aiSummary").textContent = data.ai.summary || "";

      const strengthsEl = document.getElementById("aiStrengths");
      strengthsEl.innerHTML = "";
      (data.ai.strengths || []).forEach((s) => {
        const li = document.createElement("li");
        li.textContent = s;
        strengthsEl.appendChild(li);
      });

      const gapsEl = document.getElementById("aiGaps");
      gapsEl.innerHTML = "";
      (data.ai.gaps || []).forEach((g) => {
        const li = document.createElement("li");
        li.textContent = g;
        gapsEl.appendChild(li);
      });
    } else {
      aiBlock.hidden = true;
    }

    results.hidden = false;
    results.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  runBtn.addEventListener("click", runMatch);
})();
