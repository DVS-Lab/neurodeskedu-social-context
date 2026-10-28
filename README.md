# Cross-task social-context decoding

A NeurodeskEDU teaching draft using **67 public participants and 804 precomputed outcome COPEs** from Shared Reward and Trust. Train a human/computer classifier in Shared Reward, then evaluate both tasks in the same excluded participants.

[View the notebook](Cross_task_decoding.ipynb) · [Download the notebook](https://raw.githubusercontent.com/DVS-Lab/neurodeskedu-social-context/main/Cross_task_decoding.ipynb) · [Zenodo maps](https://doi.org/10.5281/zenodo.23718599)

## Run in Neurodesk Play

1. Download `Cross_task_decoding.ipynb` and open it in [Neurodesk Play](https://play.neurodesk.org/). You can use JupyterLab's **File → Open from URL** with the download link above, or upload the downloaded notebook.
2. Use Play's default **Python [conda env:base]** kernel.
3. Choose **Kernel → Restart Kernel and Run All Cells**, or work through the cells with **Shift+Enter**.

**No installation, environment creation, setup script, custom kernel or configuration sidecar is required.** The first cell loads the explicit module:

```python
import module
await module.load("fsl/6.0.7.22")
await module.list()
```

The module supplies `fslpython`, including scikit-learn. Cells marked `%%script fslpython` run their visible code in that environment. Other cells use Play's preinstalled data-handling and plotting libraries. Numeric result files in `outputs/public/` connect the steps. Both Python environments and the Neurodesktop image are recorded at the end.

The first run downloads about **310 MB**, plus 1.5 MB of independent template references. Allow roughly **1.5 GB of free disk space**. Downloads are verified and cached in `data/`; result tables and five figures go to `outputs/public/`. Retrieving an uncached Neurodesk module can add time.

The notebook is self-contained and uses explicit loops with **no user-defined functions**. No preprocessing or first-level model fitting is required. Curator export tools and private audit inputs are separate from the learner workflow.

The installation-free path passed on **Neurodesktop 2026-10-07** using the default Play kernel and FSL module. A fresh-data run took about **2½ minutes**; a cached UI Run All took **43 seconds**, including **14 seconds** for 999 permutations. All 19 code cells completed. See the [validation record](NEURODESK_PLAY_VALIDATION.json).

## What predicts what?

| Evaluation | Train on | Predict in excluded participants |
| --- | --- | --- |
| Within-task control | Shared Reward human/computer maps | Shared Reward human/computer maps |
| Cross-task transfer | Shared Reward human/computer maps | Trust human/computer maps |

First average the two outcome valences within each partner, then average friend and stranger equally into **human**; computer supplies the other class. Each map is spatially centered within a fixed independent mask. The linear SVM settings and five participant folds stay fixed.

The score is **paired ordering accuracy**: does a participant's human map score above their computer map? Participant bootstrap intervals describe fixed out-of-fold predictions and omit training-refit uncertainty. Separately, **999 participant-blocked permutations** swap each person's labels coherently across tasks, refit every fold, and report raw and two-test maximum-statistic familywise p-values. Complete training coordinates speed up the repeated fits; agreement with the original full-voxel classifier is checked first. The permutation calculation uses straightforward serial loops.

Five figures show condition construction/folds, accuracy intervals, participant margins, permutation distributions, and predefined axial views of coefficients and forward patterns. Color clipping affects display only. These maps do not establish causal regional importance or an abstract, uniquely social representation.

## Data boundary and licenses

- Source: [OpenNeuro ds005123 v1.0.0](https://doi.org/10.18112/openneuro.ds005123.v1.0.0), originally N=114. Educational derivatives: [Zenodo v1.0.0](https://doi.org/10.5281/zenodo.23718599), N=67 after existing QC, completeness checks and protected-pool exclusion.
- All 62 people in the parent paper's protected pool were excluded before export. Detailed membership stays outside this repository. The tutorial uses only the immutable public map release and does not read paper caches, frozen signatures or reserved images.
- Temporary tutorial folds are not the paper's sealed final validation cohort. Tutorial results must not guide changes to the paper's frozen candidates.
- Maps and original archive metadata: **CC0 1.0**. Code: **MIT**. Original explanations: **CC BY 4.0**. External TemplateFlow mask/anatomy and anatomical underlays retain upstream terms; those references are not in the Zenodo ZIP.
- The exact archive has **804 COPEs plus four supporting files**. Its version-specific URL and SHA256 are written directly in the notebook. Curator metadata is retained in `data_release.json`; learners do not need that file.

## Review and validation

See [HANDOFF.md](HANDOFF.md), [VALIDATION.json](VALIDATION.json) and [NEURODESK_PLAY_VALIDATION.json](NEURODESK_PLAY_VALIDATION.json). Human scientific and teaching review remains before NeurodeskEDU submission. AI assistance is disclosed in the notebook. No colleague has been messaged automatically.

The draft follows the [contribution guide](https://neurodesk.org/edu/contribute/examples/), [README](https://github.com/neurodesk/neurodeskedu/blob/main/README.md), and [template](https://github.com/neurodesk/neurodeskedu/blob/main/books/examples/template.ipynb). [EXPORT_PUBLIC.md](EXPORT_PUBLIC.md) is for curators, not learners.
