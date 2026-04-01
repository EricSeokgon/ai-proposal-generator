"use strict";
(() => {
  // src/ui.ts
  var dropZone = document.getElementById("dropZone");
  var fileInput = document.getElementById("fileInput");
  var convertBtn = document.getElementById("convertBtn");
  var statusEl = document.getElementById("status");
  var progressWrap = document.getElementById("progressWrap");
  var progressFill = document.getElementById("progressFill");
  var progressText = document.getElementById("progressText");
  var loadedData = null;
  dropZone.addEventListener("click", function() {
    fileInput.click();
  });
  dropZone.addEventListener("dragover", function(e) {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });
  dropZone.addEventListener("dragleave", function() {
    dropZone.classList.remove("dragover");
  });
  dropZone.addEventListener("drop", function(e) {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer?.files[0])
      handleFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener("change", function() {
    if (fileInput.files?.[0])
      handleFile(fileInput.files[0]);
  });
  function handleFile(file) {
    if (!file.name.endsWith(".json")) {
      setStatus(".figma.json \uD30C\uC77C\uB9CC \uC9C0\uC6D0\uD569\uB2C8\uB2E4", "error");
      return;
    }
    var reader = new FileReader();
    reader.onload = function(e) {
      try {
        loadedData = JSON.parse(e.target?.result);
        if (!Array.isArray(loadedData) || loadedData.length === 0) {
          setStatus("\uC720\uD6A8\uD558\uC9C0 \uC54A\uC740 JSON \uD615\uC2DD", "error");
          return;
        }
        setStatus(file.name + " \u2014 " + loadedData.length + "\uAC1C \uC2AC\uB77C\uC774\uB4DC", "success");
        convertBtn.disabled = false;
        dropZone.querySelector("p").textContent = file.name;
      } catch (err) {
        setStatus("JSON \uD30C\uC2F1 \uC624\uB958: " + err.message, "error");
      }
    };
    reader.readAsText(file);
  }
  convertBtn.addEventListener("click", function() {
    if (!loadedData)
      return;
    convertBtn.disabled = true;
    progressWrap.style.display = "block";
    setProgress(10, "Figma \uBCC0\uD658 \uC911...");
    parent.postMessage({
      pluginMessage: { type: "CREATE_SLIDES", slides: loadedData, totalSlides: loadedData.length }
    }, "*");
  });
  window.onmessage = function(event) {
    var msg = event.data.pluginMessage;
    if (!msg)
      return;
    if (msg.type === "PROGRESS")
      setProgress(msg.percent, msg.message);
    else if (msg.type === "COMPLETE") {
      setProgress(100, "\uC644\uB8CC!");
      setStatus(msg.slideCount + "\uAC1C \uC2AC\uB77C\uC774\uB4DC \uBCC0\uD658 \uC644\uB8CC!", "success");
      convertBtn.disabled = false;
    } else if (msg.type === "ERROR") {
      setStatus("\uC624\uB958: " + msg.message, "error");
      convertBtn.disabled = false;
    }
  };
  function setStatus(m, t) {
    statusEl.textContent = m;
    statusEl.className = "status " + t;
  }
  function setProgress(p, m) {
    progressFill.style.width = p + "%";
    progressText.textContent = m;
  }
})();
