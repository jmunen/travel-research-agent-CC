"""Amazon Bedrock Claude integration for AI-powered travel summarization."""

import os
import json
import logging
import boto3

logger = logging.getLogger(__name__)

# Regions to try in order if throttled
FALLBACK_REGIONS = ["us-west-2", "us-east-1", "eu-west-1", "ap-northeast-1"]


class AISummarizer:
    """Generates travel briefs using Amazon Bedrock Claude with multi-region fallback."""

    def __init__(self):
        """Initialize the Bedrock runtime client using environment variables."""
        self.primary_region = os.getenv("AWS_REGION", "us-east-1")
        self.model_id = os.getenv(
            "BEDROCK_MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0"
        )
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        # Build ordered list of regions to try (primary first, then fallbacks)
        self.regions = [self.primary_region] + [
            r for r in FALLBACK_REGIONS if r != self.primary_region
        ]

        self.client = self._create_client(self.primary_region)
        logger.info(
            f"Bedrock client initialized (region={self.primary_region}, model={self.model_id})"
        )

    def _create_client(self, region: str):
        """Create a Bedrock runtime client for a specific region."""
        return boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
        )

    def summarize(self, prompt: str) -> str:
        """
        Generate a travel brief summary using Claude via Bedrock.
        Automatically retries in different regions if throttled.

        Args:
            prompt: The full prompt including research data and instructions.

        Returns:
            The generated travel brief as a Markdown string.

        Raises:
            RuntimeError: If the Bedrock API call fails in all regions.
        """
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 4096,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            }
        )

        last_error = None

        for region in self.regions:
            logger.info(f"Trying Bedrock model {self.model_id} in region {region}...")
            client = self._create_client(region)

            try:
                response = client.invoke_model(
                    modelId=self.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=body,
                )

                response_body = json.loads(response["body"].read())

                # Extract text from Claude's response format
                content = response_body.get("content", [])
                if content and len(content) > 0:
                    text = content[0].get("text", "")
                    logger.info(
                        f"Successfully generated summary in {region} ({len(text)} characters)"
                    )
                    return text

                logger.warning(f"Bedrock response from {region} contained no content")
                continue

            except client.exceptions.ThrottlingException as e:
                logger.warning(f"Throttled in {region}: {str(e)} - trying next region...")
                last_error = e
                continue
            except Exception as e:
                error_msg = f"Bedrock error in {region}: {str(e)}"
                logger.error(error_msg)
                last_error = e
                # For non-throttling errors, don't retry other regions
                if "ThrottlingException" not in str(e) and "Too many tokens" not in str(e):
                    raise RuntimeError(error_msg) from e
                continue

        # All regions exhausted
        error_msg = (
            f"All regions throttled. Daily token limit reached across all regions. "
            f"Please wait for the quota to reset (usually midnight UTC) or request a "
            f"quota increase in AWS Service Quotas. Last error: {str(last_error)}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
