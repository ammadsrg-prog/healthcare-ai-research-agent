"""
Creates the app's Amazon Bedrock Guardrail. Run it once with:
    python scripts/create_guardrail.py

A guardrail is AWS's safety filter. It checks both the text sent to the AI and the AI's answer.
This script is kept in the project so anyone can rebuild the same guardrail in their own AWS
account: the safety settings are written as code, not clicked by hand in the console.
This is called "infrastructure as code".

It prints the guardrail's ID and version. Put them in your .env file as
BEDROCK_GUARDRAIL_ID and BEDROCK_GUARDRAIL_VERSION.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # So "config" can be imported from this folder

import boto3

from config.settings import AWS_REGION

GUARDRAIL_NAME = "healthcare-research-guardrail"

# Content filters. The strength says how sure the filter must be before it blocks:
# LOW blocks only very clear cases, HIGH blocks even mild ones.
# Medical research often discusses violence (injuries, abuse), sexual health and misconduct (drug misuse),
# so those use LOW: real research must not be blocked. Hate and insults are never needed, so MEDIUM.
# PROMPT_ATTACK is AWS's own AI-based injection detector. It only checks the input (output must be NONE).
CONTENT_FILTERS = [
    {"type": "HATE", "inputStrength": "MEDIUM", "outputStrength": "MEDIUM"},
    {"type": "INSULTS", "inputStrength": "MEDIUM", "outputStrength": "MEDIUM"},
    {"type": "SEXUAL", "inputStrength": "LOW", "outputStrength": "LOW"},
    {"type": "VIOLENCE", "inputStrength": "LOW", "outputStrength": "LOW"},
    {"type": "MISCONDUCT", "inputStrength": "LOW", "outputStrength": "LOW"},
    {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"},
]

# A denied topic: the AI must never tell one person what treatment to take.
# Summarizing what a study found is fine; personal medical advice is not.
DENIED_TOPICS = [
    {
        "name": "Personal medical advice",
        "definition": (
            "Telling a specific person which treatment, medicine or dose they themselves should take, "
            "or diagnosing a specific person's own symptoms or condition."
        ),
        "examples": [
            "You should start taking metformin for your diabetes.",
            "Based on your symptoms, you have pneumonia.",
            "Stop taking your blood pressure tablets.",
        ],
        "type": "DENY",
    }
]

# Personal details are masked in the AI's answers, as a last check after src/pii.py.
# Only the output is checked: the input is public research, and our own PII check runs before searching.
PII_ENTITIES = [
    {"type": kind, "action": "ANONYMIZE", "inputEnabled": False, "outputEnabled": True, "outputAction": "ANONYMIZE"}
    for kind in ["EMAIL", "PHONE", "US_SOCIAL_SECURITY_NUMBER", "UK_NATIONAL_HEALTH_SERVICE_NUMBER"]
]


def main() -> None:
    bedrock = boto3.client("bedrock", region_name=AWS_REGION)

    guardrail = bedrock.create_guardrail(
        name=GUARDRAIL_NAME,
        description="Safety filters for the Healthcare AI Research Agent.",
        contentPolicyConfig={"filtersConfig": CONTENT_FILTERS},
        topicPolicyConfig={"topicsConfig": DENIED_TOPICS},
        sensitiveInformationPolicyConfig={"piiEntitiesConfig": PII_ENTITIES},
        # What the user sees when something is blocked
        blockedInputMessaging="This text was blocked by the app's safety guardrail before reaching the AI.",
        blockedOutputsMessaging="The AI's answer was blocked by the app's safety guardrail.",
    )

    # A version is a frozen copy. The app uses a version, so later edits can't change it by surprise.
    version = bedrock.create_guardrail_version(guardrailIdentifier=guardrail["guardrailId"])

    print("BEDROCK_GUARDRAIL_ID=" + guardrail["guardrailId"])
    print("BEDROCK_GUARDRAIL_VERSION=" + version["version"])


if __name__ == "__main__":
    main()
