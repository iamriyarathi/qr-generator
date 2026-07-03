(function () {
  "use strict";

  const body = document.getElementById("historyBody");
  const emptyState = document.getElementById("emptyState");
  const wrap = document.querySelector(".history-table-wrap");
  const searchInput = document.getElementById("searchInput");
  const filterChips = document.getElementById("filterChips");

  let currentSearch = "";
  let currentType = "";
  let debounceTimer = null;

  const TYPE_LABELS = {
    url: "URL", text: "Text", email: "Email", phone: "Phone", sms: "SMS",
    whatsapp: "WhatsApp", wifi: "WiFi", location: "Location", vcard: "Contact",
  };

  function formatDate(iso) {
    try {
      const d = new Date(iso.replace(" ", "T") + "Z");
      return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) +
        " · " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
    } catch (e) {
      return iso;
    }
  }

  async function loadHistory() {
    const params = new URLSearchParams();
    if (currentSearch) params.set("search", currentSearch);
    if (currentType) params.set("type", currentType);

    const res = await fetch("/api/history?" + params.toString());
    const data = await res.json();
    if (!data.success) return;

    body.innerHTML = "";
    if (data.items.length === 0) {
      wrap.style.display = "none";
      emptyState.style.display = "block";
      return;
    }
    wrap.style.display = "block";
    emptyState.style.display = "none";

    data.items.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML =
        '<td><div class="thumb-cell"><img loading="lazy" src="/api/thumb/' + item.id + '" alt=""></div></td>' +
        '<td><span class="type-badge">' + (TYPE_LABELS[item.qr_type] || item.qr_type) + "</span></td>" +
        '<td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + escapeHtml(item.user_input) + "</td>" +
        "<td>" + formatDate(item.created_date) + "</td>" +
        "<td>" + item.download_count + "</td>" +
        '<td><div class="row-actions">' +
        '<button title="Download PNG" data-action="download" data-id="' + item.id + '"><i class="fa-solid fa-download"></i></button>' +
        '<button title="Delete" class="danger" data-action="delete" data-id="' + item.id + '"><i class="fa-solid fa-trash"></i></button>' +
        "</div></td>";
      body.appendChild(tr);
    });
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  body.addEventListener("click", async (e) => {
    const btn = e.target.closest("button[data-action]");
    if (!btn) return;
    const id = btn.dataset.id;

    if (btn.dataset.action === "download") {
      const a = document.createElement("a");
      a.href = "/api/download/" + id + "/png";
      a.click();
      showToast("Downloading QR code…", "info");
    }

    if (btn.dataset.action === "delete") {
      if (!confirm("Delete this QR code from history? This can't be undone.")) return;
      const res = await fetch("/api/history/" + id, { method: "DELETE" });
      const data = await res.json();
      if (data.success) {
        showToast("QR code deleted.", "success");
        loadHistory();
      } else {
        showToast("Couldn't delete that item.", "error");
      }
    }
  });

  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      currentSearch = searchInput.value.trim();
      loadHistory();
    }, 300);
  });

  filterChips.addEventListener("click", (e) => {
    const chip = e.target.closest(".filter-chip");
    if (!chip) return;
    filterChips.querySelectorAll(".filter-chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    currentType = chip.dataset.type;
    loadHistory();
  });

  loadHistory();
})();
