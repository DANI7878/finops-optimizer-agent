from terraform_mapping import get_terraform_recommendation

def detect_orphan_disks(disks):
    findings = []
    for disk in disks:
        if disk["users"]:
            continue
        findings.append({"detector": "orphan_disk", "resource_type": "persistent_disk", "resource_name": disk["name"], "location": disk["zone"], "severity": "HIGH", "issue": "Persistent disk is not attached to any VM.", "evidence": {"users": [], "size_gb": disk["size_gb"], "disk_type": disk["type"]}, "recommendation": "Verify that the disk contains no required data. If unnecessary, remove its Terraform configuration.", "terraform": get_terraform_recommendation(disk.get("labels", {})), "approval_required": True})
    return findings
