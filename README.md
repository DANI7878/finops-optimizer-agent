# GCP FinOps Cloud Optimizer Lab

A reusable GCP FinOps lab that combines Terraform, GitHub Actions, Cloud
Run Jobs, deterministic waste detection, Terraform-aware remediation
recommendations, and optional Vertex AI / Gemini analysis.

The project deliberately deploys several waste scenarios, detects them
from live GCP state, maps findings back to the Terraform source that
owns them, and requires a human to approve every infrastructure change.

## Architecture

``` text
GitHub
  |
  +-- terraform.yml
  |      Plan -> Review -> Apply exact reviewed plan
  |
  +-- finops-agent.yml
  |      Build -> Deploy/update Cloud Run Job -> Optional execution
  |
  +-- terraform-destroy.yml
         Destroy plan -> Review -> Apply exact destroy plan

                         |
                         v

                       GCP
                         |
             +-----------+-----------+
             |                       |
        Waste Lab                Cloud Run Job
             |                   FinOps Agent
             |                       |
             +----------+------------+
                        |
                        v
                 Live GCP inventory
                        |
             +----------+----------+
             |          |          |
          Compute      Storage   Monitoring
             |          |          |
             +----------+----------+
                        |
                        v
              Deterministic detectors
                        |
                        v
                 Terraform mapping
                        |
                        v
              Optimization findings
                        |
             +----------+-----------+
             |                      |
       CONFIGURE /              DELETE_CANDIDATE
       INVESTIGATE                    |
             |                        |
             +-----------+------------+
                         |
                         v
                    Human review
                         |
                         v
                 Terraform code change
                         |
                         v
              Plan -> Review -> Apply
```

## What the lab deploys

The `environments/waste-lab` root module composes reusable Terraform
modules to create controlled FinOps scenarios:

-   An idle Compute Engine VM.
-   An unattached persistent disk and optional snapshot.
-   An unused reserved static IP.
-   A versioned Cloud Storage bucket without lifecycle cleanup.
-   A healthy control bucket with lifecycle rules.
-   A dedicated Cloud Storage access-log bucket.
-   The FinOps Agent runtime service account.
-   Required read-only IAM for the agent.
-   Optional Vertex AI access when AI analysis is enabled.
-   Required GCP APIs used by the lab and agent.

The Terraform state bucket and GitHub-to-GCP Workload Identity
Federation are bootstrap prerequisites and are intentionally outside the
main stack.

## FinOps Agent

The agent lives under `finops-agent/`.

``` text
finops-agent/
├── ai/
│   └── optimizer_agent.py
├── collectors/
│   ├── compute_collector.py
│   ├── disk_collector.py
│   ├── ip_collector.py
│   └── storage_collector.py
├── detectors/
│   ├── idle_vm.py
│   ├── orphan_disk.py
│   ├── unused_ip.py
│   └── storage_lifecycle.py
├── reports/
├── terraform_mapping.py
├── config.py
├── main.py
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

### Detection model

The agent does not ask an LLM to discover infrastructure facts. It
queries GCP directly and uses deterministic rules.

Examples:

  -----------------------------------------------------------------------
  Finding                 Detection               Default action
  ----------------------- ----------------------- -----------------------
  Orphan disk             Persistent disk has no  `DELETE_CANDIDATE`
                          attached users          

  Unused static IP        Reserved address has no `DELETE_CANDIDATE`
                          users                   

  Idle VM                 Average CPU below       `INVESTIGATE`
                          configured threshold    

  Missing bucket          Lab bucket has no       `CONFIGURE`
  lifecycle               lifecycle rules         
  -----------------------------------------------------------------------

### Terraform-aware remediation

Lab resources use labels such as `waste_type`. `terraform_mapping.py`
converts those labels into known Terraform ownership information.

A finding can therefore include:

``` text
Resource: orphan-disk-01
Action: DELETE_CANDIDATE
Terraform module: orphan_disk
Terraform address: module.orphan_disk.google_compute_disk.this
Terraform file: environments/waste-lab/main.tf
Human approval required: YES
Automatic deletion: NO
```

The agent never runs `terraform destroy`, `terraform state rm`, or
direct `gcloud ... delete` commands.

## AI analysis

Vertex AI / Gemini is optional.

The deterministic report remains authoritative even if AI is
unavailable. Gemini is used only to explain, prioritize, and
contextualize existing findings.

AI recommendations must not invent:

-   Resource state.
-   CPU utilization.
-   Terraform addresses.
-   Terraform modules.
-   Costs or savings that were not calculated by the application.

If Vertex AI fails, the job continues with the deterministic report.

## Repository structure

``` text
finops-lab/
├── .github/
│   └── workflows/
│       ├── terraform.yml
│       ├── terraform-destroy.yml
│       └── finops-agent.yml
├── environments/
│   └── waste-lab/
│       ├── backend.tf.example
│       ├── finops-agent.tf
│       ├── main.tf
│       ├── outputs.tf
│       ├── providers.tf
│       ├── terraform.tfvars.example
│       ├── variables.tf
│       └── versions.tf
├── finops-agent/
├── modules/
│   ├── compute-vm/
│   ├── persistent-disk/
│   ├── static-ip/
│   └── storage-bucket/
├── DEPLOYMENT.md
└── README.md
```

## Configuration

Copy:

``` bash
cd environments/waste-lab
cp terraform.tfvars.example terraform.tfvars
```

Then update the environment values.

Example:

``` hcl
project_id  = "YOUR_GCP_PROJECT_ID"
region      = "us-central1"
zone        = "us-central1-a"
name_prefix = ""

