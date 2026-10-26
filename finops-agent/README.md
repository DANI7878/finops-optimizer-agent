# GCP FinOps Cloud Optimizer

Read-only FinOps analysis for the waste-lab. It detects idle VMs, unattached disks, unused static IPs, and buckets without lifecycle rules, then maps findings back to Terraform. Deletion is recommendation-only: a human changes Terraform and uses the existing reviewed Plan/Apply workflow.

## Local
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
gcloud auth application-default login
python main.py
```

## Cloud Run Job
Deploy with `ENABLE_AI=false` first. Attach the `finops-agent` service account with Compute Viewer, Monitoring Viewer, and Storage Viewer. Enable Vertex AI and `roles/aiplatform.user` only when AI analysis is enabled.
