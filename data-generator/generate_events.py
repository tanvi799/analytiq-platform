"""
AnalytIQ — Synthetic Event Generator
Simulates realistic SaaS user events and pushes them to Kinesis.
Run this to populate your data lake during development.
"""

import json
import random
import time
import uuid
import boto3
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("en_AU")   # Australian locale for realistic names

# ── Config ────────────────────────────────────────────────────────────────────
STREAM_NAME = "analytiq-events"
REGION = "ap-southeast-2"
NUM_USERS = 200         # simulated user base
EVENTS_PER_BATCH = 50   # records per Kinesis PutRecords call
BATCHES = 20            # total batches to send (20 × 50 = 1,000 events)

EVENT_TYPES = [
    "page_view", "page_view", "page_view",      # page views are most common
    "button_click", "button_click",
    "feature_used",
    "export_data",
    "invite_team_member",
    "upgrade_plan_viewed",
    "login", "logout",
]

PAGES = [
    "/dashboard", "/dashboard", "/dashboard",
    "/reports", "/reports",
    "/settings",
    "/billing",
    "/integrations",
    "/users",
    "/analytics",
]

kinesis = boto3.client("kinesis", region_name=REGION)


def make_user_pool(n: int) -> list[dict]:
    """
    Generate a pool of users with behavioural archetypes.
    Churn likelihood is baked in — used to create realistic dropout patterns.
    """
    archetypes = [
        {"segment": "power_user",   "churn_prob": 0.05, "weight": 20},
        {"segment": "regular",      "churn_prob": 0.20, "weight": 35},
        {"segment": "at_risk",      "churn_prob": 0.65, "weight": 25},
        {"segment": "new_user",     "churn_prob": 0.30, "weight": 15},
        {"segment": "dormant",      "churn_prob": 0.85, "weight": 5},
    ]
    pool = []
    for _ in range(n):
        archetype = random.choices(archetypes, weights=[a["weight"] for a in archetypes])[0]
        signup_days_ago = random.randint(1, 365)
        pool.append({
            "user_id":      str(uuid.uuid4()),
            "company":      fake.company(),
            "email":        fake.email(),
            "segment":      archetype["segment"],
            "churn_prob":   archetype["churn_prob"],
            "plan":         random.choice(["free", "starter", "pro", "enterprise"]),
            "country":      random.choice(["AU", "AU", "AU", "NZ", "US", "GB"]),
            "signed_up_at": (datetime.utcnow() - timedelta(days=signup_days_ago)).isoformat(),
        })
    return pool


def make_event(user: dict) -> dict:
    """Build a single tracking event for a user."""
    # Dormant/at-risk users fire fewer events (realistic)
    if user["segment"] in ("dormant", "at_risk") and random.random() < 0.6:
        return None  # skip — user is inactive

    ts = datetime.utcnow() - timedelta(
        minutes=random.randint(0, 60 * 24 * 7)   # spread over last 7 days
    )

    return {
        "event_id":         str(uuid.uuid4()),
        "event_type":       random.choice(EVENT_TYPES),
        "user_id":          user["user_id"],
        "company":          user["company"],
        "segment":          user["segment"],
        "plan":             user["plan"],
        "country":          user["country"],
        "page":             random.choice(PAGES),
        "session_id":       str(uuid.uuid4())[:8],
        "timestamp":        ts.isoformat() + "Z",
        "properties": {
            "duration_ms":  random.randint(200, 15000),
            "referrer":     random.choice([None, "google", "email", "direct"]),
            "device":       random.choice(["desktop", "desktop", "mobile", "tablet"]),
        },
    }


def push_to_kinesis(events: list[dict]) -> dict:
    """Send a batch of events to Kinesis using PutRecords."""
    records = [
        {
            "Data": json.dumps(e).encode("utf-8"),
            "PartitionKey": e["user_id"],   # partition by user for ordering
        }
        for e in events
    ]
    response = kinesis.put_records(StreamName=STREAM_NAME, Records=records)
    return response


def main():
    print(f"Generating {NUM_USERS} users and {BATCHES * EVENTS_PER_BATCH} events...")
    users = make_user_pool(NUM_USERS)

    total_sent = 0
    total_failed = 0

    for batch_num in range(1, BATCHES + 1):
        events = []
        attempts = 0
        while len(events) < EVENTS_PER_BATCH and attempts < EVENTS_PER_BATCH * 3:
            user = random.choice(users)
            event = make_event(user)
            if event:
                events.append(event)
            attempts += 1

        if not events:
            continue

        response = push_to_kinesis(events)
        failed = response.get("FailedRecordCount", 0)
        total_sent += len(events) - failed
        total_failed += failed

        print(f"  Batch {batch_num:02d}/{BATCHES} — sent {len(events)} events "
              f"({failed} failed)")

        time.sleep(0.5)   # stay within Kinesis rate limits

    print(f"\n✅ Done! Sent {total_sent} events, {total_failed} failed.")
    print(f"   Check your S3 bucket: analytiq-raw-events-<your-account-id>")


if __name__ == "__main__":
    main()
