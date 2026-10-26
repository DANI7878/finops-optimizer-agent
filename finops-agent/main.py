import json
from datetime import datetime, timezone
from pathlib import Path
from collectors.compute_collector import collect_instances
from collectors.disk_collector import collect_disks
from collectors.ip_collector import collect_addresses
from collectors.storage_collector import collect_buckets
from config import ENABLE_AI, PROJECT_ID
from detectors.idle_vm import detect_idle_vms
from detectors.orphan_disk import detect_orphan_disks
from detectors.storage_lifecycle import detect_missing_lifecycle
from detectors.unused_ip import detect_unused_ips

REPORT_DIR = Path(__file__).parent / "reports"

def main():
    print("=== GCP FinOps Cloud Optimizer ===")
    print(f"Project: {PROJECT_ID}")
    REPORT_DIR.mkdir(exist_ok=True)
    instances = collect_instances(PROJECT_ID)
    disks = collect_disks(PROJECT_ID)
    addresses = collect_addresses(PROJECT_ID)
    buckets = collect_buckets(PROJECT_ID)
    findings = []
    findings += detect_orphan_disks(disks)
    findings += detect_unused_ips(addresses)
    findings += detect_missing_lifecycle(buckets)
    findings += detect_idle_vms(PROJECT_ID, instances)
    report = {"project_id": PROJECT_ID, "generated_at": datetime.now(timezone.utc).isoformat(), "summary": {"instances_scanned": len(instances), "disks_scanned": len(disks), "addresses_scanned": len(addresses), "buckets_scanned": len(buckets), "findings": len(findings)}, "findings": findings}
    report_file = REPORT_DIR / "recommendations.json"
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("FINOPS_REPORT_START")
    print(json.dumps(report, indent=2))
    print("FINOPS_REPORT_END")
    for i, finding in enumerate(findings, 1):
        print(f"\nFinding #{i}: [{finding['severity']}] {finding['resource_name']}")
        print(f"Issue: {finding['issue']}")
        print(f"Recommendation: {finding['recommendation']}")
        tf = finding.get("terraform")
        if tf:
            print(f"Terraform action: {tf['recommended_action']}")
            print(f"Terraform file: {tf['file']}")
            print(f"Terraform module: {tf['module_name']}")
            print(f"Terraform address: {tf['terraform_address']}")
            print(f"Warning: {tf['warning']}")
            print("Human approval required: YES")
            print("Automatic deletion: NO")
    if ENABLE_AI:
        from ai.optimizer_agent import generate_ai_recommendations
        ai_result = generate_ai_recommendations(PROJECT_ID, findings)
        (REPORT_DIR / "ai-recommendations.md").write_text(ai_result, encoding="utf-8")
        print("\n=== AI Recommendations ===")
        print(ai_result)
    else:
        print("\nAI analysis disabled. Set ENABLE_AI=true after Vertex AI permissions/pricing are confirmed.")

if __name__ == "__main__":
    main()
