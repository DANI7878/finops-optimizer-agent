locals {
  finops_required_apis = toset([
    "compute.googleapis.com",
    "monitoring.googleapis.com",
    "storage.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "aiplatform.googleapis.com",
  ])

  github_deployer_service_account = coalesce(var.github_deployer_service_account, "github-terraform@${var.project_id}.iam.gserviceaccount.com")

  finops_agent_roles = toset([
    "roles/compute.viewer",
    "roles/monitoring.viewer",
    "roles/storage.viewer",
  ])
}

resource "google_project_service" "finops_apis" {
  for_each = local.finops_required_apis
  project  = var.project_id
  service  = each.value
  disable_on_destroy = false
}

resource "google_service_account" "finops_agent" {
  project      = var.project_id
  account_id   = var.finops_agent_service_account_name
  display_name = "FinOps Cloud Optimizer Agent"
  description  = "Read-only runtime identity for the FinOps Cloud Optimizer Cloud Run Job."
  depends_on   = [google_project_service.finops_apis]
}

resource "google_project_iam_member" "finops_agent_roles" {
  for_each = local.finops_agent_roles
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.finops_agent.email}"
}

resource "google_project_iam_member" "finops_vertex_ai" {
  count   = var.finops_enable_ai ? 1 : 0
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.finops_agent.email}"
}

resource "google_service_account_iam_member" "github_can_use_finops_agent" {
  service_account_id = google_service_account.finops_agent.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${local.github_deployer_service_account}"
}
