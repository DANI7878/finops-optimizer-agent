import json
from google import genai
from config import GEMINI_MODEL, VERTEX_LOCATION

SYSTEM_INSTRUCTION = """You are a GCP FinOps optimization assistant. Analyze only supplied findings. Never invent costs, savings, utilization, Terraform addresses, modules, or infrastructure state. Classify actions as KEEP, INVESTIGATE, STOP, RIGHTSIZE, CONFIGURE, or DELETE_CANDIDATE. Never execute changes. Never recommend terraform state rm or direct gcloud deletion for Terraform-managed resources. Use supplied Terraform mapping only. Every destructive recommendation requires explicit human approval and a reviewed Terraform plan."""

def generate_ai_recommendations(project_id, findings):
    if not findings:
        return "No optimization findings were detected."
    client = genai.Client(vertexai=True, project=project_id, location=VERTEX_LOCATION)
    prompt = f"""GCP Project: {project_id}\nFindings:\n{json.dumps(findings, indent=2)}\nFor each finding provide resource, problem, evidence, action classification, whether Terraform deletion should be considered, supplied Terraform module/file/address, collateral risk, and human verification required. Do not invent monetary savings."""
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config={"system_instruction": SYSTEM_INSTRUCTION, "temperature": 0.2})
    return response.text or "No AI recommendations returned."
