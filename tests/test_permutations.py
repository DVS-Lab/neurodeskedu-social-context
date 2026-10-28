"""Execute the actual tutorial loops on small data and compare with full-voxel refits."""
from pathlib import Path
import json
import numpy as np
from sklearn.model_selection import KFold
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]


def cell_body(marker):
    notebook = json.loads((ROOT / 'Cross_task_decoding.ipynb').read_text())
    source = next(''.join(c['source']) for c in notebook['cells']
                  if c['cell_type'] == 'code' and marker in ''.join(c['source']))
    assert source.startswith('%%script fslpython')
    return source.split('\n', 1)[1]


def run_small_example(tmp_path, monkeypatch, rank_deficient=False):
    monkeypatch.chdir(tmp_path)
    out = Path('outputs/public'); out.mkdir(parents=True)
    rng = np.random.default_rng(74)
    x = rng.normal(size=(14, 2, 2, 25))
    if rank_deficient:
        x = x[..., :7] @ rng.normal(size=(7, 25))
    np.save(out / 'features.npy', x.astype('float32'))
    (out / 'settings.json').write_text(json.dumps(dict(seed=20261027, folds=3, C=1., permutations=8)))
    exec(cell_body('weights = []'), {})
    exec(cell_body('reference_margins ='), {})
    exec(cell_body('all_swaps ='), {})
    return out, x.astype('float32')


def test_complete_training_coordinates_match_full_voxel_fits_with_rank_deficiency(tmp_path, monkeypatch):
    out, x = run_small_example(tmp_path, monkeypatch, rank_deficient=True)
    compact = np.load(out / 'permutation_inputs.npz')
    np.testing.assert_allclose(compact['check_margins'], compact['reference_margins'], atol=2e-3, rtol=2e-3)
    np.testing.assert_equal(compact['check_margins'] > 0, compact['reference_margins'] > 0)
    observed = np.load(out / 'observed_results.npz')
    for fold, (train, test) in enumerate(KFold(3, shuffle=True, random_state=20261027).split(x), start=1):
        assert not set(train) & set(test)
        np.testing.assert_equal(np.flatnonzero(observed['fold'] == fold), test)


def test_every_randomization_refits_training_and_scores_swapped_test_labels(tmp_path, monkeypatch):
    out, x = run_small_example(tmp_path, monkeypatch)
    swaps = np.random.default_rng(20261029).choice([-1, 1], size=(8, len(x)))
    full_null = []
    for flip in swaps:
        correct = np.zeros(2)
        for train, test in KFold(3, shuffle=True, random_state=20261027).split(x):
            labels = (np.tile([1, -1], (len(train), 1)) * flip[train, None]).ravel()
            model = LinearSVC(C=1., dual=True, tol=1e-4, max_iter=100000, random_state=20261027)
            model.fit(x[train, 0].reshape(-1, 25), labels)
            for task in range(2):
                scores = model.decision_function(x[test, task].reshape(-1, 25)).reshape(-1, 2)
                correct[task] += ((scores[:, 0] - scores[:, 1]) * flip[test] > 0).sum()
        full_null.append(correct / len(x))
    np.testing.assert_equal(np.load(out / 'permutation_null.npz')['accuracies'], full_null)
