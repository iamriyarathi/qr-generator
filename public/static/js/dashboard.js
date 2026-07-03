(function () {
  "use strict";

  const TYPE_LABELS = {
    url: "URL", text: "Text", email: "Email", phone: "Phone", sms: "SMS",
    whatsapp: "WhatsApp", wifi: "WiFi", location: "Location", vcard: "Contact",
  };

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function timeAgo(iso) {
    try {
      const then = new Date(iso.replace(" ", "T") + "Z").getTime();
      const diff = Math.max(0, Date.now() - then);
      const mins = Math.floor(diff / 60000);
      if (mins < 1) return "just now";
      if (mins < 60) return mins + "m ago";
      const hrs = Math.floor(mins / 60);
      if (hrs < 24) return hrs + "h ago";
      return Math.floor(hrs / 24) + "d ago";
    } catch (e) {
      return "";
    }
  }

  async function loadStats() {
    const res = await fetch("/api/stats");
    const data = await res.json();
    if (!data.success) return;
    const s = data.stats;

    document.getElementById("statTotal").textContent = s.total;
    document.getElementById("statToday").textContent = s.today;
    document.getElementById("statMostUsed").textContent = s.most_used_type === "—" ? "—" : (TYPE_LABELS[s.most_used_type] || s.most_used_type);
    document.getElementById("statDownloads").textContent = s.total_downloads;

    const breakdown = document.getElementById("typeBreakdown");
    if (s.by_type.length === 0) {
      breakdown.innerHTML = '<p class="mono-small">No data yet — generate a QR code to see stats.</p>';
    } else {
      const max = Math.max(...s.by_type.map((t) => t.c));
      breakdown.innerHTML = s.by_type
        .map((t) => {
          const pct = max ? Math.round((t.c / max) * 100) : 0;
          return (
            '<div class="type-bar-row"><div class="type-bar-label"><span>' +
            (TYPE_LABELS[t.qr_type] || t.qr_type) +
            "</span><span>" + t.c + "</span></div>" +
            '<div class="type-bar-track"><div class="type-bar-fill" style="width:' + pct + '%;"></div></div></div>'
          );
        })
        .join("");
    }

    const recent = document.getElementById("recentActivity");
    if (s.recent.length === 0) {
      recent.innerHTML = '<p class="mono-small">No recent activity.</p>';
    } else {
      recent.innerHTML = s.recent
        .map(
          (item) =>
            '<div class="activity-item"><img loading="lazy" src="/api/thumb/' + item.id + '" alt="">' +
            '<div class="meta"><b>' + escapeHtml(item.user_input) + "</b>" +
            "<span>" + (TYPE_LABELS[item.qr_type] || item.qr_type) + " · " + timeAgo(item.created_date) + "</span></div></div>"
        )
        .join("");
    }
  }

  loadStats();
})();
