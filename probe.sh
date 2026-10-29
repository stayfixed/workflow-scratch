#!/bin/sh
# IS2 Check 3: what a custom gate reaches. Prints names only, never values.
echo "probe: env names: $(env | sed 's/=.*//' | sort | tr '\n' ' ')"
for f in .git/config ../stayfixed/.git/config; do
  if [ -f "$f" ]; then
    echo "probe: $f extraheader/credential lines: $(grep -ciE 'extraheader|credential' "$f")"
  else
    echo "probe: $f absent"
  fi
done
echo "probe: GITHUB_STEP_SUMMARY set: ${GITHUB_STEP_SUMMARY:+yes}"
echo "probe: GITHUB_OUTPUT set: ${GITHUB_OUTPUT:+yes}; GITHUB_ENV set: ${GITHUB_ENV:+yes}"
echo "::error::probe-annotation"
if [ "${PROBE_PLAIN:-}" != 1 ]; then echo "::stop-commands::probe-token"; fi
echo "::error::after-stop"
if [ "${PROBE_PLAIN:-}" != 1 ]; then echo "::probe-token::"; fi
[ -n "${GITHUB_STEP_SUMMARY:-}" ] && echo "probe summary line" >> "$GITHUB_STEP_SUMMARY"
[ -n "${GITHUB_OUTPUT:-}" ] && echo "probe=1" >> "$GITHUB_OUTPUT"
[ -n "${GITHUB_ENV:-}" ] && echo "PROBE=1" >> "$GITHUB_ENV"
exit 0
