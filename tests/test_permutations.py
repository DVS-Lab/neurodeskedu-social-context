"""Scientific checks for paired refitting and the lossless training-span speedup."""
import ast
from pathlib import Path
import json
import warnings
import numpy as np
from sklearn.svm import LinearSVC
from sklearn.model_selection import KFold
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[1]

def functions():
    notebook = json.loads((ROOT / 'Cross_task_decoding.ipynb').read_text())
    source = next(''.join(c['source']) for c in notebook['cells'] if 'def training_span' in ''.join(c['source']))
    nodes = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)]
    namespace = dict(np=np, LinearSVC=LinearSVC, C=1., SEED=20261027, warnings=warnings,
                     threadpool_limits=threadpool_limits, ConvergenceWarning=ConvergenceWarning)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), '<notebook>', 'exec'), namespace)
    return namespace

def test_training_span_preserves_regularized_classifier_with_relabelings():
    f = functions(); rng = np.random.default_rng(66)
    # Rank-deficient training data; targets may contain components outside its span.
    a = rng.normal(size=(20, 11)) @ rng.normal(size=(11, 80))
    b = rng.normal(size=(8, 80))
    reduced, targets = f['training_span'](a, [b])
    assert reduced.shape == (20, 11)
    for _ in range(4):
        y = np.tile([1, -1], (10, 1)) * rng.choice([-1, 1], size=(10, 1))
        full = f['svm']().fit(a, y.ravel()).decision_function(b)
        compact = f['svm']().fit(reduced, y.ravel()).decision_function(targets[0])
        np.testing.assert_allclose(full, compact, atol=2e-3, rtol=2e-3)

def test_swaps_refit_training_and_score_held_out_labels_in_both_tasks():
    f = functions(); rng = np.random.default_rng(74)
    x = rng.normal(size=(14, 2, 2, 25))
    folds = list(KFold(n_splits=3, shuffle=True, random_state=9).split(x))
    compressed = []
    for train, test in folds:
        a, targets = f['training_span'](x[train, 0].reshape(-1, 25),
                                       [x[test, task].reshape(-1, 25) for task in range(2)])
        compressed.append((train, test, a, targets))
    swaps = rng.choice([-1, 1], size=len(x))
    compact, iterations = f['permuted_accuracy'](compressed, swaps)
    count = np.zeros(2)
    for train, test in folds:
        labels = (np.tile([1, -1], (len(train), 1)) * swaps[train, None]).ravel()
        full = f['svm']().fit(x[train, 0].reshape(-1, 25), labels)
        for task in range(2):
            score = full.decision_function(x[test, task].reshape(-1, 25)).reshape(-1, 2)
            count[task] += ((score[:, 0] - score[:, 1]) * swaps[test] > 0).sum()
    np.testing.assert_equal(compact, count / len(x))
    assert iterations < 100000
    # Swapping every person's labels reverses both training and test labels, preserving accuracy.
    np.testing.assert_equal(f['permuted_accuracy'](compressed, swaps)[0],
                            f['permuted_accuracy'](compressed, -swaps)[0])

def test_parallel_randomizations_match_serial_results():
    from joblib import Parallel, delayed, parallel_config
    f = functions(); rng = np.random.default_rng(81)
    x = rng.normal(size=(12, 2, 2, 18))
    compressed = []
    for train, test in KFold(n_splits=3, shuffle=True, random_state=2).split(x):
        a, targets = f['training_span'](x[train, 0].reshape(-1, 18),
                                       [x[test, t].reshape(-1, 18) for t in range(2)])
        compressed.append((train, test, a, targets))
    flips = rng.choice([-1, 1], size=(5, len(x)))
    serial = [f['permuted_accuracy'](compressed, swap) for swap in flips]
    with parallel_config(backend='loky', n_jobs=2, inner_max_num_threads=1):
        parallel = Parallel()(delayed(f['permuted_accuracy'])(compressed, swap) for swap in flips)
    for expected, actual in zip(serial, parallel):
        np.testing.assert_equal(actual[0], expected[0])
        assert actual[1] == expected[1]
