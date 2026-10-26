from terraform_mapping import get_terraform_recommendation

def detect_unused_ips(addresses):
    findings = []
    for address in addresses:
        if address["status"] != "RESERVED" or address["users"]:
            continue
        findings.append({"detector": "unused_ip", "resource_type": "static_ip", "resource_name": address["name"], "severity": "MEDIUM", "issue": "Reserved static IP is not attached to a resource.", "evidence": {"status": address["status"], "address": address["address"], "users": []}, "recommendation": "If no longer required, remove the Terraform module managing this reservation.", "terraform": get_terraform_recommendation(address.get("labels", {})), "approval_required": True})
    return findings
