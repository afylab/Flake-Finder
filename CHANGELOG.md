# Changelog

Notable changes to FlakeIdentifier. The scan program's version is shown in its window and logs (`py-YYYY-MM-DD<letter>`).

## py-2026-11-19a

- **Oxide way off the one entered: a message at once.** When the oxide measured from a chip's substrate colour is more
  than 20 % from the one entered (or fits no oxide), the analysis skips that chip, as before. Until now the scan program
  only said so when the whole analysis had ended. Now a window names the chip, the oxide entered and the one measured,
  as soon as it is measured. The other chips go on.
- **Wrong wafer recognised.** When the substrate's colour is that of another calibrated wafer (for example 285 nm entered
  for a 90 nm chip), the check says "looks like 90 nm SiO2, not the 285 nm entered" instead of "the light is not as
  calibrated". This applies both to the window before each chip's scan, now titled "Oxide does not match the one
  entered", and to the analysis.
- **Viewer:**
  - The header shows the oxide measured and entered ("SiO₂ 272.5 nm measured (285 nm entered)").
  - The rhombohedral colour-path shift (e.g. −12.5 nm) is no longer in the header, where it was read as the oxide; it
    is in the header's hover text.
  - The flake table is in nm only: with rhombohedral screening the t 10x / t 100x columns showed layer counts (24 for
    8.2 nm). The headers say (nm), and the 100x thickness has its colour swatch too.
  - The "coordinates remeasured" hover text no longer shows "undefined" for remeasures done in passes.

## py-2026-11-16a

- The coordinate check (every 100x picture visited again in passes until two agreed, then the coordinates moved) is
  replaced by the **first-flake check**: after the 100x imaging, the run's first (focused) 100x picture is found again
  at its position and its offset from where it was taken is reported (over 5 µm: flagged). Nothing is moved.
  `coord_check_agree_frac` and `coord_check_max_passes` are no longer used (still accepted in settings files).
- **Update available** banner: the program asks GitHub for a newer version at the start and every 30 minutes; while
  there is one, a banner at the top of the main window and of the start screen (with its own Update...).
- Update: an expired token (or one made for the old private repository) no longer stops an update from the public
  repository: it is read without the token.

## py-2026-11-15a

- One chip the analysis cannot handle no longer costs the rest of the run. A near-bare chip (nothing to focus on or to
  register its tiles by) made the tile layout fit fail with `LinAlgError: Singular matrix`, which stopped the whole
  analysis: the chips after it got no target list, and no chip got its 100x pictures in its viewer.
  - The analysis places such tiles by their stage positions (as for too few overlapping pairs).
  - A chip that still fails is skipped (`<chip>_targets_failed.json` in the run folder); the analysis goes on with the
    next chips and exports every chip's 100x pictures.
  - The scan program stops waiting for that chip's list at once, and once the analysis has ended it no longer waits
    for the target lists of the chips after it.

## Unreleased

- First public version.
