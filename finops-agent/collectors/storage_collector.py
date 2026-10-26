from google.api_core.exceptions import Forbidden
from google.cloud import storage


def collect_buckets(project_id: str) -> list[dict]:
    client = storage.Client(project=project_id)
    buckets = []
    print("Collecting Cloud Storage buckets...")
    try:
        for bucket in client.list_buckets(project=project_id):
            try:
                buckets.append({
                    "name": bucket.name,
                    "location": bucket.location,
                    "storage_class": bucket.storage_class,
                    "versioning_enabled": bucket.versioning_enabled,
                    "lifecycle_rules": list(bucket.lifecycle_rules or []),
                    "labels": dict(bucket.labels or {}),
                })
                print(f"  Found bucket: {bucket.name}")
            except Forbidden as exc:
                print(f"WARNING: Cannot inspect bucket {bucket.name}: {exc}")
    except Forbidden as exc:
        print(f"WARNING: Unable to list Cloud Storage buckets: {exc}")
        return []
    print(f"Collected {len(buckets)} accessible Cloud Storage bucket(s).")
    return buckets
