"""Box file storage integration for uploading travel briefs."""

import os
import re
import logging
from io import BytesIO
from datetime import datetime
from boxsdk import OAuth2, Client
from boxsdk.exception import BoxAPIException

logger = logging.getLogger(__name__)


class BoxExporter:
    """Uploads travel briefs to Box cloud storage."""

    def __init__(self):
        """Initialize Box client using developer token from environment."""
        self.access_token = os.getenv("BOX_ACCESS_TOKEN")
        self.folder_id = os.getenv("BOX_FOLDER_ID", "0")

        if not self.access_token:
            logger.warning("BOX_ACCESS_TOKEN not set - file upload will fail")
            self.client = None
            return

        try:
            auth = OAuth2(
                client_id=os.getenv("BOX_CLIENT_ID", ""),
                client_secret=os.getenv("BOX_CLIENT_SECRET", ""),
                access_token=self.access_token,
            )
            self.client = Client(auth)
            logger.info("Box client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Box client: {str(e)}")
            self.client = None

    def upload_brief(self, destination: str, content: str) -> dict:
        """
        Upload a travel brief to Box as a Markdown file.

        Args:
            destination: The travel destination (used in filename).
            content: The Markdown content of the travel brief.

        Returns:
            Dict with file_id, file_name, and shared_link_url.
            Returns dict with error info on failure.
        """
        if not self.client:
            logger.error("Box client not initialized - cannot upload")
            return {
                "file_id": None,
                "file_name": None,
                "shared_link_url": None,
                "error": "Box client not initialized",
            }

        # Generate filename
        destination_slug = self._slugify(destination)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"travel_brief_{destination_slug}_{timestamp}.md"

        logger.info(f"Uploading '{file_name}' to Box folder {self.folder_id}")

        try:
            # Prepare file content as a stream
            file_content = content.encode("utf-8")
            file_stream = BytesIO(file_content)

            # Upload to Box
            folder = self.client.folder(folder_id=self.folder_id)
            uploaded_file = folder.upload_stream(file_stream, file_name)

            logger.info(f"File uploaded successfully: {uploaded_file.id}")

            # Create a shared link
            shared_link_url = None
            try:
                shared_link = uploaded_file.get_shared_link(access="open")
                shared_link_url = shared_link
                logger.info(f"Shared link created: {shared_link_url}")
            except BoxAPIException as e:
                logger.warning(f"Could not create shared link: {str(e)}")

            return {
                "file_id": uploaded_file.id,
                "file_name": file_name,
                "shared_link_url": shared_link_url,
            }

        except BoxAPIException as e:
            error_msg = f"Box API error: {str(e)}"
            logger.error(error_msg)
            return {
                "file_id": None,
                "file_name": file_name,
                "shared_link_url": None,
                "error": error_msg,
            }
        except Exception as e:
            error_msg = f"Failed to upload to Box: {str(e)}"
            logger.error(error_msg)
            return {
                "file_id": None,
                "file_name": file_name,
                "shared_link_url": None,
                "error": error_msg,
            }

    def _slugify(self, text: str) -> str:
        """Convert text to a URL-friendly slug."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_-]+", "_", text)
        text = re.sub(r"^-+|-+$", "", text)
        return text
