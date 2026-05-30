"""Amazon Bedrock Claude integration for AI-powered travel summarization."""

import os
import json
import logging
import boto3

logger = logging.getLogger(__name__)

# Models to try in order (different models may have separate quotas)
FALLBACK_MODELS = [
    "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
    "us.amazon.nova-lite-v1:0",
    "us.amazon.nova-micro-v1:0",
]


class AISummarizer:
    """Generates travel briefs using Amazon Bedrock with model fallback."""

    def __init__(self):
        """Initialize the Bedrock runtime client using environment variables."""
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.model_id = os.getenv(
            "BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        )
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
        )

        # Build model list: configured model first, then fallbacks
        self.models = [self.model_id] + [
            m for m in FALLBACK_MODELS if m != self.model_id
        ]

        logger.info(
            f"Bedrock client initialized (region={self.region}, model={self.model_id})"
        )

    def summarize(self, prompt: str) -> str:
        """
        Generate a travel brief using the Converse API with model fallback.
        Tries multiple models if one is throttled.

        Args:
            prompt: The full prompt including research data and instructions.

        Returns:
            The generated travel brief as a Markdown string.

        Raises:
            RuntimeError: If all models fail.
        """
        last_error = None

        for model_id in self.models:
            logger.info(f"Trying model: {model_id} in {self.region}...")

            try:
                response = self.client.converse(
                    modelId=model_id,
                    messages=[
                        {
                            "role": "user",
                            "content": [{"text": prompt}],
                        }
                    ],
                    inferenceConfig={
                        "maxTokens": 4096,
                        "temperature": 0.7,
                    },
                )

                # Extract text from Converse API response
                output = response.get("output", {})
                message = output.get("message", {})
                content = message.get("content", [])

                if content and len(content) > 0:
                    text = content[0].get("text", "")
                    logger.info(
                        f"Successfully generated summary with {model_id} ({len(text)} characters)"
                    )
                    return text

                logger.warning(f"Model {model_id} returned no content")
                continue

            except self.client.exceptions.ThrottlingException as e:
                logger.warning(f"Throttled on {model_id}: {str(e)} - trying next model...")
                last_error = e
                continue
            except Exception as e:
                error_str = str(e)
                if "ThrottlingException" in error_str or "Too many tokens" in error_str:
                    logger.warning(f"Throttled on {model_id}: {error_str} - trying next model...")
                    last_error = e
                    continue
                elif "model identifier is invalid" in error_str:
                    logger.warning(f"Model {model_id} not available in {self.region} - trying next...")
                    last_error = e
                    continue
                else:
                    error_msg = f"Bedrock error with {model_id}: {error_str}"
                    logger.error(error_msg)
                    raise RuntimeError(error_msg) from e

        # All models exhausted
        error_msg = (
            f"All models throttled or unavailable. Daily token limit reached. "
            f"Please wait for the quota to reset (usually midnight UTC) or request a "
            f"quota increase in AWS Service Quotas → Amazon Bedrock. "
            f"Last error: {str(last_error)}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
