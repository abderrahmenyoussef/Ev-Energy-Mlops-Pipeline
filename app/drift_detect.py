from typing import Dict, Any, Tuple
import numpy as np


def compute_drift_scores(
    baseline_stats: Dict[str, Any],
    recent_batch: Dict[str, list],
    monitored_features: list,
) -> Tuple[Dict[str, float], float]:
    """
    recent_batch: dict feature -> list of values observed recently (e.g. last N requests)
    Returns: feature_scores, global_score
    feature_score is abs((mean_recent - mean_base)/std_base)
    """
    feature_scores: Dict[str, float] = {}

    for feat in monitored_features:
        if feat not in baseline_stats:
            continue
        base_mean = float(baseline_stats[feat]["mean"])
        base_std = float(baseline_stats[feat]["std"]) + 1e-6

        vals = recent_batch.get(feat, [])
        if len(vals) < 5:
            feature_scores[feat] = 0.0
            continue

        recent_mean = float(np.mean(vals))
        z = abs((recent_mean - base_mean) / base_std)
        feature_scores[feat] = float(z)

    # simple global score: average z
    if feature_scores:
        global_score = float(np.mean(list(feature_scores.values())))
    else:
        global_score = 0.0

    return feature_scores, global_score
