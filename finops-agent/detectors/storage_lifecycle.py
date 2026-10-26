from terraform_mapping import get_terraform_recommendation


def detect_missing_lifecycle(buckets):
    findings = []
    for bucket in buckets:
        labels = bucket.get("labels", {})
        if labels.get("project") != "finops-lab":
            continue
        if labels.get("purpose") == "access-logs" or bucket["lifecycle_rules"]:
            continue
        findings.append({
            "detector": "storage_lifecycle",
            "resource_type": "storage_bucket",
            "resource_name": bucket["name"],
            "severity": "MEDIUM",
            "issue": "Storage bucket has no lifecycle policy.",
            "evidence": {
                "storage_class": bucket["storage_class"],
                "versioning_enabled": bucket["versioning_enabled"],
                "lifecycle_rule_count": 0,
            },
            "recommendation": "Add lifecycle rules if the bucket is required. Consider deletion only if a human confirms the bucket itself is unnecessary.",
            "terraform": get_terraform_recommendation(labels),
            "approval_required": True,
        })
    return findings
