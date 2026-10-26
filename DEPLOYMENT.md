# Deployment Guide

This guide describes the complete deployment flow for the GCP FinOps
Cloud Optimizer Lab.

The intended user experience after bootstrap is:

``` text
Update terraform.tfvars
        |
        v
Run Terraform Plan
        |
        v
Review + Apply
        |
        v
Run Deploy FinOps Agent
        |
        v
Use the Cloud Run Job
```

Normal agent updates do not require `gcloud run jobs deploy` from a
local terminal.

------------------------------------------------------------------------

## 1. Prerequisites

Install locally if you want to inspect/test the repository:

-   Git
-   Terraform 1.9.x
-   Google Cloud CLI
-   Python 3.11+ for local agent testing
-   Docker is optional

You also need:

-   A GCP project with billing enabled.
-   A GitHub repository containing this project.
-   Permission to configure IAM during the one-time bootstrap.

Example project used during development:

``` text
finops-lab-511007
```

Replace it with your own project.

------------------------------------------------------------------------

## 2. Bootstrap boundary

Two things must exist before the main GitHub Terraform workflow can
operate:

1.  A GCS bucket for Terraform remote state.
2.  GitHub-to-GCP Workload Identity Federation.

This is unavoidable because GitHub must authenticate to GCP and
Terraform must have a backend before the main Terraform stack can
provision anything.

Everything else in the FinOps Agent runtime is designed to be managed by
Terraform or GitHub Actions.

------------------------------------------------------------------------

## 3. Create the Terraform state bucket

Set:

``` bash
PROJECT_ID="YOUR_GCP_PROJECT_ID"
TF_STATE_BUCKET="${PROJECT_ID}-tfstate"
```

Select the project:

``` bash
gcloud config set project "$PROJECT_ID"
```

Create the bucket if it does not already exist:

``` bash
gcloud storage buckets create "gs://${TF_STATE_BUCKET}" \
  --project="$PROJECT_ID" \
  --location="us-central1" \
  --uniform-bucket-level-access
```

Enable versioning:

``` bash
gcloud storage buckets update "gs://${TF_STATE_BUCKET}" \
  --versioning
```

Keep this bucket outside the waste-lab Terraform stack so destroying the
lab does not destroy its own backend.

------------------------------------------------------------------------

## 4. Create GitHub Workload Identity Federation

The GitHub workflow needs a deployment service account.

Example:

``` bash
PROJECT_ID="YOUR_GCP_PROJECT_ID"
GITHUB_OWNER="YOUR_GITHUB_USER_OR_ORG"
GITHUB_REPO="finops-lab"

DEPLOY_SA_NAME="github-terraform"
POOL_ID="github-actions"
PROVIDER_ID="github"
```

Get the project number:

``` bash
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" \
  --format="value(projectNumber)")
```

Create the deployment service account:

``` bash
gcloud iam service-accounts create "$DEPLOY_SA_NAME" \
  --project="$PROJECT_ID" \
  --display-name="GitHub Terraform"
```

Set:

``` bash
DEPLOY_SA="${DEPLOY_SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
```

Enable the WIF-related APIs:

``` bash
gcloud services enable \
  iam.googleapis.com \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  cloudresourcemanager.googleapis.com \
  serviceusage.googleapis.com \
  --project="$PROJECT_ID"
```

Create the pool:

``` bash
gcloud iam workload-identity-pools create "$POOL_ID" \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions"
```

Create the GitHub provider:

``` bash
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="$POOL_ID" \
  --display-name="GitHub" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository=='${GITHUB_OWNER}/${GITHUB_REPO}'"
```

Create the repository principal:

``` bash
PRINCIPAL="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${GITHUB_OWNER}/${GITHUB_REPO}"
```

Allow that GitHub identity to impersonate the deployment service
account:

``` bash
gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_SA" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="$PRINCIPAL"
```

Build the provider resource name:

``` bash
GCP_WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"
```

------------------------------------------------------------------------

## 5. Bootstrap permissions for the GitHub deployment identity

The GitHub deployment service account is not the FinOps Agent runtime
identity.

The deployment identity needs enough permission to provision the lab and
deploy/update the Cloud Run Job. Use least privilege appropriate to your
organization.

For this lab, the deployment identity must be able to manage the
resource types present in the Terraform configuration, project
services/IAM used by `finops-agent.tf`, and Cloud Run deployment.

At minimum, review permissions for:

-   Compute resources.
-   Cloud Storage resources.
-   Project service enablement.
-   Project IAM bindings created by Terraform.
-   Service account creation/management.
-   Cloud Run Jobs.
-   Cloud Build / source deployment.
-   Artifact Registry.
-   Acting as the FinOps runtime service account.

Do not grant `Owner` merely to bypass permission errors.

For the Cloud Run deployment path, the deployment identity needs
permission to manage Cloud Run and to attach the runtime service
account. A common lab setup includes:

``` bash
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${DEPLOY_SA}" \
  --role="roles/run.admin"
```

