from google.cloud import compute_v1

def collect_instances(project_id: str) -> list[dict]:
    client = compute_v1.InstancesClient()
    items = []
    request = compute_v1.AggregatedListInstancesRequest(project=project_id)
    for zone, scoped in client.aggregated_list(request=request):
        for instance in scoped.instances or []:
            items.append({
                "id": str(instance.id), "name": instance.name,
                "zone": zone.split("/")[-1], "status": instance.status,
                "machine_type": instance.machine_type.split("/")[-1],
                "labels": dict(instance.labels or {}),
            })
    return items
