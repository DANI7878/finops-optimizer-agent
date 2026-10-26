from terraform_mapping import get_terraform_recommendation


def detect_missing_lifecycle(
    buckets: list[dict],
) -> list[dict]:
    findings = []

    for bucket in buckets:
        labels = bucket.get("labels", {})

        # Only analyze buckets explicitly belonging to the FinOps waste lab.
        #
        # This prevents infrastructure/support buckets such as:
        # - Terraform state bucket
        # - Cloud Run source bucket
        # - other project-level buckets
        #
        # from being incorrectly reported as FinOps waste.
        if labels.get("project") != "finops-lab":
            continue

        # Dedicated logging destination is infrastructure required
        # by the lab and should not be treated as waste.
        if labels.get("purpose") == "access-logs":
            continue

        # Bucket already has lifecycle management.
        if bucket["lifecycle_rules"]:
            continue

        terraform = get_terraform_recommendation(
            labels
        )

        findings.append(
            {
                "detector": "storage_lifecycle",
                "resource_type": "storage_bucket",
                "resource_name": bucket["name"],
                "severity": "MEDIUM",

                "issue": (
                    "Storage bucket has no lifecycle policy."
                ),

                "evidence": {
                    "storage_class": bucket["storage_class"],
                    "versioning_enabled": (
                        bucket["versioning_enabled"]
                    ),
                    "lifecycle_rule_count": 0,
                },

                "recommendation": (
                    "Add lifecycle rules if the bucket is required. "
                    "Consider deletion only if a human confirms "
                    "the bucket itself is unnecessary."
                ),

                "terraform": terraform,

                "approval_required": True,
            }
        )

    return findings