The main Terraform configuration creates the `finops-agent` runtime
service account. After the first successful Terraform Apply, it also
grants the configured GitHub deployer permission to use that runtime
identity when that deployer is represented in the Terraform
configuration.

If your organization restricts IAM administration, have an administrator
grant the exact permissions required by your environment rather than
broad project roles.

------------------------------------------------------------------------

## 6. Configure GitHub repository values

Open:

``` text
GitHub repository
-> Settings
-> Secrets and variables
-> Actions
```

Create repository variables:

``` text
GCP_PROJECT_ID = YOUR_GCP_PROJECT_ID
TF_STATE_BUCKET = YOUR_STATE_BUCKET
```

Create repository secrets:

``` text
GCP_WIF_PROVIDER = projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github-actions/providers/github

GCP_SERVICE_ACCOUNT = github-terraform@YOUR_GCP_PROJECT_ID.iam.gserviceaccount.com
```

No service-account JSON key is required.

------------------------------------------------------------------------

## 7. Configure `terraform.tfvars`

From the repository:

``` bash
cd environments/waste-lab
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`.

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

Do not commit environment-specific secrets into tfvars.

------------------------------------------------------------------------

## 8. Validate locally

Optional but recommended:

``` bash
terraform fmt -recursive
```

Then:

``` bash
cd environments/waste-lab
terraform init -backend=false
terraform validate
cd ../..
```

Expected:

``` text
Success! The configuration is valid.
```

------------------------------------------------------------------------

## 9. Push the configuration

``` bash
git status
git add .
git commit -m "configure FinOps lab"
git push origin feature/v1
```

Use your desired branch if it differs from `feature/v1`.

------------------------------------------------------------------------

## 10. Run Terraform Plan

Open:

``` text
GitHub
-> Actions
-> Terraform Plan and Apply
-> Run workflow
```

Choose the branch containing the configuration.

Select:

``` text
action = plan
plan_run_id = <blank>
```

The workflow performs:

``` text
Format
-> Validate
-> TFLint
-> Checkov
-> GCP WIF authentication
-> Terraform Init
-> Terraform Plan
-> Upload exact binary tfplan
```

Review `Show Terraform Plan`.

Do not Apply until the plan is correct.

------------------------------------------------------------------------

## 11. Apply the exact reviewed plan

Take the successful Plan workflow Run ID.

Run the same workflow again:

``` text
action = apply
plan_run_id = <PLAN_RUN_ID>
```

The Apply job:

1.  Downloads the exact reviewed `tfplan`.
2.  Validates plan metadata.
3.  Checks repository, project, backend and commit information.
4.  Checks out the exact commit used for Plan.
5.  Initializes the same backend.
6.  Shows the reviewed plan again.
7.  Executes:

``` bash
terraform apply -auto-approve tfplan
```

It does not create another plan.

------------------------------------------------------------------------

## 12. What Terraform provisions for the agent

The main Terraform stack configures the FinOps runtime prerequisites.

This includes:

-   Required GCP APIs.
-   `finops-agent` service account.
-   Compute Viewer.
-   Monitoring Viewer.
-   Storage Viewer.
-   Vertex AI User when AI is enabled.
-   Permission required for the configured GitHub deployment identity to
    attach the runtime service account.
-   Outputs consumed by the agent deployment workflow.

The runtime agent remains read-only for infrastructure discovery.

------------------------------------------------------------------------

## 13. Deploy the FinOps Agent

After Terraform Apply succeeds, open:

``` text
GitHub
-> Actions
-> Deploy FinOps Agent
-> Run workflow
```

Choose the same branch.

Set:

``` text
execute_after_deploy = true
```

The workflow:

1.  Authenticates using GitHub WIF.
2.  Initializes the Terraform backend.
3.  Reads these values from Terraform outputs:
    -   Agent runtime service account.
    -   Cloud Run Job name.
    -   Cloud Run region.
    -   AI enabled flag.
    -   Gemini model.
4.  Builds the container from `finops-agent/`.
5.  Creates or updates the Cloud Run Job.
6.  Optionally executes the job.

After this point, agent code changes do not require a local
`gcloud run jobs deploy`.

Push the new code and rerun `Deploy FinOps Agent`.

------------------------------------------------------------------------

## 14. Run the FinOps Agent

The deployment workflow can execute the agent immediately.

For later runs, you can execute the Cloud Run Job from the GCP Cloud Run
Jobs UI, or extend the GitHub workflow with an execute-only action if
desired.

The agent performs:

``` text
Collect live Compute resources
        |
Collect persistent disks
        |
Collect reserved IPs
        |
Collect Cloud Storage metadata
        |
Read Cloud Monitoring CPU metrics
        |
Run deterministic detectors
        |
Map findings to Terraform
        |
Generate deterministic report
        |
Optional Vertex AI explanation
```

------------------------------------------------------------------------

## 15. Expected findings

Typical lab output includes:

