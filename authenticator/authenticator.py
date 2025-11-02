#!/usr/bin/env python3
"""
Gesture Authenticator using Multiple Algorithms
Compares: DTW, TWED, Shape DTW, and Hidden Markov Model (HMM)
Uses demo gestures from example_data.py (2D: 80 samples × 2 dimensions [X, Y])
Also loads trained gestures from examples/ folder if available
"""

import numpy as np
from dtaidistance import dtw
from hmmlearn.hmm import GaussianHMM
import sys
import warnings
import os
import importlib.util
from pathlib import Path

# Suppress sklearn convergence warnings
warnings.filterwarnings('ignore')

# Configuration - Thresholds for each algorithm (OPTIMIZED for 2D data)
SIMILARITY_THRESHOLD_DTW = 0.04  # Changed from 0.055 - more lenient
SIMILARITY_THRESHOLD_TWED = 0.30  # Tightened from 0.35 - reduce false positives
SIMILARITY_THRESHOLD_SHAPEDTW = 0.12  # Tightened from 0.14 - reduce false positives
SIMILARITY_THRESHOLD_HMM = -1.25  # Tightened from -1.2 - more selective (more negative = stricter)
HMM_N_STATES = 3


def load_trained_gestures():
    """Load all trained gesture files from examples/ folder."""
    gestures = {}
    examples_dir = Path("examples")
    
    if not examples_dir.exists():
        return gestures
    
    # Find all example_data_*.py files
    for py_file in examples_dir.glob("example_data_*.py"):
        try:
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Extract gesture name from filename (example_data_GESTURE_NAME.py)
            gesture_name = py_file.stem.replace("example_data_", "")
            
            # Each trained file has TRAINING_DATA with 5 examples
            if hasattr(module, 'TRAINING_DATA'):
                gestures[gesture_name] = {
                    "training": module.TRAINING_DATA,
                    "source": "trained"
                }
        except Exception as e:
            pass
    
    return gestures


def normalize_series(series):
    """Normalize a 2D time series (80, 2) to have mean 0 and std 1 per column."""
    if series.shape[0] == 0:
        return series
    
    normalized = series.copy().astype(np.float64)
    
    # Normalize each column (X and Y separately)
    for col in range(normalized.shape[1]):
        mean = np.mean(normalized[:, col])
        std = np.std(normalized[:, col])
        if std == 0:
            std = 1
        normalized[:, col] = (normalized[:, col] - mean) / std
    
    return normalized


# ============================================================================
# ALGORITHM 1: DTW (Dynamic Time Warping)
# ============================================================================
def dtw_distance(series1, series2):
    """
    Calculate DTW distance between two 2D time series (160, 2).
    Compares X and Y separately, then combines scores.
    This avoids interference between different trend axes.
    """
    try:
        # Extract X and Y separately
        x1 = series1[:, 0]  # X values from series1
        y1 = series1[:, 1]  # Y values from series1
        x2 = series2[:, 0]  # X values from series2
        y2 = series2[:, 1]  # Y values from series2
        
        # Calculate DTW distance for each axis independently
        dist_x = dtw.distance(x1, x2) / len(x1)
        dist_y = dtw.distance(y1, y2) / len(y1)
        
        # Combine scores (equal weight for both axes)
        combined_distance = (dist_x + dist_y) / 2.0
        
        return combined_distance
    except:
        return float('inf')


# ============================================================================
# ALGORITHM 2: TWED (Time Warp Edit Distance)
# ============================================================================
def twed_distance(series1, series2, penalty=1.0):
    """Calculate TWED distance between two 2D time series (80, 2)."""
    # Flatten for TWED
    s1_flat = series1.flatten()
    s2_flat = series2.flatten()
    
    n, m = len(s1_flat), len(s2_flat)
    cost = np.full((n + 1, m + 1), np.inf)
    cost[0, 0] = 0
    
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d = abs(s1_flat[i-1] - s2_flat[j-1])
            time_penalty = abs(i - j) * penalty
            cost[i, j] = min(
                cost[i-1, j-1] + d + time_penalty,
                cost[i-1, j] + time_penalty,
                cost[i, j-1] + time_penalty
            )
    
    return cost[n, m] / max(n, m)


# ============================================================================
# ALGORITHM 3: Shape DTW (considers local slopes/derivatives)
# ============================================================================
def shape_dtw_distance(series1, series2):
    """Calculate Shape DTW distance for 2D time series (80, 2)."""
    s1_flat = series1.flatten()
    s2_flat = series2.flatten()
    
    # Calculate derivatives (slopes)
    der1 = np.diff(s1_flat)
    der2 = np.diff(s2_flat)
    
    # Pad to match original length
    der1 = np.append(der1, 0)
    der2 = np.append(der2, 0)
    
    # Combine original values and derivatives
    combined1 = np.column_stack([s1_flat, der1])
    combined2 = np.column_stack([s2_flat, der2])
    
    if len(combined1) == len(combined2):
        value_dist = np.sum((combined1[:, 0] - combined2[:, 0]) ** 2)
        shape_dist = np.sum((combined1[:, 1] - combined2[:, 1]) ** 2)
        return np.sqrt(value_dist + shape_dist) / len(s1_flat)
    else:
        return dtw_distance(series1, series2)


