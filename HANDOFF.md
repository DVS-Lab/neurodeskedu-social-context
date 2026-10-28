# Tutorial handoff for Jacob and Riccardo

The tutorial works with the published educational dataset, [Zenodo v1.0.0](https://doi.org/10.5281/zenodo.23718599): 67 public participants and 804 signed outcome COPEs. `Cross_task_decoding.ipynb` defaults to public mode and includes executed outputs. This remains separate from the neural-signature paper and is not yet submitted to NeurodeskEDU.

## Run and review

1. Clone/update this repository. On a laptop, use Python 3.10–3.13 and run `bash run_tutorial.sh`. In an existing Neurodesk Play JupyterLab, run `bash run_tutorial.sh --setup-play` in a terminal, open the original notebook in the repository root, and choose **Social context (pinned)**. Select **Kernel → Restart Kernel and Run All Cells**. Both paths use an isolated `.venv`; the Play option registers its kernel without starting another server.
2. Read the notebook as a learner: does it clearly explain the source COPEs, human/computer construction, participant-level folds, transfer target, paired ordering metric, confidence intervals, paired permutation null and limitations of coefficient/forward maps?
3. Independently rerun it on **Neurodesk Play** as a learner. The target environment has now passed: a fresh project environment and fresh kernels on Neurodesktop 2026-10-07/Python 3.13.15 downloaded the release, checked all maps, ran all folds and 999 permutations, and rendered the figures. The measured enhanced cached run took about 28 seconds including kernel startup, with about 7 seconds for permutations. Peak memory was not separately measured. The batch check is `.venv/bin/python tools/execute_tutorial.py --kernel social-context`; its executed copy in `work/` is for inspection, while the original root notebook is the one to rerun.
4. Finalize actual contributors' full names, contributions and tutorial authorship. Dataset creators and tutorial authors need not be identical; do not add people merely for anticipated work. Keep the existing AI-assistance disclosure.
5. Agree with NeurodeskEDU maintainers on the small `data_release.json` sidecar. Check the contribution guide, README, template and submission terms before preparing a PR. No submission or message to colleagues has been sent.

## Completed verification

- A fresh kernel downloaded the actual published Zenodo ZIP from an empty cache, verified its SHA256, extracted the exact archive, retrieved the checksum-pinned external reference, reconstructed the reviewed mask, and ran the complete computation.
- An isolated virtual environment installed only `requirements.txt`; `pip check`, the JupyterLab entry point, full notebook execution and watermark succeeded.
- All 804 map checksums, finite values and common geometry passed; the independent mask has 84,479 voxels. The classifier ran all five folds without convergence warnings.
- Twenty-four focused checks cover membership/export boundaries, exact release contents, preserved map bytes, template reconstruction, download/audit failure behavior, full-voxel versus complete training-span fits, coherent training/test label swaps and serial/parallel equivalence. See `VALIDATION.json`, `NEURODESK_PLAY_VALIDATION.json` and `PUBLISHED_RECORD_REVIEW.json`.
- The source map/manifest bytes and fixed predictions are unchanged from the reviewed prepublication candidate. No parameters or masks were selected using accuracy.

## Scientific boundary

The source snapshot is OpenNeuro ds005123 v1.0.0, originally N=114. The export required existing QC and complete maps and excluded the parent's full 62-person protected pool before source access. The tutorial consumes only public derivatives and never reads private membership lists, paper caches, fitted paper signatures or reserved validation images. The Mac consumer test does not recreate the private Linux2 membership audit; its evidence and immutable map-byte fingerprints are documented in `data_release.json`.

The tutorial averages positive/negative outcomes within partner and averages friend/stranger equally into the human class. It trains Shared Reward human/computer patterns and evaluates both Shared Reward and Trust on the same held-out participants. The paired ordering score is not ordinary threshold-based single-map accuracy. Bootstrap intervals describe fixed out-of-fold predictions and omit uncertainty from model refitting. Separately, 999 participant-blocked permutations apply the same human/computer swap across tasks, refit every fold and report raw and two-test maximum-statistic p-values. The complete training-only orthonormal span accelerates linear SVM refits without variance-based feature selection; the notebook checks agreement with full-voxel fits before randomization. Transfer does not establish an abstract or uniquely social representation.

Do not use tutorial results to revise the paper's frozen candidates, access reserved subjects, or claim independent final validation. No UGR or betrayal analysis is part of this tutorial.

## Dataset and licensing

The final ZIP contains exactly 804 COPEs and four original supporting files, under CC0 1.0. It contains no third-party template image or mask. The notebook retrieves original TemplateFlow mask and anatomical references separately under upstream terms, verifies their SHA256 values and checks the exact reconstructed binary-mask hash. Rendered anatomical underlays retain upstream terms. No FSL module is required: the example uses precomputed maps and pinned Python packages, while recording `ml list`, the base image and package versions. Code is MIT; original tutorial narrative is CC BY 4.0.

Curator-only export/finalization instructions are in `EXPORT_PUBLIC.md`; learners should not run those tools. Keep all images, private curation records, caches and virtual environments out of Git.

## Deferred metadata item

At the user's request, the Zenodo related-source DOI correction can wait. Its `isDerivedFrom` entry currently points to ds005123 v1.1.3; the archive, description, notebook and fixed source contract use v1.0.0. This is a metadata edit only, not another archive upload. Keep the analysis source pinned to v1.0.0.
