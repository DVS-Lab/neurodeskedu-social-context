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

The recommended command prepares the fixed TemplateFlow MNI152NLin6Asym res-02 brain mask from the configured TemplateFlow directory (normally `/ZPOOL/data/tools/templateflow`). It explicitly resamples that binary mask into the common source grid using nearest-neighbor interpolation. Only an eligible map's header supplies the grid; participant intensities, coverage thresholds and classifier results do not enter mask construction. It never uses the paper's group coverage mask. Missing template files stop the export; it does not download into or modify the TemplateFlow directory.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/prepare_public_maps.py \
  --paper-root /ZPOOL/data/projects/rf1-sra-neural-signature \
  --no-additional-external-validation --stage archive \
  --prepare-template-mask
```

Alternatively, supply a previously reviewed binary independent template/anatomical mask already resampled into the source grid, plus a JSON with `kind: "independent_template"`, `description`, `source_url`, and `sha256` of that mask:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/prepare_public_maps.py \
  --paper-root /ZPOOL/data/projects/rf1-sra-neural-signature \
  --no-additional-external-validation --stage archive \
  --mask work/independent_mask.nii.gz \
  --mask-provenance work/independent_mask.json
```

This rechecks membership, provenance and source hashes, then stages maps with sanitized NIfTI headers and finite signed float32 effects. No centering, thresholding or sign inversion is applied. It writes the public manifest, source/contrast metadata, aggregate checks and a single ZIP suitable for Zenodo's file-count limit. Already-compressed `.nii.gz` files are stored without a second compression pass. An existing bundle is not overwritten silently.

`archive_summary.json` records actual N, map count, compressed-map bytes, ZIP bytes and SHA256. Its status is **staged for review**, not published. Mask coverage, licensing/attribution and notebook public-mode execution still need final review. No DOI is minted and nothing is uploaded by this script.

## Exact public archive contents

Each eligible participant contributes exactly these twelve signed, uncentered outcome COPEs:

| Task | COPEs | Condition names |
| --- | --- | --- |
| Shared Reward | 1–6 | C_pun, C_rew, F_pun, F_rew, S_pun, S_rew |
| Trust | 4–9 | C_def, C_rec, F_def, F_rec, S_def, S_rec |

The notebook uses every condition to construct its valence-averaged human/computer inputs. Human is the equal average of friend and stranger. Full-trial Shared Reward maps, decision/neutral maps, UGR, Social Doors, z statistics, variance maps, individual-run duplicates, fitted paper models and protected participants are not included.

There are five supporting files: the independent `mask.nii.gz`, `manifest.csv`, `dataset_description.json`, `aggregate_image_checks.json` and `README`. The exporter checks this exact allowlist before creating the ZIP. Total ZIP entries must equal **12 × eligible N + 5**. Maps retain source values and their original grid; only headers are sanitized. Template-mask terms remain separate from the source dataset's CC0 terms and need review before publication.

## 5. Finalize the upload without redistributing the third-party template

The archive produced above is a staging artifact, not the final upload. The exact template's upstream metadata refers to a missing LICENSE file. We do not assume another template's terms or relicense it. The finalizer removes the template mask from the hosted bundle. The notebook obtains the original reference separately from TemplateFlow, verifies its SHA256, resamples it with the predefined rule, and checks the reconstructed binary mask's voxel hash against the reviewed mask. This changes no analysis voxels or participant map bytes.

For the reviewed 67-person candidate:

```bash
python3 tools/finalize_public_release.py \
  --input work/zenodo-v1/public_outcome_copes.zip \
  --output work/zenodo-final/public_outcome_copes_v1.0.0.zip \
  --sha256 3633a9d93f7b30a520b0056adaae352927bf7d4a6135aedefa4d1db2e84734e0
```

This requires the reviewed input checksum, preserves the original ZIP, checks every COPE hash, preserves all COPE and manifest bytes, replaces the staging README/license metadata, and emits a summary beside the final ZIP. A different input checksum requires review; do not substitute one merely to bypass the check.

The **final upload** contains exactly **804 COPEs and four supporting files (808 ZIP entries)**: README, manifest.csv, dataset_description.json and aggregate_image_checks.json. No third-party template image or mask is included. Distributed maps and original metadata are dedicated under **CC0 1.0 Universal**. The repository's code remains MIT and its educational narrative CC BY 4.0; those licenses do not relicense upstream template assets.

**Only upload `work/zenodo-final/public_outcome_copes_v1.0.0.zip`.** Never upload the whole work directory: it also contains private membership locks and source paths. In the Zenodo draft replace the old staging ZIP, change the license from CC BY 4.0 to CC0 1.0 Universal, retain version 1.0.0, and explain that the reference mask is retrieved separately by the accompanying notebook under its upstream terms.

In Zenodo, create a new dataset upload, add that ZIP, describe its relationship to OpenNeuro ds005123 v1.0.0, and save a draft. A DOI can be reserved while it is a draft; it is registered on publication. The notebook's DOI, download URL, checksum, N and audit flags must be filled from the reviewed release before enabling public-data mode. See [Zenodo's upload instructions](https://help.zenodo.org/docs/deposit/create-new-upload/).

## What to say in the notebook

Explain that public data availability and eligibility for model development are separate. The notebook uses a permitted public development subset; a prespecified validation cohort was excluded before loading images and remains outside training, tuning, interpretation and tutorial exercises. Its identities and private exclusion reasons are not part of the teaching bundle.

Distinguish the tutorial's temporary participant-level cross-validation folds from the paper's reserved validation cohort. Report the final tutorial N, source snapshot, selection/QC rules and cross-validation method. Disclosing that a cohort is reserved does not score it or leak its outcomes; the key protection is preventing those images/results from influencing development. Do not describe cross-validation performance as independent final validation.