extra_labels = {
  owner = "YOUR_NAME"
}

finops_agent_service_account_name = "finops-agent"
finops_agent_region               = "asia-south1"
finops_agent_job_name             = "finops-optimizer-agent"

finops_enable_ai       = true
finops_gemini_model    = "gemini-3.5-flash-lite"
finops_vertex_location = "global"

finops_idle_cpu_threshold = 0.05
finops_idle_lookback_days = 7
```

Most users only need to change the project, region/zone, naming, and
optional FinOps settings.

## GitHub repository configuration

The workflows expect these bootstrap values.

### Repository variables

``` text
GCP_PROJECT_ID
TF_STATE_BUCKET
```

### Repository secrets

``` text
GCP_WIF_PROVIDER
GCP_SERVICE_ACCOUNT
```

`GCP_SERVICE_ACCOUNT` is the GitHub deployment identity used through
Workload Identity Federation. It is separate from the read-only
`finops-agent` runtime service account created by Terraform.

## Workflows

### `terraform.yml`

Manual workflow supporting:

``` text
action = plan
```

and:

``` text
action = apply
plan_run_id = <reviewed plan run ID>
```

Apply downloads and applies the exact binary `tfplan` produced by the
reviewed Plan run.

### `finops-agent.yml`

Reads the FinOps runtime configuration from Terraform outputs, builds
the container from `finops-agent/`, deploys or updates the Cloud Run
Job, and can optionally execute it immediately.

### `terraform-destroy.yml`

Creates an exact Terraform destroy plan, allows manual review, and
applies only the reviewed binary destroy plan.

## Security model

The FinOps runtime identity is intentionally read-only.

Expected runtime roles include:

``` text
roles/compute.viewer
roles/monitoring.viewer
roles/storage.viewer
```

When AI is enabled:

``` text
roles/aiplatform.user
```

The agent is not granted Compute Admin, Storage Admin, Editor, or Owner.

The GitHub deployment identity requires separate deployment permissions
because it creates infrastructure and updates Cloud Run. Follow
`DEPLOYMENT.md` for bootstrap details.

## Typical operating flow

``` text
1. Update terraform.tfvars
2. Run Terraform Plan workflow
3. Review plan
4. Apply exact reviewed plan
5. Run Deploy FinOps Agent workflow
6. Agent scans live GCP resources
7. Review FinOps findings
8. Human approves a remediation
9. Modify Terraform source
10. Run Terraform Plan again
11. Review actual impact
12. Apply exact reviewed plan
13. Run agent again
14. Verify the finding disappeared
```

## Example remediation

If the agent reports:

``` text
orphan-disk-01
DELETE_CANDIDATE
module.orphan_disk
```

a human reviews `environments/waste-lab/main.tf`.

If deletion is approved, remove the `orphan_disk` module and update any
outputs that still reference it. Run the normal Terraform Plan workflow.

Terraform may show both the disk and snapshot being destroyed. Review
that impact before Apply.

Do not directly delete the disk with `gcloud`, because Terraform is the
source of truth.

## Cost controls

This repository is intended for a small lab, but GCP resources can still
incur charges.

-   Keep billing and budget alerts enabled.
-   Destroy lab resources when testing is complete.
-   Keep the agent Cloud Run Job small.
-   Run the agent on demand or at a modest schedule.
-   Verify current Vertex AI model pricing before enabling repeated AI
    inference.
-   Budget alerts do not guarantee that spending automatically stops.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for the complete first-time
deployment, workflow usage, remediation, redeployment, troubleshooting,
and destroy procedure.
