/*
 * ShopSafe Lab - inert laboratory resource.
 *
 * This file is intentionally benign. It exists only to demonstrate that a
 * request for a non-approved resource path appears in the access log and can
 * be compared against the legitimate site's approved-resource allowlist.
 *
 * It deliberately does NOT:
 *   - read or write browser storage of any kind,
 *   - access authentication data,
 *   - fingerprint the browser,
 *   - make any network request,
 *   - load or evaluate remote code,
 *   - contain obfuscated logic.
 */
(function () {
    "use strict";

    var markerId = "lab-resource-marker";

    function applyMarker() {
        var el = document.getElementById(markerId);
        if (el) {
            el.textContent = "Lab resource loaded: unapproved.js (inert, same-origin).";
            el.classList.add("lab-resource-active");
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", applyMarker);
    } else {
        applyMarker();
    }

    // Harmless console notice for laboratory observation.
    if (window.console && typeof window.console.log === "function") {
        window.console.log("[ShopSafe Lab] inert lab resource loaded: /lab-test/resources/unapproved.js");
    }
})();