# ============================================================================
# ALGORITHM 4: Hidden Markov Model (HMM) using hmmlearn
# ============================================================================
def hmm_distance(reference_gestures, test_gesture, n_states=HMM_N_STATES):
    """
    Calculate HMM-based score using hmmlearn's GaussianHMM.
    Trains on all reference gestures combined and scores test gesture.
    Returns log likelihood (higher is better).
    """
    try:
        # Train HMM on all reference gestures combined
        X_all = np.vstack([g.flatten().reshape(-1, 1) for g in reference_gestures])
        hmm = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=1000, random_state=42)
        hmm.fit(X_all)
        
        # Score test gesture
        X_test = test_gesture.flatten().reshape(-1, 1)
        log_likelihood = hmm.score(X_test)
        
        # Normalize by gesture length for consistency
        normalized_score = log_likelihood / len(test_gesture.flatten())
        return normalized_score
    except Exception as e:
        return float('-inf')


# ============================================================================
# Testing Function
# ============================================================================
def test_all_algorithms(gesture_name, training_gestures, test_similar_list, test_different_list, verbose=False):
    """Test all 4 algorithms on a gesture set."""
    results = {
        "DTW": {"correct": 0, "total": 0},
        "TWED": {"correct": 0, "total": 0},
        "ShapeDTW": {"correct": 0, "total": 0},
        "HMM": {"correct": 0, "total": 0},
    }
    
    # Store scores for analysis
    scores = {
        "DTW": {"similar": [], "different": []},
        "TWED": {"similar": [], "different": []},
        "ShapeDTW": {"similar": [], "different": []},
        "HMM": {"similar": [], "different": []},
    }
    
    # Normalize all training gestures once
    training_norm = [normalize_series(g) for g in training_gestures]
    
    # Test SIMILAR gestures (should authenticate - distance <= threshold)
    for test_gesture in test_similar_list:
        test_norm = normalize_series(test_gesture)
        
        dtw_dist = min([dtw_distance(t, test_norm) for t in training_norm])
        twed_dist = min([twed_distance(t, test_norm) for t in training_norm])
        shape_dist = min([shape_dtw_distance(t, test_norm) for t in training_norm])
        hmm_score_val = hmm_distance(training_norm, test_norm)
        
        scores["DTW"]["similar"].append(dtw_dist)
        scores["TWED"]["similar"].append(twed_dist)
        scores["ShapeDTW"]["similar"].append(shape_dist)
        scores["HMM"]["similar"].append(hmm_score_val)
        
        # Check each algorithm
        if dtw_dist <= SIMILARITY_THRESHOLD_DTW:
            results["DTW"]["correct"] += 1
        results["DTW"]["total"] += 1
        
        if twed_dist <= SIMILARITY_THRESHOLD_TWED:
            results["TWED"]["correct"] += 1
        results["TWED"]["total"] += 1
        
        if shape_dist <= SIMILARITY_THRESHOLD_SHAPEDTW:
            results["ShapeDTW"]["correct"] += 1
        results["ShapeDTW"]["total"] += 1
        
        if hmm_score_val >= SIMILARITY_THRESHOLD_HMM:
            results["HMM"]["correct"] += 1
        results["HMM"]["total"] += 1
    
    # Test DIFFERENT gestures (should reject - distance > threshold)
    for test_gesture in test_different_list:
        test_norm = normalize_series(test_gesture)
        
        dtw_dist = min([dtw_distance(t, test_norm) for t in training_norm])
        twed_dist = min([twed_distance(t, test_norm) for t in training_norm])
        shape_dist = min([shape_dtw_distance(t, test_norm) for t in training_norm])
        hmm_score_val = hmm_distance(training_norm, test_norm)
        
        scores["DTW"]["different"].append(dtw_dist)
        scores["TWED"]["different"].append(twed_dist)
        scores["ShapeDTW"]["different"].append(shape_dist)
        scores["HMM"]["different"].append(hmm_score_val)
        
        # Check each algorithm (different should fail the threshold)
        if dtw_dist > SIMILARITY_THRESHOLD_DTW:
            results["DTW"]["correct"] += 1
        results["DTW"]["total"] += 1
        
        if twed_dist > SIMILARITY_THRESHOLD_TWED:
            results["TWED"]["correct"] += 1
        results["TWED"]["total"] += 1
        
        if shape_dist > SIMILARITY_THRESHOLD_SHAPEDTW:
            results["ShapeDTW"]["correct"] += 1
        results["ShapeDTW"]["total"] += 1
        
        if hmm_score_val < SIMILARITY_THRESHOLD_HMM:
            results["HMM"]["correct"] += 1
        results["HMM"]["total"] += 1
    
    if verbose:
        print(f"\n📊 DETAILED SCORES FOR {gesture_name}:")
        for algo in ["DTW", "TWED", "ShapeDTW", "HMM"]:
            print(f"\n  {algo}:")
            if scores[algo]["similar"]:
                sim_vals = scores[algo]["similar"]
                print(f"    Similar:   {sim_vals} → min={min(sim_vals):.6f}, max={max(sim_vals):.6f}")
            if scores[algo]["different"]:
                diff_vals = scores[algo]["different"]
                print(f"    Different: {diff_vals} → min={min(diff_vals):.6f}, max={max(diff_vals):.6f}")
            threshold = {
                "DTW": SIMILARITY_THRESHOLD_DTW,
                "TWED": SIMILARITY_THRESHOLD_TWED,
                "ShapeDTW": SIMILARITY_THRESHOLD_SHAPEDTW,
                "HMM": SIMILARITY_THRESHOLD_HMM,
            }[algo]
            print(f"    Threshold: {threshold}")
    
    return results, scores


