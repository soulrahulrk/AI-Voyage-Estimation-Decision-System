const form = document.getElementById("voyageForm");
const bannersEl = document.getElementById("banners");
const manualInputs = document.getElementById("manualInputs");
const decisionTag = document.getElementById("decisionTag");
const keyNumbers = document.getElementById("keyNumbers");
const decisionStats = document.getElementById("decisionStats");
const suggestionsEl = document.getElementById("suggestions");
const warningsEl = document.getElementById("warnings");
const risksEl = document.getElementById("risks");
const resetBtn = document.getElementById("resetBtn");

const currencySymbol = { USD: "$", EUR: "€", INR: "₹" };

function formatNumber(value) {
  if (value === null || value === undefined) return "-";
  return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function setDecisionTag(decision) {
  decisionTag.textContent = decision;
  decisionTag.className = "tag";
  if (decision.includes("DO NOT SAIL")) decisionTag.classList.add("danger");
  else if (decision.includes("RISK")) decisionTag.classList.add("warn");
  else if (decision.includes("GO")) decisionTag.classList.add("success");
}

function clearLists() {
  [keyNumbers, decisionStats, suggestionsEl, warningsEl, risksEl].forEach((el) => (el.innerHTML = ""));
  bannersEl.innerHTML = "";
}

function renderList(el, items) {
  if (!items || items.length === 0) {
    const li = document.createElement("li");
    li.textContent = "None";
    el.appendChild(li);
    return;
  }
  items.forEach((txt) => {
    const li = document.createElement("li");
    li.textContent = txt;
    el.appendChild(li);
  });
}

function bannerClass(text) {
  if (text.toLowerCase().includes("distance")) return "yellow";
  if (text.toLowerCase().includes("fuel")) return "red";
  if (text.toLowerCase().includes("risky")) return "orange";
  if (text.toLowerCase().includes("loss")) return "red";
  if (text.toLowerCase().includes("manual")) return "gray";
  return "gray";
}

function renderBanners(list) {
  bannersEl.innerHTML = "";
  list.forEach((txt) => {
    const div = document.createElement("div");
    div.className = `banner ${bannerClass(txt)}`;
    div.textContent = txt;
    bannersEl.appendChild(div);
  });
}

function validateForm(data) {
  let valid = true;
  const errors = form.querySelectorAll(".error");
  errors.forEach((e) => (e.textContent = ""));

  const numericRules = [
    "speed",
    "fuel_consumption",
    "fuel_price",
    "port_charges",
    "freight_income",
    "manual_distance",
    "manual_fuel_cost",
  ];

  Object.entries(data).forEach(([key, val]) => {
    const input = form.querySelector(`[name="${key}"]`);
    if (!input) return;
    const errorEl = input.parentElement.querySelector(".error");

    if (["start_port", "end_port"].includes(key)) {
      if (!val.trim()) {
        errorEl.textContent = "Required";
        valid = false;
      }
    }

    if (numericRules.includes(key) && val !== "" && val !== null) {
      const num = Number(val);
      if (Number.isNaN(num)) return;
      if (num < 0) {
        errorEl.textContent = "Must be non-negative";
        valid = false;
      }
      if (key === "fuel_price" && num === 0) {
        errorEl.textContent = "Fuel price cannot be zero";
        valid = false;
      }
    }
  });

  return valid;
}

async function submitForm(evt) {
  evt.preventDefault();
  clearLists();

  const formData = new FormData(form);
  const payload = Object.fromEntries(formData.entries());

  // Convert numbers
  ["speed", "fuel_consumption", "fuel_price", "port_charges", "freight_income", "manual_distance", "manual_fuel_cost"].forEach((k) => {
    if (payload[k] === "") payload[k] = null;
    else payload[k] = Number(payload[k]);
  });

  if (!validateForm(payload)) return;

  const submitBtn = form.querySelector("button[type=submit]");
  submitBtn.disabled = true;
  submitBtn.textContent = "Estimating...";

  try {
    const res = await fetch("http://localhost:8000/estimate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      setDecisionTag("Server error");
      renderBanners(["Server error. Check backend logs."]);
      return;
    }

    const data = await res.json();
    manualInputs.classList.toggle("hidden", !(data.needs_manual_distance || data.needs_manual_fuel_cost));
    setDecisionTag(data.final_decision);
    renderBanners(data.banners || []);

    const cur = currencySymbol[data.currency] || "";

    keyNumbers.innerHTML = "";
    [
      ["Distance", `${formatNumber(data.distance_nm)} nm`],
      ["Voyage Days", formatNumber(data.voyage_days)],
      ["Total Fuel Used", `${formatNumber(data.total_fuel_used)} tons`],
      ["Total Fuel Cost", `${cur}${formatNumber(data.total_fuel_cost)}`],
      ["Total Expense", `${cur}${formatNumber(data.total_expense)}`],
      ["Profit", `${cur}${formatNumber(data.net_profit)} (${formatNumber(data.profit_percent)}%)`],
    ].forEach(([label, value]) => {
      const li = document.createElement("li");
      li.innerHTML = `<span>${label}</span><span>${value}</span>`;
      keyNumbers.appendChild(li);
    });

    decisionStats.innerHTML = "";
    [
      ["Profit Zone", data.profit_zone || "-"],
      ["Fuel % of Expense", `${formatNumber(data.fuel_percent_of_expense)}%`],
      ["Port % of Expense", `${formatNumber(data.port_percent_of_expense)}%`],
      ["Final Decision", data.final_decision],
    ].forEach(([label, value]) => {
      const li = document.createElement("li");
      li.innerHTML = `<span>${label}</span><span>${value}</span>`;
      decisionStats.appendChild(li);
    });

    renderList(suggestionsEl, data.suggestions || []);
    renderList(warningsEl, data.warnings || []);
    renderList(risksEl, data.risk_flags || []);
  } catch (err) {
    setDecisionTag("Request failed");
    renderBanners(["Could not reach backend. Ensure uvicorn is running on :8000"]);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Estimate Voyage";
  }
}

form.addEventListener("submit", submitForm);
resetBtn.addEventListener("click", () => {
  form.reset();
  manualInputs.classList.add("hidden");
  clearLists();
  setDecisionTag("Awaiting input");
});
