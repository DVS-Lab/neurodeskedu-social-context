# Prepare the Zenodo maps on Linux2

The user confirmed on October 27, 2026: exclude the paper's full **62-person protected pool** (the original 50 plus 12 supplemental holdouts); there is no additional external-validation list. All original holdouts remain excluded even if they later failed QC. The exact overlap with the public 114 requires the private IDs; it cannot be calculated from the published aggregate count or hashes.

The local Mac checkout has no private membership locks and therefore stops before source-image access. Run the following stages on Linux2, where the locks and FEAT outputs already exist. The tools do not reconstruct membership, score models, or write into the paper/source repositories.

## 1. Clone the teaching repository

```bash
cd /ZPOOL/data/projects
git clone https://github.com/DVS-Lab/neurodeskedu-social-context.git
cd neurodeskedu-social-context
```

If it is already cloned, use its existing checkout and `git pull --ff-only`.

## 2. Count the overlap using membership metadata only

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/prepare_public_maps.py \
  --paper-root /ZPOOL/data/projects/rf1-sra-neural-signature \
  --no-additional-external-validation --stage overlap
```

This validates the hashes of the original and revised paper membership locks and the pinned public participants file. It prints the total overlap with N=114, its original/supplemental components, and the public unprotected count. **It does not load even image headers.** No participant IDs are printed. The result is also saved in ignored `work/zenodo-v1/overlap_summary.json`.

Do not subtract 62 from 114: the protected pool was drawn from the larger study, so the intersection must be counted. The unprotected public count is not yet the usable imaging N; QC and complete source-map checks follow.

## 3. Inventory the permitted maps and actual compressed bytes

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/prepare_public_maps.py \
  --paper-root /ZPOOL/data/projects/rf1-sra-neural-signature \
  --no-additional-external-validation --stage plan
```

Only unprotected public participant IDs reach the source adapters. The plan checks:

- The exact ds005123 v1.0.0 participants and public task/run inventory. The source release is sessionless; the matching canonical baseline is ses-01. Only runs present in that public snapshot can contribute to exported maps.
- The complete protected union, including all original and supplemental assignments, against their tracked hash records. No redraw or inference from a seed is allowed.
- Existing tSNR/coverage/FD QC flags, without recomputing outlier thresholds.
- Audited phase-resolved Shared Reward outcomes, honoring its verified one-/two-run strategy; completed two-run Trust outcomes and their fitted contrast weights/design provenance.
- Twelve maps/person, their exact contrast names, original signed source-file checksums and headers, and matching grids. No group map or frozen paper model is used.

The private plan, source paths, exclusion reasons and protected identities stay under ignored `work/zenodo-v1/`. `plan_summary.json` prints aggregate Ns, reasons and compressed-byte totals. Missing required private locks or unexpected provenance changes stop execution; do not bypass these guards. No source voxel arrays are materialized during planning, though eligible map bytes are read for SHA256 checks.

To share results back without disclosing identities, copy only the aggregate JSON summaries into a separately reviewed public status file. **Do not force-add work/, private_export_plan.csv, private_exclusions.csv or protected_union.json.**

## 4. Stage the archive after reviewing the plan and independent mask

Supply a binary independent template/anatomical mask already resampled into the source grid, plus a JSON with `kind: "independent_template"`, `description`, `source_url`, and `sha256` of that mask. Do not use the paper's learned/group coverage mask. The exporter does not choose masks from accuracy or silently resample one.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/prepare_public_maps.py \
  --paper-root /ZPOOL/data/projects/rf1-sra-neural-signature \
  --no-additional-external-validation --stage archive \
  --mask work/independent_mask.nii.gz \
  --mask-provenance work/independent_mask.json
```

This rechecks membership, provenance and source hashes, then stages maps with sanitized NIfTI headers and finite signed float32 effects. No centering, thresholding or sign inversion is applied. It writes the public manifest, source/contrast metadata, aggregate checks and a single ZIP suitable for Zenodo's file-count limit. Already-compressed `.nii.gz` files are stored without a second compression pass. An existing bundle is not overwritten silently.

`archive_summary.json` records actual N, map count, compressed-map bytes, ZIP bytes and SHA256. Its status is **staged for review**, not published. Mask coverage, licensing/attribution and notebook public-mode execution still need final review. No DOI is minted and nothing is uploaded by this script.

## What to say in the notebook

Explain that public data availability and eligibility for model development are separate. The notebook uses a permitted public development subset; a prespecified validation cohort was excluded before loading images and remains outside training, tuning, interpretation and tutorial exercises. Its identities and private exclusion reasons are not part of the teaching bundle.

Distinguish the tutorial's temporary participant-level cross-validation folds from the paper's reserved validation cohort. Report the final tutorial N, source snapshot, selection/QC rules and cross-validation method. Disclosing that a cohort is reserved does not score it or leak its outcomes; the key protection is preventing those images/results from influencing development. Do not describe cross-validation performance as independent final validation.
