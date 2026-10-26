# finops-lab

Reusable Terraform modules plus a "waste lab" environment that deliberately creates cloud waste on GCP. The lab gives the cost optimizer a ground truth to be measured against.

## Layout

```
modules/                    reusable building blocks (no provider config, no hard-coded values)
  compute-vm/               VM with shielded VM, OS Login, optional external IP and resource policies
  persistent-disk/          disk plus optional snapshot
  static-ip/                reserved external IP
  storage-bucket/           bucket with secure defaults and configurable lifecycle rules
environments/
  waste-lab/                root module: pins the provider, composes the modules, exports ground truth
```

Modules never configure providers or pin exact versions. The environment (the root module) does that.

## Use the lab

```bash
cd environments/waste-lab
cp terraform.tfvars.example terraform.tfvars   # set project_id
terraform init
terraform fmt -recursive ../..
terraform validate
terraform plan -out=tfplan                      # expect: Plan: 6 to add
terraform apply tfplan
terraform output expected_findings              # the ground truth for the detectors
```

Tear it down when you are done testing:

```bash
terraform destroy
```

## Use a module from another repo

Tag a release, then reference it by Git ref so consumers control when they upgrade:

```hcl
module "vm" {
  source = "git::https://github.com/<you>/finops-lab.git//modules/compute-vm?ref=v0.1.0"

  name = "my-vm"
  zone = "us-central1-a"
}
```

## Conventions

- Resource inside a module is named `this`.
- Every module accepts `labels`. Cost allocation depends on them.
- Inputs are validated, so mistakes fail at plan time with a readable message.
- Commit `.terraform.lock.hcl` to pin provider versions.

## FinOps Agent automation

The waste-lab Terraform now enables the required GCP APIs, creates the `finops-agent` runtime service account, and grants its read-only Compute, Monitoring, Storage and optional Vertex AI roles. The `Deploy FinOps Agent` workflow reads runtime configuration from Terraform outputs and deploys/updates the Cloud Run Job from `finops-agent/`.

For a new environment, copy `environments/waste-lab/terraform.tfvars.example` to `terraform.tfvars` and update the project/region values. GitHub-to-GCP Workload Identity Federation and the remote-state bucket are bootstrap prerequisites because GitHub must authenticate before it can run Terraform; the repository's existing GitHub secrets/variables provide those bootstrap values.
