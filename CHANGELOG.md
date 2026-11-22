# Changelog

Notable changes to FlakeIdentifier. The scan program's version is shown in its window and logs (`py-YYYY-MM-DD<letter>`).

## py-2026-11-21a

- **Faint hBN steps are found.** One- and two-layer steps (about a 1 % colour change on thick hBN) are as large as the
  per-pixel noise, so the debris / step threshold (2.5 % colour) and the fine-terrace levels missed them: flakes with
  many steps kept a large clean area and a high score. A new oriented step-edge filter (`screen100.step_edges`)
  averages the raw red, green and blue contrast (each scaled by its own noise) along ~10 um in thin bands either side
  of each direction and keeps sharp jumps, not smooth background blotches or lines (folds). It does not use the
  thin-film model: on 285 nm oxide the model's predicted colour change per nm is off (the steps show mostly in red and
  green, the model expects blue), and projecting onto it lost most of a step's contrast. Each found edge is carried on
  to the flake edge or the next step (a step cannot end inside a terrace). The edges cut the clean area of the 100x
  score, are drawn in orange in the `_debris` picture and are stored in `_regions.json` (`step_lines`,
  `step_lines_stage_um`). New features `step_n` and `step_len_density` (not used by the screening model until it is
  refitted).

## py-2026-11-19b

- **Loose 1 cm chips: focus on the chip, not the holder.** In each 10x focus point's autofocus sweep, a height counts as
  focus only where at least 15 % of the picture is substrate colour (`focus_min_substrate_af`). The plastic holder in
  focus beside the chip no longer wins; with no such height the point is tried further in. Other chip types and the 100x
  autofocus are unchanged.
- **Skip all** in the 100x windows that ask you to find and focus a flake by hand ("N flakes not found", "Autofocus
  failed"): the scan goes on and asks no more of these questions in the run.
- **Those windows fit the screen.** The live view is made smaller when the window would be taller than the screen, and
  on a narrow screen the "where the flake should be" picture too; the buttons are always visible.

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
