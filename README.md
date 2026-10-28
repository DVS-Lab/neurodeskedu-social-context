# Cross-task social-context decoding

A working NeurodeskEDU tutorial draft using **67 public participants and 804 precomputed outcome COPEs** from Shared Reward and Trust. The notebook downloads a fixed Zenodo release, checks every map, constructs human/computer patterns, and evaluates participant-separated cross-task prediction. No fMRI preprocessing, first-level model fitting, private data or FSL installation is required.

[Open the notebook](Cross_task_decoding.ipynb) · [Zenodo dataset](https://doi.org/10.5281/zenodo.23718599) · [Validation record](VALIDATION.json)

## Run it

Use Python **3.10–3.13**. The pinned environment passed locally with Python 3.13.5 and on **Neurodesk Play / Neurodesktop 2026-10-07 with Python 3.13.15**. A cached Play run of the enhanced notebook took about 28 seconds including fresh-kernel startup; its 999 permutations took about 7 seconds. See the [Play validation record](NEURODESK_PLAY_VALIDATION.json).

```bash
git clone https://github.com/DVS-Lab/neurodeskedu-social-context.git
cd neurodeskedu-social-context
bash run_tutorial.sh
```

The launcher finds a compatible Python (including standard Anaconda/Miniforge/Miniconda locations), creates a local `.venv`, installs `requirements.txt`, and opens `Cross_task_decoding.ipynb` in JupyterLab. Select **Kernel → Restart Kernel and Run All Cells**. If you already have the checkout, run `git pull --ff-only` there before launching it. `bash run_tutorial.sh --check` checks interpreter selection without installing or starting anything; `TUTORIAL_PYTHON=/path/to/python` overrides selection.

The first run downloads approximately **310 MB**, plus approximately 1.5 MB of external template references, and caches the files. Allow about **1.5 GB free disk space**. The feature array uses about 91 MB, with additional memory for model fitting. Download time depends on the connection; repeat runs use the checksum-verified cache.

In **Neurodesk Play**, use its existing JupyterLab rather than starting a second server:

```bash
bash run_tutorial.sh --setup-play
```

This installs an isolated environment and registers **Social context (pinned)**. Open `Cross_task_decoding.ipynb`, choose that kernel and use **Restart Kernel and Run All Cells**. Keep `data_release.json` beside the notebook. `ml` loads application containers; this Python-only example does not execute FSL and therefore needs no FSL module. The notebook runs `ml list` when available and records the base image and exact Python package versions.

For a fresh-kernel batch check in either environment:

```bash
.venv/bin/python tools/execute_tutorial.py
# On Play, add: --kernel social-context
```

Outputs and downloaded files stay local and are ignored by Git. The executed copy is saved under `work/`.

**Public mode is the default.** For a simulated code-flow demonstration, explicitly change `MODE` to `"synthetic"` in the first code cell. Download or integrity failures stop execution; they never silently select synthetic data.

## What predicts what?

| Evaluation | Train on | Evaluate on | Unit kept out of training |
| --- | --- | --- | --- |
| Within-task control | Shared Reward human vs computer maps | Shared Reward human vs computer maps | Participant |
| Cross-task transfer | Shared Reward human vs computer maps | Trust human vs computer maps | The same participant across both tasks |

Each source task supplies computer, friend and stranger maps for two outcome valences. The notebook averages positive/negative outcomes within partner, then averages friend and stranger equally to form **human**. The second condition is **computer**. Features are spatially centered within a fixed independent mask. A fixed linear SVM is fitted in five participant folds; no classifier or mask is selected by accuracy.

The reported metric is **paired ordering accuracy**: how often a held-out participant's human map scores above their computer map. This differs from threshold-based accuracy on individual maps. Participant bootstrap intervals summarize the fixed out-of-fold predictions and omit uncertainty from refitting the training models. A separate **999-permutation** analysis coherently swaps human/computer labels within each participant across both tasks and refits every fold. It reports raw and two-test maximum-statistic familywise p-values, exceedances, null means and Monte Carlo uncertainty. A complete training-only orthonormal span speeds up refits without selecting features; agreement with the full-voxel predictions is checked before randomization. Up to four processes are used with one BLAS thread each.

The five figure panels show label construction and fold allocation, performance intervals, participant margins, permutation null distributions, and six predefined axial planes of coefficients and Haufe-style forward patterns over an anatomical reference. Display scales clip at each pattern’s 99th absolute percentile; this affects colors only and is not a significance threshold. They illustrate the tutorial; they do not establish causal regional importance or an abstract, uniquely social representation.

## Data boundary and licenses

- Original public source: [OpenNeuro ds005123 v1.0.0](https://doi.org/10.18112/openneuro.ds005123.v1.0.0), originally N=114.
- Educational derivatives: [Zenodo v1.0.0](https://doi.org/10.5281/zenodo.23718599), N=67 after the protected-pool exclusion, existing QC and complete-input checks.
- All 62 people in the parent paper's protected pool were excluded before export. Detailed membership stays outside this repository. The notebook uses only released maps and does not access reserved images, paper caches or frozen signatures.
- Tutorial folds are temporary cross-validation partitions inside the educational subset. They are not the paper's sealed final validation cohort. Tutorial results must not drive changes to the paper's frozen candidates.
- Distributed maps and original archive metadata: **CC0 1.0**. Code: **MIT**. Original tutorial narrative: **CC BY 4.0**.
- Third-party template assets are not redistributed in the Zenodo ZIP. The notebook retrieves checksum-pinned TemplateFlow mask and anatomical references from their provider, reconstructs the fixed mask, and verifies its exact binary voxel hash. Upstream terms apply to that external resource.

The archive contains exactly **804 COPEs plus four supporting files**. Its SHA256 and version-specific URL are pinned in `data_release.json`. The consumer's integrity checks complement the guarded Linux2 export; they do not independently recreate the private membership audit.

## Review and contribution

See [HANDOFF.md](HANDOFF.md) for remaining human teaching/scientific review, contributor credit and target-environment validation details. This is not yet a NeurodeskEDU submission. Codex assistance is disclosed in the notebook. No colleague has been messaged automatically.

The draft follows the [contribution guide](https://neurodesk.org/edu/contribute/examples/), [repository README](https://github.com/neurodesk/neurodeskedu/blob/main/README.md), and [example template](https://github.com/neurodesk/neurodeskedu/blob/main/books/examples/template.ipynb).

Curator-only provenance/export instructions are in [EXPORT_PUBLIC.md](EXPORT_PUBLIC.md). Learners do not need to run those tools. Private curation records, images, caches and environments are ignored by Git; only the notebook, configuration, code and small documentation belong in this repository.
