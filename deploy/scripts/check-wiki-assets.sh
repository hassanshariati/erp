#!/usr/bin/env bash
# Validate the actual Wiki Vite bundles referenced by the rendered HTML.
# Pure GET requests: usable in disposable site and on live armember.ir.
set -Eeuo pipefail

BASE_URL="${1:?Pass a base URL, e.g. https://armember.ir}"
SITE_HOST="${2:-}"
BASE_URL="${BASE_URL%/}"

CURL=(curl --fail --silent --show-error --location --max-time 20
  --retry 12 --retry-delay 5 --retry-connrefused)
if [[ -n "$SITE_HOST" ]]; then
  CURL+=(-H "Host: $SITE_HOST")
fi

html="$("${CURL[@]}" "$BASE_URL/wiki-app/spaces")"
js_path="$(printf '%s' "$html" | grep -Eo '/assets/wiki/frontend/assets/[^"[:space:]<>]+\.js' | head -n 1 || true)"
css_path="$(printf '%s' "$html" | grep -Eo '/assets/wiki/frontend/assets/[^"[:space:]<>]+\.css' | head -n 1 || true)"
[[ -n "$js_path" ]] || { echo "Wiki page has no Vite JS bundle URL" >&2; exit 1; }
[[ -n "$css_path" ]] || { echo "Wiki page has no Vite CSS bundle URL" >&2; exit 1; }

for path in "$js_path" "$css_path"; do
  content_type="$("${CURL[@]}" --output /dev/null --write-out '%{content_type}' "$BASE_URL$path")"
  case "$path" in
    *.js)
      [[ "$content_type" == *javascript* ]] || {
        echo "Wiki JS not served with JavaScript MIME: $path ($content_type)" >&2; exit 1;
      }
      ;;
    *.css)
      [[ "$content_type" == text/css* ]] || {
        echo "Wiki CSS not served with CSS MIME: $path ($content_type)" >&2; exit 1;
      }
      ;;
  esac
  echo "Wiki asset healthy: $path ($content_type)"
done

echo "Wiki HTML, real JS bundle and real CSS bundle verified."
