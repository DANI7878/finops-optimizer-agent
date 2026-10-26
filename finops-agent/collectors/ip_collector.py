from google.cloud import compute_v1

def collect_addresses(project_id: str) -> list[dict]:
    client = compute_v1.AddressesClient()
    items = []
    request = compute_v1.AggregatedListAddressesRequest(project=project_id)
    for scope, scoped in client.aggregated_list(request=request):
        for address in scoped.addresses or []:
            items.append({"id": str(address.id), "name": address.name, "address": address.address, "status": address.status, "address_type": address.address_type, "scope": scope, "users": list(address.users or []), "labels": dict(address.labels or {})})
    return items
