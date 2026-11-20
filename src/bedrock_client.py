"""
Talks to Amazon Bedrock: sends a prompt to the AI and returns its answer.

This is the only file that talks to the AI, so changing AI later only means changing this file.
"""

import boto3

from config.settings import AWS_REGION, BEDROCK_MODEL_ID


def ask_ai(prompt: str, max_tokens: int = 4000) -> str:
    """Send a prompt to the AI and return its answer as text.

    max_tokens is the longest answer we allow, which also limits the cost.
    """
    client = boto3.client("bedrock-runtime", region_name=AWS_REGION)

    response = client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": max_tokens},
    )

    # An answer can have several parts, so we keep only the text parts
    parts = response["output"]["message"]["content"]
    return "".join(part["text"] for part in parts if "text" in part)
