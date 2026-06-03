"""
AnalytIQ — Week 5: Churn Prediction Model
Trains an XGBoost churn classifier on the feature matrix.
Run: python ml/train_churn_model.py
"""

import boto3
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report, roc_auc_score,
    RocCurveDisplay, ConfusionMatrixDisplay
)
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

REGION  = "ap-southeast-2"
ACCOUNT = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]
PROCESSED_BUCKET = f"analytiq-processed-{ACCOUNT}"

s3 = boto3.client("s3", region_name=REGION)


# ── 1. Load feature matrix ────────────────────────────────────────────────────
print("=== AnalytIQ Churn Model Training ===\n")
print("Loading feature matrix...")
df = pd.read_csv("ml/features_with_rfm.csv")
print(f"  {len(df)} users, {df['churned'].sum()} churned ({df['churned'].mean()*100:.1f}%)")


# ── 2. Feature engineering ────────────────────────────────────────────────────
print("\nEngineering features...")

# Encode categorical columns
le_segment  = LabelEncoder()
le_plan     = LabelEncoder()
le_country  = LabelEncoder()
le_rfm      = LabelEncoder()

df["segment_enc"]   = le_segment.fit_transform(df["segment"].fillna("unknown"))
df["plan_enc"]      = le_plan.fit_transform(df["plan"].fillna("unknown"))
df["country_enc"]   = le_country.fit_transform(df["country"].fillna("unknown"))
df["rfm_label_enc"] = le_rfm.fit_transform(df["rfm_label"].fillna("unknown"))

# Select final features
FEATURES = [
    "total_events",
    "total_sessions",
    "unique_pages",
    "days_since_last_seen",
    "account_age_days",
    "events_per_day",
    "sessions_per_day",
    "r_score",
    "f_score",
    "m_score",
    "rfm_score",
    "segment_enc",
    "plan_enc",
    "rfm_label_enc",
]

X = df[FEATURES].fillna(0)
y = df["churned"]

print(f"  Features: {FEATURES}")
print(f"  X shape: {X.shape}")


# ── 3. Train/test split ───────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\nTrain: {len(X_train)} | Test: {len(X_test)}")


# ── 4. Baseline — Logistic Regression ────────────────────────────────────────
print("\n── Baseline: Logistic Regression ───────────────────")
lr = LogisticRegression(max_iter=1000, random_state=42)
lr.fit(X_train, y_train)
lr_preds = lr.predict(X_test)
lr_probs = lr.predict_proba(X_test)[:, 1]
lr_auc   = roc_auc_score(y_test, lr_probs)
print(f"  AUC-ROC: {lr_auc:.4f}")
print(classification_report(y_test, lr_preds, target_names=["active", "churned"]))


# ── 5. XGBoost model ──────────────────────────────────────────────────────────
print("── XGBoost ──────────────────────────────────────────")
xgb = XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    scale_pos_weight=len(y[y==0]) / max(len(y[y==1]), 1),  # handle class imbalance
    random_state=42,
    eval_metric="auc",
    verbosity=0,
)
xgb.fit(X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False)

xgb_preds = xgb.predict(X_test)
xgb_probs = xgb.predict_proba(X_test)[:, 1]
xgb_auc   = roc_auc_score(y_test, xgb_probs)
print(f"  AUC-ROC: {xgb_auc:.4f}")
print(classification_report(xgb_preds, y_test, target_names=["active", "churned"]))


# ── 6. Cross-validation ───────────────────────────────────────────────────────
print("── Cross-validation (5-fold) ────────────────────────")
cv_scores = cross_val_score(xgb, X, y, cv=5, scoring="roc_auc")
print(f"  AUC scores: {cv_scores.round(3)}")
print(f"  Mean AUC:   {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")


# ── 7. Feature importance ─────────────────────────────────────────────────────
print("\n── Feature Importance ───────────────────────────────")
importance_df = pd.DataFrame({
    "feature":   FEATURES,
    "importance": xgb.feature_importances_,
}).sort_values("importance", ascending=False)
print(importance_df.to_string(index=False))


# ── 8. Score ALL users (not just test set) ────────────────────────────────────
print("\nScoring all users...")
df["churn_score"] = xgb.predict_proba(X)[:, 1]
df["churn_risk"]  = pd.cut(
    df["churn_score"],
    bins=[0, 0.33, 0.66, 1.0],
    labels=["low", "medium", "high"]
)

scores_df = df[["user_id", "churn_score", "churn_risk", "segment"]].copy()
scores_df["churn_score"] = scores_df["churn_score"].round(4)

print(f"\nChurn risk breakdown:")
print(scores_df["churn_risk"].value_counts().to_string())


# ── 9. Save model and scores ──────────────────────────────────────────────────
print("\nSaving model...")
joblib.dump(xgb,        "ml/churn_model.pkl")
joblib.dump(le_segment, "ml/le_segment.pkl")
joblib.dump(le_plan,    "ml/le_plan.pkl")
joblib.dump(le_country, "ml/le_country.pkl")
joblib.dump(le_rfm,     "ml/le_rfm.pkl")

# Save scores locally and to S3
scores_df.to_csv("ml/churn_scores.csv", index=False)

s3.put_object(
    Bucket=PROCESSED_BUCKET,
    Key="ml-features/churn_scores.csv",
    Body=scores_df.to_csv(index=False).encode("utf-8"),
    ContentType="text/csv",
)

# Save feature importance
importance_df.to_csv("ml/feature_importance.csv", index=False)

print("  ✓ ml/churn_model.pkl")
print("  ✓ ml/churn_scores.csv")
print("  ✓ ml/feature_importance.csv")
print(f"  ✓ Scores uploaded to s3://{PROCESSED_BUCKET}/ml-features/churn_scores.csv")


# ── 10. Plot results ──────────────────────────────────────────────────────────
print("\nGenerating evaluation plots...")
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
fig.suptitle("AnalytIQ — Churn Model Evaluation", fontsize=13, fontweight="bold")

# ROC curve
RocCurveDisplay.from_predictions(y_test, xgb_probs, ax=axes[0], color="#1D9E75")
axes[0].set_title(f"ROC Curve (AUC = {xgb_auc:.3f})")
axes[0].plot([0,1],[0,1],"--", color="gray", alpha=0.5)

# Confusion matrix
ConfusionMatrixDisplay.from_predictions(
    y_test, xgb_preds, ax=axes[1],
    display_labels=["Active","Churned"],
    colorbar=False, cmap="Greens"
)
axes[1].set_title("Confusion Matrix")

# Feature importance
top10 = importance_df.head(10)
axes[2].barh(top10["feature"], top10["importance"], color="#1D9E75")
axes[2].set_title("Top 10 Feature Importance")
axes[2].invert_yaxis()

plt.tight_layout()
plt.savefig("ml/model_evaluation.png", dpi=150, bbox_inches="tight")
print("  ✓ ml/model_evaluation.png")

print(f"""
╔══════════════════════════════════════════════╗
║       Churn Model Training Complete!         ║
╠══════════════════════════════════════════════╣
║  Logistic Regression AUC : {lr_auc:.4f}            ║
║  XGBoost AUC             : {xgb_auc:.4f}            ║
║  Cross-val Mean AUC      : {cv_scores.mean():.4f}            ║
╚══════════════════════════════════════════════╝
  → Resume bullet: "Trained XGBoost churn model
    (AUC {xgb_auc:.2f}) on 198 users with 14 features"
""")
