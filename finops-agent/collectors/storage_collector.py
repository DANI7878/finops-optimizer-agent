from google.cloud import storage

def collect_buckets(project_id: str) -> list[dict]:
    client = storage.Client(project=project_id)
    items = []
    for bucket in client.list_buckets():
        bucket.reload()
        items.append({"name": bucket.name, "location": bucket.location, "storage_class": bucket.storage_class, "versioning_enabled": bucket.versioning_enabled, "lifecycle_rules": list(bucket.lifecycle_rules or []), "labels": dict(bucket.labels or {})})
    return items
