# NeurodeskEDU: Cross-task decoding

A separate educational draft for David, Jacob and Riccardo. It starts from precomputed outcome COPEs and teaches participant-separated Shared Reward → Trust classification. This folder is independent of `rf1-sra-neural-signature`; the paper's analysis and validation samples are not modified.

**Status:** notebook draft with a labelled synthetic fixture. A final public-data archive (67 participants, 804 outcome maps, four supporting files) has been prepared under CC0. It excludes third-party template assets; the updated notebook fetches the original reference separately and verifies reconstruction of the same mask. The final archive and downstream computation passed local tests; the Zenodo downloader and Neurodesk Play execution are not yet tested. See `PUBLIC_CANDIDATE_REVIEW.json`. The committed notebook still defaults to synthetic mode.

## Start here

Open [Cross_task_decoding.ipynb](Cross_task_decoding.ipynb) from this directory and run all cells. Its default `MODE = "synthetic"` generates simulated maps under ignored `data/`, fits a small educational classifier, and saves labelled figures under ignored `outputs/`. The saved notebook outputs are synthetic examples, not study results. See `VALIDATION.json` for the local execution status when available.

The final public mode requires a published archive and completed `data_release.json`. It stops while those entries are incomplete. There is no silent switch from failed real-data loading to simulated data. The notebook contains its own download, validation and analysis code; it does not import the paper's code or models. `requirements.txt` records a proposed environment; Neurodesk Play testing remains pending. The offline draft prints software versions when watermark is unavailable; watermark should be installed and checked before submission.

## Recommended repository and data host

