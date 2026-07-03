(function () {
  "use strict";

  const form = document.getElementById("qrForm");
  const typeTabs = document.getElementById("typeTabs");
  let currentType = "url";
  let currentId = null;
  let logoDataUrl = null;

  /* ---------------- Type tabs ---------------- */
  typeTabs.addEventListener("click", function (e) {
    const btn = e.target.closest(".type-tab");
    if (!btn) return;
    document.querySelectorAll(".type-tab").forEach((t) => t.classList.remove("active"));
    btn.classList.add("active");
    currentType = btn.dataset.type;
    document.querySelectorAll(".field-group").forEach((g) => {
      g.classList.toggle("active", g.dataset.group === currentType);
    });
    clearErrors();
  });

  // Deep-link support: /generator#type=wifi
  const hashMatch = window.location.hash.match(/type=([a-z]+)/);
  if (hashMatch) {
    const tab = document.querySelector('.type-tab[data-type="' + hashMatch[1] + '"]');
    if (tab) tab.click();
  }

  /* ---------------- Customization: size / border sliders ---------------- */
  const sizeInput = document.getElementById("size");
  const sizeValue = document.getElementById("sizeValue");
  sizeInput.addEventListener("input", () => (sizeValue.textContent = sizeInput.value + "px"));

  const borderInput = document.getElementById("border");
  const borderValue = document.getElementById("borderValue");
  borderInput.addEventListener("input", () => (borderValue.textContent = borderInput.value));

  /* ---------------- Colors ---------------- */
  function bindColor(pickerId, hexId) {
    const picker = document.getElementById(pickerId);
    const hex = document.getElementById(hexId);
    const swatch = picker.closest(".color-swatch");
    picker.addEventListener("input", () => {
      hex.value = picker.value;
      swatch.style.background = picker.value;
    });
    hex.addEventListener("input", () => {
      let v = hex.value.trim();
      if (/^#[0-9a-fA-F]{6}$/.test(v)) {
        picker.value = v;
        swatch.style.background = v;
      }
    });
  }
  bindColor("fg_color", "fg_color_hex");
  bindColor("bg_color", "bg_color_hex");

  /* ---------------- Error correction chips ---------------- */
  const ecOptions = document.getElementById("ecOptions");
  let currentEc = "M";
  ecOptions.addEventListener("click", (e) => {
    const opt = e.target.closest(".ec-option");
    if (!opt) return;
    ecOptions.querySelectorAll(".ec-option").forEach((o) => o.classList.remove("active"));
    opt.classList.add("active");
    currentEc = opt.dataset.ec;
  });

  /* ---------------- Logo upload ---------------- */
  const logoInput = document.getElementById("logo");
  const logoBtn = document.getElementById("logoBtn");
  const logoPreview = document.getElementById("logoPreview");
  logoBtn.addEventListener("click", () => logoInput.click());
  logoInput.addEventListener("change", () => {
    const file = logoInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      logoDataUrl = e.target.result;
      logoPreview.innerHTML = "";
      const img = document.createElement("img");
      img.src = logoDataUrl;
      logoPreview.appendChild(img);
    };
    reader.readAsDataURL(file);
  });

  /* ---------------- Location helper ---------------- */
  const useMyLocation = document.getElementById("useMyLocation");
  if (useMyLocation) {
    useMyLocation.addEventListener("click", () => {
      if (!navigator.geolocation) {
        showToast("Geolocation isn't supported in this browser.", "error");
        return;
      }
      useMyLocation.disabled = true;
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          document.getElementById("latitude").value = pos.coords.latitude.toFixed(6);
          document.getElementById("longitude").value = pos.coords.longitude.toFixed(6);
          useMyLocation.disabled = false;
          showToast("Location captured.", "success");
        },
        () => {
          useMyLocation.disabled = false;
          showToast("Couldn't access your location.", "error");
        }
      );
    });
  }

  /* ---------------- Errors ---------------- */
  function clearErrors() {
    document.querySelectorAll(".field-error").forEach((el) => {
      el.textContent = "";
      el.classList.remove("show");
    });
    document.querySelectorAll("input.invalid, textarea.invalid").forEach((el) => el.classList.remove("invalid"));
  }

  function showErrors(errors) {
    clearErrors();
    Object.keys(errors).forEach((field) => {
      const el = document.querySelector('[data-error-for="' + field + '"]');
      if (el) {
        el.textContent = errors[field];
        el.classList.add("show");
      }
      const input = form.querySelector('[name="' + field + '"]');
      if (input) input.classList.add("invalid");
    });
    const firstMsg = errors._ || Object.values(errors)[0];
    if (firstMsg) showToast(firstMsg, "error");
  }

  /* ---------------- Preview elements ---------------- */
  const previewImg = document.getElementById("previewImg");
  const previewEmpty = document.getElementById("previewEmpty");
  const previewLoading = document.getElementById("previewLoading");
  const previewType = document.getElementById("previewType");
  const previewEc = document.getElementById("previewEc");
  const downloadPng = document.getElementById("downloadPng");
  const downloadSvg = document.getElementById("downloadSvg");
  const downloadJpg = document.getElementById("downloadJpg");
  const printBtn = document.getElementById("printBtn");

  function setLoading(on) {
    previewLoading.classList.toggle("show", on);
  }

  /* ---------------- Generate ---------------- */
  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    clearErrors();
    setLoading(true);

    const fd = new FormData();
    fd.append("qr_type", currentType);

    form.querySelectorAll(".field-group.active input, .field-group.active textarea, .field-group.active select").forEach((el) => {
      if (el.type === "checkbox") {
        fd.append(el.name, el.checked ? "true" : "false");
      } else if (el.name) {
        fd.append(el.name, el.value);
      }
    });

    fd.append("size", sizeInput.value);
    fd.append("fg_color", document.getElementById("fg_color").value);
    fd.append("bg_color", document.getElementById("bg_color").value);
    fd.append("border", borderInput.value);
    fd.append("error_correction", currentEc);
    fd.append("rounded", document.getElementById("rounded").checked ? "true" : "false");
    fd.append("transparent", document.getElementById("transparent").checked ? "true" : "false");

    if (logoInput.files[0]) fd.append("logo", logoInput.files[0]);

    const generateBtn = document.getElementById("generateBtn");
    generateBtn.disabled = true;

    try {
      const res = await fetch("/api/generate", { method: "POST", body: fd });
      const data = await res.json();

      if (!data.success) {
        showErrors(data.errors || { _: "Something went wrong. Please try again." });
        return;
      }

      currentId = data.id;
      previewImg.src = data.preview;
      previewImg.style.display = "block";
      previewEmpty.style.display = "none";
      previewType.textContent = data.qr_type.toUpperCase();
      previewEc.textContent = "Error correction: " + data.error_correction_used;

      [downloadPng, downloadSvg, downloadJpg, printBtn].forEach((b) => (b.disabled = false));
      showToast("QR code generated and saved to history.", "success");
    } catch (err) {
      showToast("Network error — please try again.", "error");
    } finally {
      setLoading(false);
      generateBtn.disabled = false;
    }
  });

  /* ---------------- Downloads / print ---------------- */
  function triggerDownload(fmt) {
    if (!currentId) return;
    const a = document.createElement("a");
    a.href = "/api/download/" + currentId + "/" + fmt;
    a.click();
  }
  downloadPng.addEventListener("click", () => triggerDownload("png"));
  downloadSvg.addEventListener("click", () => triggerDownload("svg"));
  downloadJpg.addEventListener("click", () => triggerDownload("jpg"));

  printBtn.addEventListener("click", () => {
    if (!previewImg.src) return;
    const w = window.open("", "_blank");
    w.document.write(
      '<html><head><title>Print QR code</title></head><body style="display:flex;align-items:center;justify-content:center;height:100vh;margin:0;">' +
        '<img src="' + previewImg.src + '" style="max-width:80%;max-height:80%;" onload="window.print();"></body></html>'
    );
    w.document.close();
  });

  /* ---------------- Copy input / reset ---------------- */
  document.getElementById("copyInputBtn").addEventListener("click", async () => {
    const activeGroup = document.querySelector(".field-group.active");
    const values = [];
    activeGroup.querySelectorAll("input, textarea, select").forEach((el) => {
      if (el.value && el.type !== "checkbox") values.push(el.value);
    });
    const text = values.join(" | ");
    if (!text) {
      showToast("Nothing to copy yet.", "info");
      return;
    }
    try {
      await navigator.clipboard.writeText(text);
      showToast("Input copied to clipboard.", "success");
    } catch (e) {
      showToast("Couldn't copy — please copy manually.", "error");
    }
  });

  document.getElementById("resetBtn").addEventListener("click", () => {
    form.reset();
    clearErrors();
    currentId = null;
    logoDataUrl = null;
    logoPreview.innerHTML = '<i class="fa-solid fa-image" style="color:var(--text-faint);"></i>';
    previewImg.style.display = "none";
    previewEmpty.style.display = "block";
    previewType.textContent = "—";
    previewEc.textContent = "—";
    [downloadPng, downloadSvg, downloadJpg, printBtn].forEach((b) => (b.disabled = true));
    sizeValue.textContent = "400px";
    borderValue.textContent = "4";
    ecOptions.querySelectorAll(".ec-option").forEach((o) => o.classList.remove("active"));
    document.querySelector('.ec-option[data-ec="M"]').classList.add("active");
    currentEc = "M";
    document.querySelector('.color-swatch').style.background = "#000000";
    document.querySelectorAll('.color-swatch')[1].style.background = "#ffffff";
    showToast("Form reset.", "info");
  });
})();
