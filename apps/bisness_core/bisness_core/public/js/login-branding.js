/* Per-site branding on Frappe's native login. Never modify authentication. */
(() => {
  "use strict";
  const endpoint = "/api/method/bisness_core.api.branding.get_login_branding";

  function publicAsset(url, version) {
    if (typeof url !== "string" || !url.startsWith("/")) return "";
    try {
      const parsed = new URL(url, window.location.origin);
      if (parsed.origin !== window.location.origin) return "";
      if (!parsed.pathname.startsWith("/files/") && !parsed.pathname.startsWith("/assets/")) return "";
      if (parsed.pathname.includes("..") || parsed.search || parsed.hash) return "";
      if (typeof version === "string" && /^[0-9a-f]{12}$/.test(version)) {
        parsed.searchParams.set("v", version);
      }
      return parsed.href;
    } catch (_) {
      return "";
    }
  }

  function element(tag, className, parent) {
    const node = document.createElement(tag);
    node.className = className;
    if (parent) parent.appendChild(node);
    return node;
  }

  function init() {
    const root = document.querySelector("#page-login");
    const layout = root && root.querySelector(".page_content > div");
    if (!layout || layout.querySelector(".bisness-login-hero")) return false;

    const hero = element("aside", "bisness-login-hero");
    hero.setAttribute("aria-label", "Product branding");
    const stage = element("div", "bisness-login-hero-stage", hero);
    element("span", "bisness-login-orbit bisness-login-orbit--outer", stage).setAttribute("aria-hidden", "true");
    element("span", "bisness-login-orbit bisness-login-orbit--inner", stage).setAttribute("aria-hidden", "true");
    const mark = element("img", "bisness-login-mark", stage);
    mark.src = "/assets/bisness_core/images/login-mark.svg";
    mark.alt = "";
    mark.setAttribute("aria-hidden", "true");

    const brandName = element("strong", "bisness-login-brand-name", hero);
    brandName.textContent = "Business Platform";
    const tagline = element("p", "bisness-login-brand-tagline", hero);
    tagline.textContent = "One connected workspace";

    layout.classList.add("bisness-login-has-hero");
    layout.prepend(hero);

    fetch(endpoint, { credentials: "same-origin", cache: "no-store" })
      .then((response) => {
        if (!response.ok) throw new Error("Branding unavailable");
        return response.json();
      })
      .then((payload) => {
        const settings = payload && payload.message;
        if (!settings || typeof settings !== "object") return;
        const name = typeof settings.brand_name === "string" ? settings.brand_name.trim() : "";
        brandName.textContent = name || "Business Platform";
        hero.setAttribute("aria-label", brandName.textContent);
        const subtitle = typeof settings.brand_tagline === "string" ? settings.brand_tagline.trim() : "";
        tagline.textContent = subtitle;
        tagline.hidden = !subtitle;

        if (typeof settings.accent_color === "string" && /^#[0-9a-fA-F]{6}$/.test(settings.accent_color)) {
          root.style.setProperty("--bisness-green", settings.accent_color);
          root.style.setProperty("--bisness-green-strong", settings.accent_color);
        }

        const logoUrl = publicAsset(settings.logo_url, settings.logo_version);
        if (logoUrl) {
          mark.src = logoUrl;
          root.querySelectorAll(".page-card-head .app-logo").forEach((logo) => {
            logo.src = logoUrl;
          });
        }

        const mediaUrl = publicAsset(settings.media_url, settings.media_version);
        if (!mediaUrl) return;
        let media;
        if (settings.media_kind === "video") {
          media = element("video", "bisness-login-uploaded-media");
          media.muted = true;
          media.defaultMuted = true;
          media.loop = true;
          media.playsInline = true;
          media.preload = "auto";
          const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
          media.autoplay = !reduced;
          media.controls = Boolean(reduced);
          media.addEventListener("loadeddata", () => {
            stage.replaceChildren(media);
            hero.classList.add("bisness-login-hero--uploaded");
            if (!reduced) media.play().catch(() => {});
          }, { once: true });
        } else if (settings.media_kind === "image") {
          media = element("img", "bisness-login-uploaded-media");
          media.alt = "";
          media.decoding = "async";
          media.addEventListener("load", () => {
            stage.replaceChildren(media);
            hero.classList.add("bisness-login-hero--uploaded");
          }, { once: true });
        } else {
          return;
        }
        // Keep the animated default intact until the uploaded media has loaded.
        media.src = mediaUrl;
      })
      .catch(() => {
        // A branding failure must never prevent native Frappe login.
      });
    return true;
  }

  // Frappe may render the login container after the website bundle executes.
  // Observe only until the login page is present, not the entire session.
  const observer = new MutationObserver(() => {
    if (init()) observer.disconnect();
  });
  if (document.documentElement) {
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => {
      if (init()) observer.disconnect();
    }, { once: true });
  } else if (init()) {
    observer.disconnect();
  }
})();
