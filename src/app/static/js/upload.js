// Upload page: show the chosen file, support drag and drop,
// and show the loading overlay while the analysis runs.

const input = document.getElementById("file-input");
const zone = document.getElementById("dropzone");
const text = document.getElementById("dz-text");
const button = document.getElementById("analyse-btn");
const form = document.getElementById("upload-form");
const overlay = document.getElementById("loading");

function showFile() {
  if (input.files.length === 0) { return; }
  const f = input.files[0];
  const mb = (f.size / (1024 * 1024)).toFixed(2);
  text.textContent = f.name + "  (" + mb + " MB)";
  button.disabled = false;
}

input.addEventListener("change", showFile);

["dragenter", "dragover"].forEach(function (ev) {
  zone.addEventListener(ev, function (e) { e.preventDefault(); zone.classList.add("over"); });
});
["dragleave", "drop"].forEach(function (ev) {
  zone.addEventListener(ev, function (e) { e.preventDefault(); zone.classList.remove("over"); });
});
zone.addEventListener("drop", function (e) {
  if (e.dataTransfer.files.length > 0) {
    input.files = e.dataTransfer.files;
    showFile();
  }
});

form.addEventListener("submit", function () { overlay.classList.add("show"); });
window.addEventListener("pageshow", function () { overlay.classList.remove("show"); });