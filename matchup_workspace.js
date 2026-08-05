(() => {
  "use strict";

  const CANONICAL_PAGE = "openers.html";

  function normalizeGameId(value) {
    const text = String(value ?? "").trim();
    return text || null;
  }

  function canonicalUrl(gameId, section) {
    const id = normalizeGameId(gameId);
    if (!id) return null;
    const url = new URL(CANONICAL_PAGE, window.location.href);
    url.searchParams.set("game_id", id);
    if (section) url.hash = String(section).replace(/^#/, "");
    return url.href;
  }

  function openCanonicalMatchup(gameId, section) {
    const url = canonicalUrl(gameId, section);
    if (!url) return false;
    window.location.assign(url);
    return true;
  }

  function gameIdFromElement(target) {
    if (!target) return null;
    const row = target.closest?.("tr");
    const direct = [
      target.dataset?.matchupId,
      target.dataset?.gameId,
      target.dataset?.id,
      row?.dataset?.matchupId,
      row?.dataset?.gameId,
      row?.dataset?.id,
      row?.dataset?.game,
    ].find(Boolean);
    if (direct) return String(direct);

    const link = target.closest?.('a[href*="game_id="]') ||
      row?.querySelector?.('a[href*="game_id="]');
    if (link) {
      try {
        return new URL(link.getAttribute("href"), window.location.href)
          .searchParams.get("game_id");
      } catch (_) {}
    }

    const attrs = [
      target.getAttribute?.("onclick") || "",
      row?.getAttribute?.("onclick") || "",
      target.closest?.("a[href]")?.getAttribute("href") || "",
    ].join(" ");

    const call = attrs.match(
      /(?:openDrawer|openGame|openMatchupWorkspace|showMatchup|openWorkspace)\s*\(\s*['"]([^'"]+)['"]/i
    );
    if (call) return call[1];

    const gid = attrs.match(/\b(g\d+)\b/i);
    return gid ? gid[1] : null;
  }

  function canonicalizeLinks(root = document) {
    root.querySelectorAll?.('a[href*="game_id="]').forEach((link) => {
      try {
        const url = new URL(link.getAttribute("href"), window.location.href);
        const id = url.searchParams.get("game_id");
        if (!id) return;
        if (url.pathname.endsWith("/matchups.html") ||
            url.pathname.endsWith("/openers.html") ||
            url.pathname.endsWith("/index.html")) {
          link.href = canonicalUrl(id);
        }
      } catch (_) {}
    });
  }

  document.addEventListener("click", (event) => {
    const target = event.target;
    const link = target.closest?.('a[href*="game_id="]');
    if (link) {
      try {
        const url = new URL(link.getAttribute("href"), window.location.href);
        const id = url.searchParams.get("game_id");
        if (id && !url.pathname.endsWith("/matchup.html")) {
          event.preventDefault();
          event.stopPropagation();
          event.stopImmediatePropagation();
          openCanonicalMatchup(id, target.dataset?.matchupSection);
          return;
        }
      } catch (_) {}
    }

    const row = target.closest?.("tr");
    if (!row || row.closest("thead")) return;
    if (target.closest("input,select,textarea,label")) return;

    const button = target.closest("button");
    const explicit = button?.matches(
      ".open,.open-matchup,.matchup-open,[data-open-matchup],[data-matchup-id],[data-game-id]"
    );
    const arrow = button && ["›", ">", "→"].includes((button.textContent || "").trim());
    if (button && !explicit && !arrow) return;

    const id = gameIdFromElement(target);
    if (!id) return;

    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();
    openCanonicalMatchup(id, target.dataset?.matchupSection);
  }, true);

  // Compatibility API for older generated pages. These names now navigate to
  // the one canonical full matchup report instead of opening a second renderer.
  const pageName = (window.location.pathname.split("/").pop() || "").toLowerCase();
  const isCanonicalOpenersPage =
    pageName === "openers.html" || pageName === "openers_v2.html";

  window.openMatchupWorkspace = openCanonicalMatchup;

  // Openers owns its native drawer functions. Overriding them here causes
  // openers.html?game_id=... to reload itself instead of opening the drawer.
  if (!isCanonicalOpenersPage) {
    window.openDrawer = openCanonicalMatchup;
    window.openGame = openCanonicalMatchup;
    window.showMatchup = openCanonicalMatchup;
    window.openWorkspace = openCanonicalMatchup;
    window.closeDrawer = () => {};
  }

  window.closeMatchupWorkspace = () => {};

  const params = new URLSearchParams(window.location.search);
  const linkedGameId = params.get("game_id");
  if (linkedGameId && /\/(matchups|matchup)\.html$/i.test(window.location.pathname)) {
    window.location.replace(canonicalUrl(linkedGameId));
    return;
  }

  canonicalizeLinks();
  new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node.nodeType === 1) canonicalizeLinks(node);
      }
    }
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
