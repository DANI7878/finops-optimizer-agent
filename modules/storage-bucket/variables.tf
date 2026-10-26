variable "name" {
  description = "Bucket name. Globally unique, 3 to 63 characters."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]$", var.name))
    error_message = "name must be 3-63 characters of lowercase letters, digits, dots, underscores or hyphens, starting and ending with a letter or digit."
  }
}

variable "location" {
  description = "Bucket location, for example US-CENTRAL1."
  type        = string
}

variable "storage_class" {
  description = "Default storage class."
  type        = string
  default     = "STANDARD"

  validation {
    condition     = contains(["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"], var.storage_class)
    error_message = "storage_class must be one of STANDARD, NEARLINE, COLDLINE, ARCHIVE."
  }
}

variable "labels" {
  description = "Labels applied to the bucket."
  type        = map(string)
  default     = {}
}

variable "force_destroy" {
  description = "Allow Terraform to delete the bucket even when it contains objects. Keep false outside labs."
  type        = bool
  default     = false
}

variable "versioning_enabled" {
  description = "Enable object versioning."
  type        = bool
  default     = true
}

variable "lifecycle_rules" {
  description = <<-EOT
    Lifecycle rules. Example:
    [{
      action    = { type = "SetStorageClass", storage_class = "NEARLINE" }
      condition = { age = 30 }
    },
    {
      action    = { type = "Delete" }
      condition = { age = 365 }
    }]
  EOT
  type = list(object({
    action = object({
      type          = string
      storage_class = optional(string)
    })
    condition = object({
      age                = optional(number)
      num_newer_versions = optional(number)
      with_state         = optional(string)
      matches_prefix     = optional(list(string))
    })
  }))
  default = []

  validation {
    condition = alltrue([
      for rule in var.lifecycle_rules :
      contains(["Delete", "SetStorageClass", "AbortIncompleteMultipartUpload"], rule.action.type)
    ])
    error_message = "Each lifecycle rule action.type must be Delete, SetStorageClass or AbortIncompleteMultipartUpload."
  }
}

variable "logging_bucket" {
  description = "Name of the GCS bucket used to store access logs."
  type        = string
  default     = null
}

variable "log_object_prefix" {
  description = "Prefix used for access log objects."
  type        = string
  default     = "access-logs"
}
