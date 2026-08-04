#!/usr/bin/env python3
from pathlib import Path
import re

TARGETS = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

for path in TARGETS:
    if not path.exists():
        continue

    s = path.read_text(errors="ignore")

    # ------------------------------------------------------------
    # 1. Expose existing page-specific functions globally.
    # ------------------------------------------------------------

    # Home Command Center's internal mount().
    home_marker = """  function schedule(){
    setTimeout(() => mount('current'), 50);"""
    if home_marker in s and "window.mountHomeCommandCenterNative = mount;" not in s:
        s = s.replace(
            home_marker,
            """  window.mountHomeCommandCenterNative = mount;

  function schedule(){
    setTimeout(() => mount('current'), 50);""",
            1,
        )

    # Old-dashboard cleanup function.
    cleanup_marker = """  function schedule(){
    setTimeout(cleanup, 50);
    setTimeout(cleanup, 250);
    setTimeout(cleanup, 800);
  }

  const oldRender = window.render;"""
    if cleanup_marker in s:
        s = s.replace(
            cleanup_marker,
            """  window.cleanupHomeAfterCommandCenterNative = cleanup;

  function schedule(){
    setTimeout(cleanup, 50);
    setTimeout(cleanup, 250);
    setTimeout(cleanup, 800);
  }

  const oldRender = window.render;""",
            1,
        )

    # Home Command Center row/logo enhancement.
    polish_marker = """  function schedule(){
    setTimeout(enhanceRows, 50);
    setTimeout(enhanceRows, 250);
    setTimeout(enhanceRows, 800);
  }

  const oldRender = window.render;"""
    if polish_marker in s:
        s = s.replace(
            polish_marker,
            """  window.polishHomeCommandCenterNative = enhanceRows;

  function schedule(){
    setTimeout(enhanceRows, 50);
    setTimeout(enhanceRows, 250);
    setTimeout(enhanceRows, 800);
  }

  const oldRender = window.render;""",
            1,
        )

    # ------------------------------------------------------------
    # 2. Remove the four full-site render wrappers.
    # ------------------------------------------------------------

    wrapper_patterns = [
        # Simulations wrapper.
        r"""
  const oldRender = window\.render;
  if \(typeof oldRender === 'function' && !oldRender\.__simBoardMountWrapped\) \{
    const wrapped = function\(\)\{
      const result = oldRender\.apply\(this, arguments\);
      if \(location\.hash === '#simulations'\) setTimeout\(\(\) => \{
        if \(typeof mountSimulationsPage === 'function'\) mountSimulationsPage\(\);
      \}, 0\);
      return result;
    \};
    wrapped\.__simBoardMountWrapped = true;
    window\.render = wrapped;
  \}

  window\.addEventListener\('hashchange', \(\) => \{
    if \(location\.hash === '#simulations'\) setTimeout\(\(\) => \{
      if \(typeof mountSimulationsPage === 'function'\) mountSimulationsPage\(\);
    \}, 50\);
  \}\);
""",

        # Home Command Center wrapper/listeners.
        r"""
  const oldRender = window\.render;
  if \(typeof oldRender === 'function' && !oldRender\.__homeCommandCenterWrapped\) \{
    const wrapped = function\(\)\{
      const result = oldRender\.apply\(this, arguments\);
      schedule\(\);
      return result;
    \};
    wrapped\.__homeCommandCenterWrapped = true;
    window\.render = wrapped;
  \}

  window\.addEventListener\('hashchange', schedule\);
  document\.addEventListener\('DOMContentLoaded', schedule\);
  schedule\(\);
""",

        # Old-home cleanup wrapper/listeners.
        r"""
  const oldRender = window\.render;
  if \(typeof oldRender === 'function' && !oldRender\.__cleanupHomeAfterCommandCenterWrapped\) \{
    const wrapped = function\(\)\{
      const result = oldRender\.apply\(this, arguments\);
      schedule\(\);
      return result;
    \};
    wrapped\.__cleanupHomeAfterCommandCenterWrapped = true;
    window\.render = wrapped;
  \}

  window\.addEventListener\('hashchange', schedule\);
  document\.addEventListener\('DOMContentLoaded', schedule\);
  schedule\(\);
""",

        # Home polish wrapper/listeners.
        r"""
  const oldRender = window\.render;
  if \(typeof oldRender === 'function' && !oldRender\.__polishHomeCommandCenterUIWrapped\) \{
    const wrapped = function\(\)\{
      const result = oldRender\.apply\(this, arguments\);
      schedule\(\);
      return result;
    \};
    wrapped\.__polishHomeCommandCenterUIWrapped = true;
    window\.render = wrapped;
  \}

  window\.addEventListener\('hashchange', schedule\);
  document\.addEventListener\('DOMContentLoaded', schedule\);
  schedule\(\);
""",
    ]

    for pattern in wrapper_patterns:
        s = re.sub(pattern, "\n", s, flags=re.X)

    # ------------------------------------------------------------
    # 3. Add direct page mounts to the native router.
    # ------------------------------------------------------------

    native_mounts = """  if (hash==='#simulations' && typeof mountSimulationsPage === 'function') {
    mountSimulationsPage();
  }

  if (hash==='#/' || hash==='' || hash==='#home') {
    if (typeof window.mountHomeCommandCenterNative === 'function') {
      window.mountHomeCommandCenterNative('current');
    }
    if (typeof window.cleanupHomeAfterCommandCenterNative === 'function') {
      window.cleanupHomeAfterCommandCenterNative();
    }
    if (typeof window.polishHomeCommandCenterNative === 'function') {
      window.polishHomeCommandCenterNative();
    }
  }
"""

    insertion_point = """  if (hash==='#betting') mountBettingFilters();
}"""

    if "mountHomeCommandCenterNative('current')" not in s:
        if insertion_point not in s:
            raise SystemExit(f"native router insertion point not found in {path}")

        s = s.replace(
            insertion_point,
            """  if (hash==='#betting') mountBettingFilters();

""" + native_mounts + """}""",
            1,
        )

    # ------------------------------------------------------------
    # 4. Remove the remaining delayed Dashboard rename routine.
    # Dashboard is already native in buildNav().
    # ------------------------------------------------------------

    s = re.sub(
        r"""
  function renameDashboardNav\(\)\{
    [\s\S]*?
  \}
  document\.addEventListener\('DOMContentLoaded', renameDashboardNav\);
  window\.addEventListener\('hashchange', \(\) => setTimeout\(renameDashboardNav, 100\)\);
  setTimeout\(renameDashboardNav, 100\);
  setTimeout\(renameDashboardNav, 500\);
""",
        "\n",
        s,
        flags=re.X,
    )

    path.write_text(s, encoding="utf-8")
    print(path, "native page mounts consolidated")
