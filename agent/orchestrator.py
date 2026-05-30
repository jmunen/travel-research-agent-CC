"""Main agent orchestration logic - ties all components together."""

import logging
from models.schemas import ResearchRequest, ResearchResponse, TravelPreferences
from agent.apify_collector import ApifyCollector
from agent.ai_summarizer import AISummarizer
from agent.box_exporter import BoxExporter
from utils.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class TravelResearchOrchestrator:
    """
    Orchestrates the full travel research pipeline:
    1. Collect data from the web via Apify
    2. Build a prompt with the collected data
    3. Generate a travel brief via Bedrock Claude
    4. Upload the brief to Box
    5. Return the result
    """

    def __init__(self):
        """Initialize all component services."""
        self.collector = ApifyCollector()
        self.summarizer = AISummarizer()
        self.exporter = BoxExporter()
        self.prompt_builder = PromptBuilder()
        logger.info("TravelResearchOrchestrator initialized")

    async def run(self, request: ResearchRequest) -> ResearchResponse:
        """
        Execute the full research pipeline for a given destination.

        Args:
            request: The research request with destination and optional preferences.

        Returns:
            ResearchResponse with results or error information.
        """
        destination = request.destination
        preferences = request.preferences

        logger.info(f"Starting research for '{destination}'...")

        try:
            # Step 1: Collect travel data from the web
            logger.info("Step 1: Collecting travel data via Apify...")
            raw_data = self.collector.collect_travel_data(destination, preferences)

            if not raw_data:
                logger.warning(
                    "No data collected from Apify - will rely on AI knowledge"
                )

            logger.info(f"Collected {len(raw_data)} data points")

            # Step 2: Build the AI prompt
            logger.info("Step 2: Building AI prompt...")
            prompt = self.prompt_builder.build_summary_prompt(
                destination=destination,
                preferences=preferences,
                raw_data=raw_data,
            )

            # Step 3: Generate the travel brief via AI
            logger.info("Step 3: Generating travel brief via Bedrock Claude...")
            brief_content = self.summarizer.summarize(prompt)

            if not brief_content:
                raise RuntimeError("AI summarizer returned empty content")

            logger.info(
                f"Generated brief: {len(brief_content)} characters"
            )

            # Step 4: Upload to Box
            logger.info("Step 4: Uploading brief to Box...")
            upload_result = self.exporter.upload_brief(destination, brief_content)

            # Step 5: Build and return response
            logger.info("Step 5: Building response...")

            box_file_id = upload_result.get("file_id")
            box_file_name = upload_result.get("file_name")
            box_file_url = upload_result.get("shared_link_url")

            if upload_result.get("error"):
                message = (
                    f"Travel brief generated successfully for {destination}. "
                    f"Note: Box upload issue - {upload_result['error']}"
                )
            else:
                message = (
                    f"Travel brief generated and uploaded successfully for {destination}!"
                )

            # Preview is first 500 chars of the brief
            brief_preview = brief_content[:500]

            response = ResearchResponse(
                success=True,
                destination=destination,
                box_file_id=box_file_id,
                box_file_name=box_file_name,
                box_file_url=box_file_url,
                brief_preview=brief_preview,
                brief_full=brief_content,
                message=message,
            )

            logger.info(f"Research complete for '{destination}'")
            return response

        except Exception as e:
            error_msg = f"Research pipeline failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            return ResearchResponse(
                success=False,
                destination=destination,
                box_file_id=None,
                box_file_name=None,
                box_file_url=None,
                brief_preview="",
                message=error_msg,
            )