``` text
orphan-disk-01
  -> DELETE_CANDIDATE
  -> module.orphan_disk

unused-ip-01
  -> DELETE_CANDIDATE
  -> module.unused_ip

lab-data bucket
  -> CONFIGURE
  -> module.no_lifecycle_bucket

idle-vm-01
  -> INVESTIGATE
  -> module.idle_vm
```

The agent must not automatically delete resources.

------------------------------------------------------------------------

## 16. Human-approved remediation

Example: orphan disk.

The report identifies:

``` text
Terraform file:
environments/waste-lab/main.tf

Terraform module:
orphan_disk

Action:
DELETE_CANDIDATE
```

A human verifies the disk and associated snapshot are no longer
required.

Then remove the `orphan_disk` module from Terraform.

Also remove or update any Terraform outputs that still reference that
module. Otherwise Terraform validation will fail with
`Reference to undeclared module`.

Example:

``` text
module.orphan_disk.name
module.orphan_disk.snapshot_name
```

must not remain in `outputs.tf` after the module is removed.

Commit the remediation and run the normal Plan workflow.

------------------------------------------------------------------------

## 17. Review the remediation Plan

Terraform may show:

``` text
0 to add
0 to change
2 to destroy
```

For the orphan disk module this can include:

-   Persistent disk.
-   Managed snapshot.

This is why the agent only recommends deletion and never performs it.

If the Terraform Plan is correct, run Apply with that exact Plan Run ID.

------------------------------------------------------------------------

## 18. Rescan

After remediation, run the FinOps Agent again.

The removed resource should no longer appear in the findings.

This demonstrates the complete loop:

``` text
Detect
-> Recommend
-> Human approve
-> Modify Terraform
-> Plan
-> Human review
-> Apply exact plan
-> Rescan
-> Verify
```

------------------------------------------------------------------------

## 19. Agent code updates

When changing files under:

``` text
finops-agent/
```

commit and push:

``` bash
git add finops-agent/
git commit -m "update FinOps Agent"
git push origin feature/v1
```

Then run:

``` text
GitHub
-> Actions
-> Deploy FinOps Agent
```

The workflow rebuilds and updates the Cloud Run Job.

No local Cloud Run deployment command is required.

------------------------------------------------------------------------

## 20. Destroy the lab

Use:

``` text
GitHub
-> Actions
-> Terraform Destroy
```

First:

``` text
action = destroy-plan
```

Review the exact destroy plan.

Then rerun:

``` text
action = destroy
plan_run_id = <DESTROY_PLAN_RUN_ID>
confirmation = DESTROY
```

The destroy workflow applies the exact reviewed binary destroy plan.

Keep the remote Terraform state bucket and WIF bootstrap outside the lab
unless you intentionally want to remove the entire deployment
foundation.

------------------------------------------------------------------------

## 21. Troubleshooting

### `storage.buckets.get` denied

Confirm the runtime service account has:

``` text
roles/storage.viewer
```

The storage collector is designed to continue scanning if an individual
bucket cannot be inspected.

### Vertex AI model returns 404

Verify:

-   Vertex AI API is enabled.
-   Runtime service account has `roles/aiplatform.user`.
-   The configured Gemini model exists and is available in the
    configured location.
-   The Cloud Run Job environment contains the expected model/location.

Model availability changes over time. Update `finops_gemini_model` in
Terraform configuration when migrating models.

The deterministic report remains usable if AI analysis fails.

### `Reference to undeclared module`

A Terraform module was removed but `outputs.tf` or another file still
references it.

Remove/update those references and rerun validation.

### Cloud Run deployment fails with IAM error

The GitHub deployment identity is separate from the FinOps runtime
identity.

The deployment identity needs Cloud Run/build permissions and permission
to attach the runtime service account. Do not solve this by granting the
runtime agent Admin permissions.

### Plan artifact errors

Always create a new Plan after changing Terraform or workflow behavior.
Do not reuse an old Plan Run ID after changing the configuration.

------------------------------------------------------------------------

## 22. Cost controls

This project can create billable resources.

Recommended controls:

-   Keep GCP billing enabled only where intended.
-   Configure budget alerts.
-   Keep VM/disk sizes small.
-   Run the agent on demand while developing.
-   Verify current Vertex AI pricing before enabling frequent AI calls.
-   Destroy the lab when testing is complete.

Budget alerts notify; they do not necessarily stop spending
automatically.

------------------------------------------------------------------------

## 23. Day-to-day workflow

After bootstrap, normal usage is:

``` text
Infrastructure change
    -> edit tfvars/Terraform
    -> Terraform Plan
    -> review
    -> Apply exact plan

Agent code change
    -> edit finops-agent/
    -> push
    -> Deploy FinOps Agent workflow

FinOps remediation
    -> review agent report
    -> approve recommendation
    -> modify Terraform
    -> Plan
    -> review
    -> Apply exact plan
    -> rescan

End of lab
    -> Destroy Plan
    -> review
    -> Destroy
```

This keeps Terraform as the infrastructure source of truth, GitHub
Actions as the controlled execution layer, and the FinOps Agent as a
read-only detection and recommendation system.
