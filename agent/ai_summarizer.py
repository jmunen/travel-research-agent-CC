"""Amazon Bedrock Claude integration for AI-powered travel summarization."""

import os
import json
import logging
import boto3

logger = logging.getLogger(__name__)


class AISummarizer:
    """Generates travel briefs using Amazon Bedrock Claude."""

    def __init__(self):
        """Initialize the Bedrock runtime client using environment variables."""
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.model_id = os.getenv(
            "BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"
        )

        try:
            self.client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            )
            logger.info(
                f"Bedrock client initialized (region={self.region}, model={self.model_id})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {str(e)}")
            raise

    def summarize(self, prompt: str) -> str:
        """
        Generate a travel brief summary using Claude via Bedrock.

        Args:
            prompt: The full prompt including research data and instructions.

        Returns:
            The generated travel brief as a Markdown string.

        Raises:
            RuntimeError: If the Bedrock API call fails.
        """
        logger.info(f"Calling Bedrock model: {self.model_id}")

        try:
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

            response = self.client.invoke_model(
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
                    f"Successfully generated summary ({len(text)} characters)"
                )
                return text

            logger.warning("Bedrock response contained no content")
            raise RuntimeError("Bedrock returned an empty response")

        except self.client.exceptions.ClientError as e:
            error_msg = f"Bedrock API error: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to generate summary: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e
