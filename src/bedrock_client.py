"""
Talks to Amazon Bedrock: sends a prompt to the AI and returns its answer.

This is the only file that talks to the AI, so changing AI later only means changing this file.
Because every AI call passes through here, this is also the one place that logs them all
and applies the safety guardrail to them all.
"""

import time

import boto3

from config.settings import AWS_REGION, BEDROCK_GUARDRAIL_ID, BEDROCK_GUARDRAIL_VERSION, BEDROCK_MODEL_ID
from src.audit_log import log_event


class GuardrailBlockedError(Exception):
    """Raised when the Bedrock Guardrail blocks the question or the answer."""


def build_content(prompt: str, untrusted: str | None) -> list[dict]:
    """Split the prompt so the guardrail checks only the untrusted part (the papers), not our instructions.

    This is called "input tagging". Without it, the guardrail read our own instructions
    ("Use exactly these six headings...") as an attack, and blocked 17 of 27 real abstracts.
    Text inside "guardContent" is checked by the guardrail; normal "text" is not.
    The AI still receives everything, in the same order.
    """
    if not (BEDROCK_GUARDRAIL_ID and untrusted and untrusted in prompt):
        return [{"text": prompt}]

    before, after = prompt.split(untrusted, 1)  # The text before and after the papers
    content = []
    if before:
        content.append({"text": before})
    content.append({"guardContent": {"text": {"text": untrusted}}})
    if after:
        content.append({"text": after})
    return content


def guardrail_reasons(trace: dict) -> tuple[list[str], list[str]]:
    """Read the guardrail's report and return (what it blocked, what it masked)."""
    guardrail = trace.get("guardrail", {})
    assessments = list(guardrail.get("inputAssessment", {}).values())
    for output_list in guardrail.get("outputAssessments", {}).values():
        assessments.extend(output_list)

    blocked, masked = [], []
    for assessment in assessments:
        for item in assessment.get("contentPolicy", {}).get("filters", []):
            if item.get("action") == "BLOCKED":
                blocked.append(item["type"].lower().replace("_", " "))  # like "prompt attack"
        for item in assessment.get("topicPolicy", {}).get("topics", []):
            if item.get("action") == "BLOCKED":
                blocked.append(item["name"].lower())  # like "personal medical advice"
        for item in assessment.get("sensitiveInformationPolicy", {}).get("piiEntities", []):
            (blocked if item.get("action") == "BLOCKED" else masked).append(item["type"].lower())
    return blocked, masked


def ask_ai(prompt: str, max_tokens: int = 4000, task: str = "unknown", untrusted: str | None = None) -> str:
    """Send a prompt to the AI and return its answer as text.

    max_tokens is the longest answer we allow, which also limits the cost.
    task says what the call is for (like "summarize"), so the audit log can show it.
    untrusted is the part of the prompt that came from outside (paper text), for the guardrail to check.
    """
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    request = {
        "modelId": BEDROCK_MODEL_ID,
        "messages": [{"role": "user", "content": build_content(prompt, untrusted)}],
        "inferenceConfig": {"maxTokens": max_tokens},
    }
    # The guardrail is optional: it is only used if its ID is set in .env (a "feature flag")
    if BEDROCK_GUARDRAIL_ID:
        request["guardrailConfig"] = {
            "guardrailIdentifier": BEDROCK_GUARDRAIL_ID,
            "guardrailVersion": BEDROCK_GUARDRAIL_VERSION,
            "trace": "enabled",  # Ask AWS to explain what it blocked, for the audit log
        }

    started = time.perf_counter()  # A stopwatch, to measure how long the AI takes
    try:
        response = client.converse(**request)  # ** unpacks the dictionary into named arguments
    except Exception as error:
        # Write the failure in the log, then "raise" passes the error on to app.py as before
        log_event(
            "ai_error",
            task=task,
            model=BEDROCK_MODEL_ID,
            error=type(error).__name__,  # Only the error's type, like "ClientError"
            seconds=round(time.perf_counter() - started, 2),
        )
        raise

    # Bedrock tells us how many tokens were used. Tokens are what AWS charges for.
    usage = response.get("usage", {})
    log_event(
        "ai_call",
        task=task,
        model=BEDROCK_MODEL_ID,
        input_tokens=usage.get("inputTokens", 0),
        output_tokens=usage.get("outputTokens", 0),
        stop_reason=response.get("stopReason", ""),  # "max_tokens" means the answer was cut off
        guardrail="on" if BEDROCK_GUARDRAIL_ID else "off",
        seconds=round(time.perf_counter() - started, 2),
        prompt_characters=len(prompt),  # The size of the prompt, never the prompt itself
    )

    if response.get("stopReason") == "guardrail_intervened":
        blocked, masked = guardrail_reasons(response.get("trace", {}))
        if blocked:
            log_event("guardrail_blocked", task=task, reasons=blocked)
            raise GuardrailBlockedError(", ".join(blocked))
        if masked:
            # Personal details in the answer were replaced, like {EMAIL}. The rest of the answer is kept.
            log_event("guardrail_masked", task=task, kinds=masked)

    # An answer can have several parts, so we keep only the text parts
    parts = response["output"]["message"]["content"]
    return "".join(part["text"] for part in parts if "text" in part)
