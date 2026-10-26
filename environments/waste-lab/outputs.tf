output "expected_findings" {
  description = "Expected FinOps waste findings remaining in the lab."

  value = [
    {
      resource_type = "compute_instance"
      name          = module.idle_vm.name
      waste_type    = "idle-vm"
    },
    {
      resource_type = "compute_address"
      name          = module.unused_ip.name
      waste_type    = "unused-ip"
    },
    {
      resource_type = "storage_bucket"
      name          = module.no_lifecycle_bucket.name
      waste_type    = "no-lifecycle"
    }
  ]
}