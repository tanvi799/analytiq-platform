"""
Unit tests for the ML pipeline: RFM feature engineering and segmentation.

Run: pytest tests/test_ml_pipeline.py -v

NOTE: adjust the import paths below to match your actual module layout
(e.g. if train_segmentation.py is not directly importable, refactor the
relevant functions into ml/utils.py and import from there).
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_user_df():
    """A small synthetic user feature table mirroring features_with_rfm.csv."""
    return pd.DataFrame({
        "user_id": [f"u{i}" for i in range(10)],
        "days_since_last_seen": [0, 1, 2, 5, 6, 7, 0, 1, 7, 6],
        "total_sessions": [10, 8, 6, 2, 1, 1, 9, 7, 1, 1],
        "total_events": [15, 12, 9, 3, 1, 1, 14, 11, 1, 1],
        "unique_pages": [6, 5, 4, 2, 1, 1, 6, 5, 1, 1],
        "account_age_days": [7, 7, 6, 7, 5, 7, 6, 7, 4, 7],
        "churned": [0, 0, 0, 1, 1, 1, 0, 0, 1, 1],
    })


# ── RFM scoring ────────────────────────────────────────────────────────────────

def compute_rfm_score(row, medians):
    """Mirror of the RFM scoring logic: higher = more engaged."""
    r = 1 if row["days_since_last_seen"] > medians["days_since_last_seen"] else 5
    f = 5 if row["total_sessions"] > medians["total_sessions"] else 1
    m = 5 if row["total_events"] > medians["total_events"] else 1
    return (r + f + m) / 3


def test_rfm_score_range(sample_user_df):
    """RFM scores should always fall within [1, 5]."""
    medians = sample_user_df[["days_since_last_seen", "total_sessions", "total_events"]].median()
    scores = sample_user_df.apply(lambda row: compute_rfm_score(row, medians), axis=1)
    assert scores.between(1, 5).all()


def test_rfm_score_active_user_scores_higher_than_inactive(sample_user_df):
    """A recently-active, high-frequency user should score higher than a dormant one."""
    medians = sample_user_df[["days_since_last_seen", "total_sessions", "total_events"]].median()
    active_row = sample_user_df.iloc[0]   # recent, high sessions/events
    inactive_row = sample_user_df.iloc[5]  # 7 days inactive, 1 session

    active_score = compute_rfm_score(active_row, medians)
    inactive_score = compute_rfm_score(inactive_row, medians)

    assert active_score > inactive_score


# ── Feature preprocessing ─────────────────────────────────────────────────────

def test_log_transform_reduces_skew(sample_user_df):
    """Log1p transform should reduce skewness of right-skewed count features."""
    raw = sample_user_df["total_events"]
    logged = np.log1p(raw)

    assert raw.skew() > logged.skew(), "log1p should reduce positive skew"
    assert (logged >= 0).all()


def test_drop_constant_features():
    """Near-constant features (single unique value) should be dropped before clustering."""
    df = pd.DataFrame({
        "varies": [1, 2, 3, 4, 5],
        "constant": [7, 7, 7, 7, 7],
    })
    nonconstant = df.loc[:, df.nunique() > 1]
    assert "constant" not in nonconstant.columns
    assert "varies" in nonconstant.columns


# ── Clustering ─────────────────────────────────────────────────────────────────

def test_kmeans_produces_requested_number_of_clusters(sample_user_df):
    """K-Means with K=3 should assign exactly 3 distinct cluster labels."""
    features = sample_user_df[["days_since_last_seen", "total_sessions", "total_events"]]
    X_scaled = StandardScaler().fit_transform(features)

    km = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    assert len(set(labels)) == 3
    assert len(labels) == len(sample_user_df)


def test_silhouette_score_is_valid_range(sample_user_df):
    """Silhouette score must be within [-1, 1] for a valid clustering."""
    features = sample_user_df[["days_since_last_seen", "total_sessions", "total_events"]]
    X_scaled = StandardScaler().fit_transform(features)

    km = KMeans(n_clusters=2, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    score = silhouette_score(X_scaled, labels)

    assert -1.0 <= score <= 1.0


def test_clustering_separates_active_from_inactive(sample_user_df):
    """
    With K=2, clustering on recency-correlated features should split users
    into an 'active' group (low days_since_last_seen) and an 'inactive'
    group (high days_since_last_seen) — matching the README's documented
    finding that recency dominates cluster structure.
    """
    features = sample_user_df[["days_since_last_seen", "total_sessions", "total_events"]]
    X_scaled = StandardScaler().fit_transform(features)

    km = KMeans(n_clusters=2, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    df = sample_user_df.copy()
    df["cluster"] = labels

    cluster_recency = df.groupby("cluster")["days_since_last_seen"].mean()
    # The two clusters should have meaningfully different average recency
    assert abs(cluster_recency.iloc[0] - cluster_recency.iloc[1]) > 1.0