def main():
    """Run all tests with compact output."""
    print("\n" + "=" * 100)
    print("🎯 GESTURE AUTHENTICATION - 4 ALGORITHMS COMPARISON (2D Data)")
    print("=" * 100)
    print(f"\nThresholds (OPTIMIZED for 2D):")
    print(f"  DTW: {SIMILARITY_THRESHOLD_DTW}")
    print(f"  TWED: {SIMILARITY_THRESHOLD_TWED}")
    print(f"  ShapeDTW: {SIMILARITY_THRESHOLD_SHAPEDTW}")
    print(f"  HMM: {SIMILARITY_THRESHOLD_HMM}")
    
    # Load demo gestures from example_data.py
    print("\n📁 Loading demo gestures from example_data.py...")
    all_gestures = {}
    # The GESTURES dictionary is no longer imported, so we'll just load a placeholder
    # This part of the code will need to be updated if actual demo data is required
    # For now, we'll just print a message indicating the placeholder
    print("Placeholder: No actual demo gestures loaded. This part of the code needs to be updated.")
    
    # NOTE: Trained gestures from examples/ are only loaded when needed by canvas
    # Standalone mode focuses on demo gestures for threshold tuning
    
    if not all_gestures:
        print("❌ No gestures found!")
        return
    
    print("\n" + "-" * 100)
    print(f"{'Gesture':<25} {'DTW':<18} {'TWED':<18} {'ShapeDTW':<18} {'HMM':<18}")
    print("-" * 100)
    
    overall_results = {
        "DTW": {"total": 0, "correct": 0},
        "TWED": {"total": 0, "correct": 0},
        "ShapeDTW": {"total": 0, "correct": 0},
        "HMM": {"total": 0, "correct": 0},
    }
    
    # Test all gestures
    for gesture_name in sorted(all_gestures.keys()):
        gesture_data = all_gestures[gesture_name]
        results, scores = test_all_algorithms(
            gesture_name,
            gesture_data["training"],
            gesture_data["test_similar"],
            gesture_data["test_different"],
            verbose=False # Disable verbose output now that thresholds are tuned
        )
        
        # Calculate accuracy for each algorithm
        dtw_acc = (results["DTW"]["correct"] / results["DTW"]["total"] * 100) if results["DTW"]["total"] > 0 else 0
        twed_acc = (results["TWED"]["correct"] / results["TWED"]["total"] * 100) if results["TWED"]["total"] > 0 else 0
        shape_acc = (results["ShapeDTW"]["correct"] / results["ShapeDTW"]["total"] * 100) if results["ShapeDTW"]["total"] > 0 else 0
        hmm_acc = (results["HMM"]["correct"] / results["HMM"]["total"] * 100) if results["HMM"]["total"] > 0 else 0
        
        # Format gesture name
        gesture_short = gesture_name[:24]
        
        # Print compact results
        print(f"{gesture_short:<25} {dtw_acc:>5.1f}% ({results['DTW']['correct']}/{results['DTW']['total']})      "
              f"{twed_acc:>5.1f}% ({results['TWED']['correct']}/{results['TWED']['total']})      "
              f"{shape_acc:>5.1f}% ({results['ShapeDTW']['correct']}/{results['ShapeDTW']['total']})      "
              f"{hmm_acc:>5.1f}% ({results['HMM']['correct']}/{results['HMM']['total']})")
        
        # Track overall
        for algo in overall_results:
            overall_results[algo]["total"] += results[algo]["total"]
            overall_results[algo]["correct"] += results[algo]["correct"]
    
    # Print summary
    print("-" * 100)
    print("\n📊 OVERALL ACCURACY:")
    for algo in ["DTW", "TWED", "ShapeDTW", "HMM"]:
        data = overall_results[algo]
        acc = data["correct"] / data["total"] * 100 if data["total"] > 0 else 0
        print(f"  {algo:<12}: {acc:>6.1f}% ({data['correct']}/{data['total']})")
    
    print("\n" + "=" * 100 + "\n")


if __name__ == "__main__":
    main()
