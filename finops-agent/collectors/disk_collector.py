from google.cloud import compute_v1

def collect_disks(project_id: str) -> list[dict]:
    client = compute_v1.DisksClient()
    items = []
    request = compute_v1.AggregatedListDisksRequest(project=project_id)
    for zone, scoped in client.aggregated_list(request=request):
        for disk in scoped.disks or []:
            items.append({"id": str(disk.id), "name": disk.name, "zone": zone.split("/")[-1], "size_gb": disk.size_gb, "type": disk.type.split("/")[-1], "status": disk.status, "users": list(disk.users or []), "labels": dict(disk.labels or {})})
    return items
