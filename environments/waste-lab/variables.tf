variable "project_id" {
  description = "GCP project ID for the lab."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id must be 6-30 characters: lowercase letters, digits and hyphens, starting with a letter."
  }
}

variable "region" {
  description = "Region. Use us-west1, us-central1 or us-east1 to stay inside the always-free e2-micro."
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "Zone inside the region."
  type        = string
  default     = "us-central1-a"
}

variable "name_prefix" {
  description = "Prefix for resource names, so several copies of the lab can coexist. Include the trailing hyphen."
  type        = string
  default     = ""
}

variable "extra_labels" {
  description = "Extra labels merged into every resource."
  type        = map(string)
  default     = {}
}

variable "finops_agent_service_account_name" {
  description = "Service account ID for the FinOps Agent runtime."
  type        = string
  default     = "finops-agent"
}

variable "finops_enable_ai" {
  description = "Enable Vertex AI recommendations for the FinOps Agent."
  type        = bool
  default     = true
}

variable "finops_agent_region" {
  description = "Cloud Run region for the FinOps Agent."
  type        = string
  default     = "asia-south1"
}

variable "finops_agent_job_name" {
  description = "Cloud Run Job name for the FinOps Agent."
  type        = string
  default     = "finops-optimizer-agent"
}

variable "finops_gemini_model" {
  description = "Gemini model used by the FinOps Agent."
  type        = string
  default     = "gemini-3.5-flash-lite"
}

variable "finops_vertex_location" {
  description = "Vertex AI location for Gemini."
  type        = string
  default     = "global"
}

variable "finops_idle_cpu_threshold" {
  description = "Average CPU threshold below which a VM is considered potentially idle."
  type        = number
  default     = 0.05
}

variable "finops_idle_lookback_days" {
  description = "Cloud Monitoring lookback period for idle VM analysis."
  type        = number
  default     = 7
}

variable "github_deployer_service_account" {
  description = "GitHub Actions WIF service account email. Leave null to use github-terraform@PROJECT_ID.iam.gserviceaccount.com."
  type        = string
  default     = null
  nullable    = true
}