Use **[DVS-Lab/neurodeskedu-social-context](https://github.com/DVS-Lab/neurodeskedu-social-context)**, for the notebook, small metadata/configuration files, documentation and tests. Keep the NIfTI maps and private curation records out of Git. When ready, contribute the reviewed notebook to NeurodeskEDU's functional-imaging examples; agree on placement of the small release-configuration sidecar with the maintainers.

Use **Zenodo for the versioned derivative-data release and DOI**. Its default quota is 50 GB per record; the stated 100-file limit means our >1,000 NIfTIs should go inside one ZIP, not become separate record attachments. Pin the release-specific URL/DOI and archive SHA256 in the notebook configuration. A DOI establishes a citation target; the exact archive checksum establishes the bytes consumed.

I would not start a new OSF Project for this work. The OSF transition guide, checked **October 27, 2026**, says new Projects/Components stop on **November 16, 2026**, and existing Projects become read-only on **February 19, 2027**. Public materials retain their URLs and remain downloadable. That makes Zenodo a better fit for a new release expected to receive revisions.

Sources:

- [Zenodo default storage quota](https://help.zenodo.org/docs/deposit/manage-quota/)
- [Zenodo file-count and size limits](https://support.zenodo.org/help/en-gb/1-upload-deposit/80-what-are-the-size-limitations-of-zenodo)
- [Zenodo version-specific DOIs](https://zenodo.org/help/versioning)
- [OSF Projects transition](https://help.osf.io/article/759-details-of-osf-projects-transition)

## How much data?

These are **uncompressed float32 NIfTI-1 map estimates**, not measured public-participant exports. The current analysis grid is 57 × 70 × 54 voxels, approximately 2.7 × 2.7 × 2.97 mm. Only a previously produced group-map header was inspected to establish this geometry; no participant image was opened for this estimate. Each full-grid map occupies about 0.862 MB including its basic header.

| Proposed content | Maps/person | Maps at N=114 | Map bytes, decimal GB |
|---|---:|---:|---:|
| Compact, valence-averaged human/computer maps for two tasks | 4 | 456 | 0.39 |
| **Recommended: two tasks × three partners × two valences** | **12** | **1,368** | **1.18** |
| Recommended set plus corresponding z-statistics | 24 | 2,736 | 2.36 |
| Twelve COPE conditions separately for two runs | 24 | 2,736 | 2.36 |
| Twelve conditions on a standard 91 × 109 × 91, 2 mm grid | 12 | 1,368 | 4.94 |

The chosen core uses participant-level signed COPEs after the verified retained-run combination. It does not require zstats, varcopes, residual time series, raw BOLD, anatomical scans, or entire `.feat` trees. Gzip/ZIP size depends on the actual maps. Add the small mask, manifest and methods metadata to obtain the final archive size. Missing maps, QC exclusions and protected participants reduce the usable N, so 114 is an upper-bound inventory count, not the promised tutorial N.

The estimate scales linearly: **about 10.35 MB per person for the 12-map core before compression**. At either grid, the core is comfortably under Zenodo's default 50 GB quota. These figures describe storage, not peak RAM or actual-public-data runtime.

Run the metadata-only estimator:

```bash
python tools/estimate_release_size.py
python tools/estimate_release_size.py --n 90
python tools/estimate_release_size.py --shape 91 109 91
```

After curation, `--manifest work/approved_manifest.csv` sums its recorded compressed `byte_size` column without opening the images. Do not guess a compression ratio or treat the synthetic fixture's compressibility as human-data measurements.

## Public derivative bundle

The candidate source is [OpenNeuro ds005123 v1.0.0](https://doi.org/10.18112/openneuro.ds005123.v1.0.0), with CC0 in its source metadata. The raw-release DOI and the new derivative-release DOI are separate citations. Use original, signed, uncentered outcome COPEs for computer/friend/stranger × positive/negative in Shared Reward and Trust. Exact source contrast names/weights and phase provenance must be checked before release; the notebook does not infer labels from numeric COPE indices.

The finalized release archive contains:

- `maps/*.nii.gz`: 12 finite, signed float32 condition maps per eligible person on the same verified grid.
- External reference mask: fetched separately by the notebook from the original TemplateFlow provider, checksum-verified and reconstructed with the predefined rule. No third-party mask or template is redistributed in the final Zenodo ZIP.
- `manifest.csv`: one row per map with the fields demonstrated in the notebook. `byte_size` and `sha256` refer to each distributed compressed file.
- `dataset_description.json`, `README` and `aggregate_image_checks.json`, with original license/provenance metadata. The final ZIP has exactly 804 maps and these four supporting files including the manifest (808 entries).

Do not export paper-derived weights, group patterns, paper coverage masks, or outputs involving nonpublic/reserved people. The educational features and display maps are built within the tutorial's own permitted data boundary.

## Current repository and guarded Linux2 export

The requested GitHub repository is now live. The user confirmed that the complete protected pool is the paper's original 50 plus 12 supplemental holdouts, with no additional external list. These 62 people were selected from the larger study; their overlap with the public 114 must be counted, not assumed. The private locks are not present in the local Mac checkout.

[EXPORT_PUBLIC.md](EXPORT_PUBLIC.md) gives metadata-only overlap, provenance/size planning and staged-archive commands for Linux2. `tools/prepare_public_maps.py` checks the actual pinned public task/run inventory as well as participant membership, so it cannot export additional unpublished runs merely because their participant ID is public. Its consumer bundle includes no protected membership file or source filesystem paths. Curator-controlled mask provenance and later release review remain required.

The notebook explains the reserved-validation boundary without exposing participant identities. Its ordinary cross-validation test folds are temporary partitions inside the permitted development subset; they are not the paper's sealed final evaluation cohort.

## Eligibility check before image export

The final sample is:

`public ds005123 v1.0.0 participants ∩ required outcome maps/QC − union of all protected validation participants`.

A curator must prepare a private metadata file describing the **complete union** of the sealed N=50 and any reserved external-validation participants. This draft has not read or derived that list. Every plan participant must be publicly released, unprotected, QC-eligible and complete for the fixed 12 conditions. Private exclusion identities and reasons must not enter the public manifest.

`tools/check_export_plan.py` checks those metadata conditions before any copying or NIfTI load. It is deliberately not an image exporter and does not certify consent/provenance or inspect image headers/intensities. A passed metadata check is one prerequisite for a later curator-reviewed export, not permission to publish unreviewed data.

```bash
python tools/check_export_plan.py \
  --public-participants work/public_participants.tsv \
  --export-plan work/proposed_export.csv \
  --protected-membership work/protected_union.json
```

The two tables need `participant_id`; the export plan also requires `source_dataset`, `source_version`, `task`, `partner`, `valence`, `phase`, `qc_included`, and `byte_size`. The private JSON must contain `complete: true`, `covers: ["sealed_N50", "external_validation"]`, and `participant_ids: [...]`. Hash and retain the original membership sources in the curator's private audit. The JSON declaration alone does not prove membership correctness.

## Review and submission

See [HANDOFF.md](HANDOFF.md). The draft follows the [official template](https://github.com/neurodesk/neurodeskedu/blob/main/books/examples/template.ipynb) and [contribution guidance](https://neurodesk.org/edu/contribute/examples/): short title, author/date/license, AI disclosure, citations, commented steps and environment reporting. Read the [repository README](https://github.com/neurodesk/neurodeskedu/blob/main/README.md) and [submission terms](https://github.com/neurodesk/neurodeskedu/blob/main/TERMS_OF_SUBMISSION.md).

Before submission, replace the synthetic default with the reviewed public release, verify watermark/dependencies, finalize authors/licenses/citations and test a fresh download plus restart/run-all in Neurodesk Play. Automated execution and merge publish the notebook; peer review follows. No submission or message to colleagues has been sent.
