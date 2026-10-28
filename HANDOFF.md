# Handoff for Jacob and Riccardo

This is an educational draft, separate from the paper. The notebook currently runs labelled synthetic maps. Its methods narrative is ready for review, but it is not a public-data demonstration or a NeurodeskEDU submission yet.

## Scientific/data review

- Confirm the public source snapshot: ds005123 v1.0.0, originally N=114. Determine the actual eligible overlap of Shared Reward and Trust after existing QC and map completeness checks; do not promise N=114.
- Obtain the authoritative curator-prepared union of sealed N=50 and external-validation membership using metadata only. Exclude those people before any map export. Keep membership/exclusion records private under ignored work/ or an approved private curation location.
- Check the exact source outcome COPE definitions, signs, names/weights, phase evidence and retained-run strategy. The educational prediction is human (equal friend/stranger mean) versus computer, averaging positive/negative outcomes. This differs from the paper's full cross-valence matrix.
- Use only participant-specific public-source derivatives. Establish an independent fixed template/anatomical mask; do not copy paper masks, trained weights or group patterns involving additional people.
- Prepare a metadata export plan, record actual compressed file sizes, run the plan checker, and review provenance, finite values and geometry in the later approved export. The draft tools do not perform that image export.
- Finalize licenses, the original dataset/data-paper citation, derivative DOI, authors' full names/contributions and AI-assistance statement.

## Technical/teaching review

- Read the notebook without running it: are the COPE/label distinction, paired ordering metric, participant folds and cross-task interpretation clear?
- Run the synthetic draft from a fresh kernel, including a second Run All to check repeatability. Its accuracies are simulated and cannot guide paper choices.
- After curation, bundle the maps/metadata into one ZIP (or a few documented archives); >1,000 loose map attachments exceed Zenodo's stated file-count limit. Check total byte size and checksum. Do not upload raw BOLD or whole FEAT trees.
- Create a reviewed versioned Zenodo record; populate the release DOI/URL/SHA256, actual N and audit fields in data_release.json. This draft does not create a remote deposit or mint a DOI.
- Test real public mode in a clean Neurodesk Play session: dependency installation, download/retry failure, checksums, memory/runtime, plots and watermark. Confirm the notebook does not require paths into this local folder's parent or the paper repository.
- Agree with maintainers on including the small release-configuration JSON with the otherwise self-contained notebook. Remove template instructions, retain needed citations/disclosures, and check static rendering.
- Test a checksum mismatch and incomplete archive: execution should stop, never silently use synthetic data. Finalize the expected validation cells and deterministic tolerances without selecting parameters for higher accuracy.
- After internal testing/review, submit a NeurodeskEDU PR with dependencies, expected outputs and contributor information. Publication follows automated checks and merge, while peer review follows publication.

## What is already provided

- A 22-cell draft with 12-map data layout, participant-separated five-fold evaluation, within-SR control, SR→Trust transfer, paired participant bootstrap and coefficient/forward-pattern displays.
- A synthetic fixture for code-flow testing only; real data use requires a completed release configuration.
- Storage arithmetic, optional summation of recorded file sizes, and a metadata-only pre-export membership/completeness checker.
- Proposed dependency pins, licences and a separate local development folder.

Do not use educational results to revise the paper's frozen candidates or score protected validation subjects. This handoff has not been sent to anyone automatically.
