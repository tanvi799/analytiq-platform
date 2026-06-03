"""
AnalytIQ — Week 6: Customer Segmentation (K-Means)
Clusters users into meaningful segments using RFM features.
Run: python ml/train_segmentation.py
"""

import boto3
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA

REGION  = "ap-southeast-2"
ACCOUNT = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]
PROCESSED_BUCKET = f"analytiq-processed-{ACCOUNT}"
s3 = boto3.client("s3", region_name=REGION)

print("=== AnalytIQ Customer Segmentation (K-Means) ===\n")

# ── 1. Load features ──────────────────────────────────────────────────────────
df = pd.read_csv("ml/features_with_rfm.csv")
print(f"Loaded {len(df)} users")

# RFM features for clustering
CLUSTER_FEATURES = [
    "days_since_last_seen",   # Recency
    "total_sessions",         # Frequency
    "total_events",           # Monetary proxy
    "unique_pages",           # Breadth of usage
    "account_age_days",       # Tenure
]

X = df[CLUSTER_FEATURES].fillna(0)

# ── 2. Scale features ─────────────────────────────────────────────────────────
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ── 3. Find optimal K using elbow + silhouette ────────────────────────────────
print("Finding optimal number of clusters...")
inertias    = []
silhouettes = []
k_range     = range(2, 9)

for k in k_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    inertias.append(km.inertia_)
    silhouettes.append(silhouette_score(X_scaled, labels))
    print(f"  K={k}  inertia={km.inertia_:.0f}  silhouette={silhouettes[-1]:.3f}")

best_k = k_range[np.argmax(silhouettes)]
print(f"\n  Best K = {best_k} (highest silhouette score)")

# ── 4. Train final model ──────────────────────────────────────────────────────
print(f"\nTraining K-Means with K={best_k}...")
kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
df["cluster"] = kmeans.fit_predict(X_scaled)

# ── 5. Label clusters meaningfully ───────────────────────────────────────────
# Analyse each cluster to assign a human-readable label
cluster_stats = df.groupby("cluster")[CLUSTER_FEATURES].mean()
cluster_stats["size"] = df.groupby("cluster").size()

print("\nCluster profiles:")
print(cluster_stats.round(1).to_string())

# Auto-label based on recency and activity
def label_cluster(row):
    recency  = row["days_since_last_seen"]
    activity = row["total_events"]
    sessions = row["total_sessions"]
    if recency < 2 and activity > cluster_stats["total_events"].median():
        return "power_users"
    elif recency < 3:
        return "regular_users"
    elif recency < 5 and sessions > 1:
        return "at_risk"
    elif activity < cluster_stats["total_events"].quantile(0.25):
        return "dormant"
    else:
        return "new_users"

cluster_labels = {
    i: label_cluster(cluster_stats.loc[i])
    for i in cluster_stats.index
}
print(f"\nCluster labels: {cluster_labels}")
df["cluster_label"] = df["cluster"].map(cluster_labels)

# ── 6. Segment summary ────────────────────────────────────────────────────────
print("\n── Segment Summary ──────────────────────────────────")
summary = (
    df.groupby("cluster_label")
    .agg(
        users          =("user_id",            "count"),
        avg_events     =("total_events",        "mean"),
        avg_sessions   =("total_sessions",      "mean"),
        avg_recency    =("days_since_last_seen", "mean"),
        churn_rate     =("churned",             "mean"),
    )
    .round(2)
    .sort_values("avg_events", ascending=False)
)
print(summary.to_string())

# ── 7. Save model and scores ──────────────────────────────────────────────────
print("\nSaving segmentation model...")
joblib.dump(kmeans, "ml/segmentation_model.pkl")
joblib.dump(scaler, "ml/segmentation_scaler.pkl")

seg_df = df[["user_id", "cluster", "cluster_label"]].copy()
seg_df.to_csv("ml/segments.csv", index=False)

s3.put_object(
    Bucket=PROCESSED_BUCKET,
    Key="ml-features/segments.csv",
    Body=seg_df.to_csv(index=False).encode("utf-8"),
    ContentType="text/csv",
)
print("  ✓ ml/segmentation_model.pkl")
print("  ✓ ml/segments.csv")
print(f"  ✓ Uploaded to s3://{PROCESSED_BUCKET}/ml-features/segments.csv")

# ── 8. Plots ──────────────────────────────────────────────────────────────────
print("\nGenerating plots...")
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
fig.suptitle("AnalytIQ — Customer Segmentation", fontsize=13, fontweight="bold")

COLORS = ["#1D9E75","#378ADD","#EF9F27","#7F77DD","#E24B4A","#B4B2A9"]

# Elbow curve
axes[0].plot(list(k_range), inertias, "o-", color="#1D9E75", linewidth=2)
axes[0].set_xlabel("Number of clusters (K)")
axes[0].set_ylabel("Inertia")
axes[0].set_title("Elbow Curve")
axes[0].axvline(best_k, color="#E24B4A", linestyle="--", alpha=0.7, label=f"Best K={best_k}")
axes[0].legend()

# Silhouette scores
axes[1].plot(list(k_range), silhouettes, "o-", color="#378ADD", linewidth=2)
axes[1].set_xlabel("Number of clusters (K)")
axes[1].set_ylabel("Silhouette Score")
axes[1].set_title("Silhouette Scores")
axes[1].axvline(best_k, color="#E24B4A", linestyle="--", alpha=0.7)

# PCA scatter plot of clusters
pca = PCA(n_components=2, random_state=42)
X_pca = pca.fit_transform(X_scaled)
for i, (cluster_id, label) in enumerate(cluster_labels.items()):
    mask = df["cluster"] == cluster_id
    axes[2].scatter(
        X_pca[mask, 0], X_pca[mask, 1],
        c=COLORS[i % len(COLORS)], label=label, alpha=0.7, s=40
    )
axes[2].set_title(f"Clusters (PCA projection)")
axes[2].legend(fontsize=8)
axes[2].set_xlabel("PC1")
axes[2].set_ylabel("PC2")

plt.tight_layout()
plt.savefig("ml/segmentation_plots.png", dpi=150, bbox_inches="tight")
print("  ✓ ml/segmentation_plots.png")

print(f"""
╔══════════════════════════════════════════════╗
║     Segmentation Training Complete!          ║
╠══════════════════════════════════════════════╣
║  Optimal K        : {best_k}                          ║
║  Silhouette score : {max(silhouettes):.4f}                  ║
║  Users segmented  : {len(df)}                        ║
╚══════════════════════════════════════════════╝
  → Resume bullet: "K-Means segmentation (K={best_k})
    identified {best_k} customer archetypes via RFM clustering
    (silhouette={max(silhouettes):.2f})"
""")
