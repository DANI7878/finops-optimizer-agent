TERRAFORM_RESOURCE_MAP = {
    "idle-vm": {
        "terraform_address": "module.idle_vm.google_compute_instance.this",
        "module_name": "idle_vm",
        "file": "environments/waste-lab/main.tf",
        "recommended_action": "INVESTIGATE",
        "deletion_scope": "module",
        "warning": "If permanently unnecessary, removing module.idle_vm destroys the Terraform-managed VM.",
    },
    "unattached-disk": {
        "terraform_address": "module.orphan_disk.google_compute_disk.this",
        "module_name": "orphan_disk",
        "file": "environments/waste-lab/main.tf",
        "recommended_action": "DELETE_CANDIDATE",
        "deletion_scope": "module",
        "warning": "Removing module.orphan_disk can destroy both the persistent disk and its managed snapshot. Verify data retention first.",
    },
    "unused-ip": {
        "terraform_address": "module.unused_ip.google_compute_address.this",
        "module_name": "unused_ip",
        "file": "environments/waste-lab/main.tf",
        "recommended_action": "DELETE_CANDIDATE",
        "deletion_scope": "module",
        "warning": "Removing module.unused_ip releases the Terraform-managed reserved static IP.",
    },
    "no-lifecycle": {
        "terraform_address": "module.no_lifecycle_bucket.google_storage_bucket.this",
        "module_name": "no_lifecycle_bucket",
        "file": "environments/waste-lab/main.tf",
        "recommended_action": "CONFIGURE",
        "deletion_scope": "review",
        "warning": "Prefer lifecycle rules if the bucket is still required. Delete only after a human confirms the bucket itself is unnecessary.",
    },
}

def get_terraform_recommendation(labels: dict):
    waste_type = labels.get("waste_type")
    mapping = TERRAFORM_RESOURCE_MAP.get(waste_type)
    if not mapping:
        return None
    return {**mapping, "human_approval_required": True, "automatic_deletion_allowed": False}
