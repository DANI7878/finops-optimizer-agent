from google.api_core.exceptions import Forbidden
from google.cloud import storage


def collect_buckets(project_id: str) -> list[dict]:
    client = storage.Client(project=project_id)

    buckets = []

    print("Collecting Cloud Storage buckets...")

    try:
        bucket_iterator = client.list_buckets(project=project_id)

        for bucket in bucket_iterator:
            try:
                lifecycle_rules = list(
                    bucket.lifecycle_rules or []
                )

                bucket_data = {
                    "name": bucket.name,
                    "location": bucket.location,
                    "storage_class": bucket.storage_class,
                    "versioning_enabled": (
                        bucket.versioning_enabled
                    ),
                    "lifecycle_rules": lifecycle_rules,
                    "labels": dict(bucket.labels or {}),
                }

                buckets.append(bucket_data)

                print(
                    f"  Found bucket: {bucket.name}"
                )

            except Forbidden as exc:
                print(
                    f"WARNING: Cannot inspect bucket "
                    f"{bucket.name}: {exc}"
                )

                continue

    except Forbidden as exc:
        print(
            "WARNING: Unable to list Cloud Storage buckets."
        )
        print(exc)

        return []

    print(
        f"Collected {len(buckets)} accessible "
        f"Cloud Storage bucket(s)."
    )

    return buckets