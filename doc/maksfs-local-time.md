# MaksFS: local time in the status bar

## Change

The status bar now shows the OS local time in `HH:MM` beside the existing SLT
clock. Preferences → User Interface → Top Bars has **Show local time**
(**Показывать местное время** in Russian). `MaksFSShowLocalTime` is a global
Boolean setting, enabled by default with `Persist=1`; the existing settings
save/restore mechanism handles persistence and Preferences cancellation.

The hover tooltip contains the full calendar date, 24-hour time and numeric
UTC offset, for example `2026-11-10 02:59 (UTC+0300)`. The offset identifies the
local time zone without ambiguous abbreviations or Windows locale encoding
problems. Conversion uses `localtime_s` on Windows and `localtime_r` elsewhere,
with the system wall clock (`std::time`), independent of simulator corrections.
The zone is not hardcoded or derived from the grid or viewer language.

SLT still uses `time_corrected()`, its existing formats, click action, tooltip
and one-second update timer. One small related fix falls back to the language
format if a saved SLT format is unknown, instead of rendering an empty clock.

The new clock reuses the existing timer. While enabled, it reads the wall clock
on that tick and formats/sets text and tooltip only when the epoch minute
changes (also after enabling). While disabled it returns before reading time.
There are no new threads, timers, network requests, dependencies or accumulating
history. State consists of one text control, a flag and a cached minute.
These are implementation observations, not measured performance results.

The standard, Starlight and Starlight CUI layouts each provide the clock.
Placement uses the resolved SLT rectangle, including language-specific widths.
Toggling reserves/releases 46 logical pixels and repositions balance, menu
search and Omnifilter using their existing positioning paths. Media controls
stay at the same screen positions. The clock follows SLT visibility in
mouselook. Grid-independent code is used in both Second Life and OpenSim;
there are no changes to protocols, grid detection, currency handling or SLT.

## Checks actually performed in Codex Cloud

- `git diff --check`: passed.
- Parsed all nine changed XML files with Python ElementTree: passed.
- Checked every settings map for paired, unique keys and checked the new
  setting's Boolean type, enabled default and persistence: passed.
- Checked the local clock and tooltip template exist in all three English
  skin definitions, with Russian tooltip overrides: passed.
- Compiled and ran a temporary **isolated Linux C++17 harness**, with
  `g++ -Wall -Wextra -Werror`, extracting the two new methods from
  `llstatusbar.cpp`. UI objects were minimal stubs and the wall-clock read
  was replaced with a deterministic timestamp. Passed assertions for:
  `HH:MM`, UTC, Moscow and Kolkata offsets, midnight/date rollover,
  Los Angeles spring/fall DST transitions, same-minute cache suppression,
  disabled-clock early return, reversible/idempotent geometry changes,
  and enabling while SLT is hidden for mouselook.
- Reviewed declarations, `LLPanel::getString` argument types, settings signal
  routing, `LLView::setRect`/`translate` semantics, startup positioning and
  the existing FPS/media/net-stat visibility paths in source.

The isolated harness checks the methods with Linux libc and UI stubs; it is
**not viewer compilation or an interactive UI/integration test**. The temporary
probe files are `/tmp/check_local_time.py` and
`/tmp/maksfs_local_clock_check.cpp` in the task's Cloud environment.

## Limits and checks still needed before leaving draft

No viewer target was compiled. No full Windows build, executable launch,
interactive skin test, Second Life/OpenSim session, persisted-settings restart
test or CPU/memory benchmark was run. No configured build tree
(`CMakeCache.txt`/`compile_commands.json`) or viewer executable was present in
the checkout. The Windows `localtime_s`/CRT formatting path remains untested.
No CI configuration or branding changed; no workflow was manually dispatched.

Suggested target validation:

1. Incrementally compile the viewer on Windows and another supported platform.
   Check tooltip UTC offsets, including DST, against the OS clock.
2. In Second Life and OpenSim, compare SLT before/after and exercise its
   language/12h/24h/seconds settings and click action. Try an invalid saved SLT
   format and confirm the language fallback.
3. Toggle local time, Cancel/Apply Preferences, restart, and verify saved
   visibility. Check the English and Russian Preferences labels.
4. Exercise all three skins, narrow windows and UI scales; toggle FPS, media,
   net stats, menu search, balance and Omnifilter; enter/leave mouselook.
   Confirm clock text fits and there are no overlaps or cumulative shifts.
5. Check midnight, DST and changing the OS zone. Local display refreshes on the
   next minute observed by the existing timer; an OS/runtime that caches zone
   configuration may require restarting the viewer after changing the zone.
6. If overhead needs quantifying, measure identical scenes with the setting
   on/off. No speedup or quantified overhead is claimed by this PR.

For user documentation, add the Top Bars checkbox and explain that the adjacent
clock uses the OS local time while SLT retains its existing behavior.

## Scope

Based on `maksfs-main` at `6dad28a7d853c29e1a477248c5ce47724b0cc327`,
on a separate `codex/local-time-statusbar` branch. The base branch and existing
Draft PR #1 are not modified. This change is submitted as a separate draft;
no merge or auto-merge is requested.
