from datetime import datetime, timedelta, timezone
from google.cloud import monitoring_v3
from config import IDLE_CPU_THRESHOLD, IDLE_LOOKBACK_DAYS
from terraform_mapping import get_terraform_recommendation

def detect_idle_vms(project_id, instances):
    findings = []
    client = monitoring_v3.MetricServiceClient()
    end = datetime.now(timezone.utc)
    interval = monitoring_v3.TimeInterval({"end_time": end, "start_time": end - timedelta(days=IDLE_LOOKBACK_DAYS)})
    for instance in instances:
        if instance["status"] != "RUNNING":
            continue
        metric_filter = f'metric.type="compute.googleapis.com/instance/cpu/utilization" AND resource.labels.instance_id="{instance["id"]}"'
        series = client.list_time_series(request={"name": f"projects/{project_id}", "filter": metric_filter, "interval": interval, "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL})
        values = [point.value.double_value for ts in series for point in ts.points]
        if not values:
            continue
        avg = sum(values) / len(values)
        if avg >= IDLE_CPU_THRESHOLD:
            continue
        findings.append({"detector": "idle_vm", "resource_type": "compute_instance", "resource_name": instance["name"], "location": instance["zone"], "severity": "HIGH", "issue": "VM has low average CPU utilization.", "evidence": {"average_cpu": round(avg, 4), "threshold": IDLE_CPU_THRESHOLD, "lookback_days": IDLE_LOOKBACK_DAYS, "samples": len(values), "machine_type": instance["machine_type"]}, "recommendation": "Confirm the workload is unnecessary. Consider stop/rightsize first; if permanently unnecessary, review Terraform module removal.", "terraform": get_terraform_recommendation(instance.get("labels", {})), "approval_required": True})
    return findings
