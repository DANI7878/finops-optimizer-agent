resource "google_storage_bucket" "this" {
  name          = var.name
  location      = var.location
  storage_class = var.storage_class
  labels        = var.labels
  force_destroy = var.force_destroy

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = var.versioning_enabled
  }

  dynamic "logging" {
    for_each = var.logging_bucket != null ? [1] : []
    content {
      log_bucket        = var.logging_bucket
      log_object_prefix = var.log_object_prefix
    }
  }

  dynamic "lifecycle_rule" {
    for_each = var.lifecycle_rules
    content {
      action {
        type          = lifecycle_rule.value.action.type
        storage_class = lifecycle_rule.value.action.storage_class
      }
      condition {
        age                = lifecycle_rule.value.condition.age
        num_newer_versions = lifecycle_rule.value.condition.num_newer_versions
        with_state         = lifecycle_rule.value.condition.with_state
        matches_prefix     = lifecycle_rule.value.condition.matches_prefix
      }
    }
  }
}
