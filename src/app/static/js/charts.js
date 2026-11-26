// Results page: the View charts / Hide charts button.
// plotly.js is loaded earlier in the page (see partials/_charts.html).

const toggle = document.getElementById("toggle-charts");
const box = document.getElementById("charts-box");

function fit() {
  document.querySelectorAll("#charts-box .js-plotly-plot").forEach(function (el) {
    Plotly.Plots.resize(el);
  });
}

toggle.addEventListener("click", function () {
  const opening = !box.classList.contains("open");
  box.classList.toggle("open", opening);
  toggle.textContent = opening ? "Hide charts" : "View charts";
  toggle.setAttribute("aria-expanded", opening ? "true" : "false");
  if (opening) {
    // Plotly sizes charts wrongly inside a hidden box, so resize once it is visible.
    requestAnimationFrame(fit);
    setTimeout(fit, 200);
    box.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});