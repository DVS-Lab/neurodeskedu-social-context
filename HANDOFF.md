# Tutorial review for Jacob and Riccardo

This teaching example uses [Zenodo v1.0.0](https://doi.org/10.5281/zenodo.23718599): 67 public participants and 804 signed outcome COPEs. It remains separate from the neural-signature paper and is not yet submitted to NeurodeskEDU.

## Run as a learner

1. Open `Cross_task_decoding.ipynb` in Neurodesk Play using the default **Python [conda env:base]** kernel. The notebook can be downloaded alone; no configuration file is required beside it.
2. Select **Kernel → Restart Kernel and Run All Cells**, or step through with **Shift+Enter**. The first cell loads `fsl/6.0.7.22`. There is no package installation, virtual environment or custom kernel registration.
3. Cells headed `%%script fslpython` run their visible Python inside the module, which provides scikit-learn. Other cells use Play's preinstalled data/plotting libraries. Result files in `outputs/public/` carry data between these steps. The notebook records both environments.
4. Check the download and checksums, all five figures, the accuracy table, permutation diagnostics, module listing and watermark. First-run downloads total about 312 MB; module retrieval can add time. Numerical features occupy about 91 MB, with additional memory for fitting.

The notebook contains **no user-defined functions**. Analysis steps use explicit loops, descriptive variable names and short cells. The complete-training-coordinate step for faster permutations is marked as an optional deeper mathematical topic; it verifies agreement with the full-voxel fit before randomization.

## Teaching and scientific review

- Is it clear which condition maps are averaged, what predicts what, and why each person's maps stay in one fold across tasks?
- Does the explanation distinguish paired ordering from single-map threshold accuracy, bootstrap intervals from permutations, and coefficients from forward patterns?
- Is the `%%script fslpython` convention and its input/output file flow clear to a novice?
- Independently reproduce the notebook, review the interpretations, finalize actual contributor names/roles and keep the AI-assistance disclosure.
- Before submission, check the current NeurodeskEDU contribution guide and template. No PR or message to colleagues has been sent.

## Verification records

`VALIDATION.json` and `NEURODESK_PLAY_VALIDATION.json` document the current target-environment test: all **19 code cells** completed in a fresh default kernel and through the UI **Restart and Run All** action, with no installs or custom kernel. The standalone fresh-download run took about **2½ minutes**; cached UI execution took **43 seconds**, including **14 seconds** for 999 permutations. **23 focused checks** pass, including actual inline refits, rank-deficient coordinate checks and label-swap evaluation. The committed notebook contains the actual Play outputs, with source matching the tested revision. The earlier isolated-environment run is historical: it does not establish the new installation-free path. Guarded export and byte-preserving release checks remain in the curator tests and `PUBLISHED_RECORD_REVIEW.json`.

For a maintainer's fresh-kernel batch check *inside Play*, the preinstalled Python can run `python tools/execute_tutorial.py`. Learners can simply run the notebook. Batch copies saved in `work/` are for inspection; rerun the notebook from its own directory so its relative paths remain consistent.

## Data boundary and licensing

The source snapshot is OpenNeuro ds005123 v1.0.0, originally N=114. Existing QC, complete maps and the full 62-person protected-pool exclusion were applied before export. The tutorial never needs private membership lists, paper caches, frozen models or reserved images. Its cross-validation folds stay inside the 67-person public teaching subset. Do not use tutorial results to alter the paper's frozen candidates or claim final independent validation. No UGR or betrayal analysis is included.

The ZIP contains exactly 804 COPEs and four supporting files under CC0. External TemplateFlow mask/anatomy are retrieved separately, checksum-verified and covered by upstream terms, including anatomical underlays in plots. Code is MIT; original explanations are CC BY 4.0. Keep images, caches and private curator inputs out of Git.

The deferred Zenodo related-source DOI correction remains a metadata-only item: its relation points to v1.1.3 while the actual release and notebook are pinned to v1.0.0. It does not require another archive upload.
