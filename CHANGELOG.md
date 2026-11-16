# Changelog

Notable changes to FlakeIdentifier. The scan program's version is shown in its window and logs (`py-YYYY-MM-DD<letter>`).

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
