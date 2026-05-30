"""Builds AI prompts from collected travel data and user preferences."""

import logging
from datetime import datetime
from models.schemas import TravelPreferences

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Constructs structured prompts for the AI summarizer."""

    def build_summary_prompt(
        self,
        destination: str,
        preferences: TravelPreferences | None,
        raw_data: list[dict],
    ) -> str:
        """
        Build a detailed prompt for Claude to generate a structured travel brief.

        Args:
            destination: The travel destination.
            preferences: Optional user travel preferences.
            raw_data: List of scraped data dicts with title, url, description keys.

        Returns:
            A formatted prompt string for the AI model.
        """
        # Format raw data into a readable block
        data_block = self._format_raw_data(raw_data)

        # Build preferences context
        prefs_block = self._format_preferences(preferences)

        current_year = datetime.now().year

        prompt = f"""You are an expert travel researcher and writer. Based on the following web research data about {destination}, create a comprehensive and well-organized travel brief in Markdown format.

## User Preferences
{prefs_block}

## Research Data Collected from the Web
{data_block}

## Instructions
Using the research data above (and your own knowledge to fill gaps), create a polished travel brief for **{destination}** with the following sections:

# Travel Brief: {destination}

## 1. Destination Overview
Provide a compelling 2-3 paragraph overview of the destination, including what makes it special, the general vibe, and who it's best suited for.

## 2. Top Attractions & Things To Do
List 8-10 must-see attractions and activities. For each, include a brief description and any practical tips (best time to visit, cost, etc.).

## 3. Best Restaurants & Food Scene
Recommend 6-8 restaurants or food experiences across different price points. Include cuisine type, price range, and what to order.

## 4. Neighborhoods to Explore
Describe 4-6 key neighborhoods/areas, what they're known for, and what to do in each.

## 5. Practical Tips
Cover:
- Safety considerations
- Getting around (transport options)
- Budget tips and expected costs
- Cultural etiquette
- Best time to visit

## 6. Suggested Itinerary
Create a day-by-day itinerary{f" for a {preferences.trip_length} trip" if preferences and preferences.trip_length else " for a 5-day trip"}. Include morning, afternoon, and evening suggestions for each day.

## 7. Quick Reference
Provide a quick-reference table or list with:
- Best time to visit
- Currency
- Language(s)
- Time zone
- Emergency numbers
- Visa requirements (general guidance)
- Tipping customs

## Formatting Guidelines
- Use clean Markdown formatting
- Be specific with recommendations (names, addresses when possible)
- Include price indicators ($ / $$ / $$$ / $$$$)
- Make it actionable and practical
- Current year is {current_year} - ensure information is up to date
- Tailor recommendations to the user's preferences where applicable
"""
        return prompt

    def _format_raw_data(self, raw_data: list[dict]) -> str:
        """Format raw scraped data into a readable text block."""
        if not raw_data:
            return "No web research data was collected. Please use your own knowledge to create the travel brief."

        formatted_items = []
        for i, item in enumerate(raw_data, 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "")
            description = item.get("description", item.get("snippet", "No description available"))

            formatted_items.append(
                f"### Source {i}\n"
                f"- **Title:** {title}\n"
                f"- **URL:** {url}\n"
                f"- **Content:** {description}\n"
            )

        return "\n".join(formatted_items)

    def _format_preferences(self, preferences: TravelPreferences | None) -> str:
        """Format user preferences into a readable block."""
        if not preferences:
            return "No specific preferences provided. Create a general-purpose travel brief."

        parts = []

        if preferences.travel_dates:
            parts.append(f"- **Travel Dates:** {preferences.travel_dates}")
        if preferences.trip_length:
            parts.append(f"- **Trip Length:** {preferences.trip_length}")
        if preferences.budget_level:
            parts.append(f"- **Budget Level:** {preferences.budget_level.value}")
        if preferences.travel_style:
            parts.append(f"- **Travel Style:** {', '.join(preferences.travel_style)}")
        if preferences.food_interests:
            parts.append(f"- **Food Interests:** {', '.join(preferences.food_interests)}")
        if preferences.group_type:
            parts.append(f"- **Group Type:** {preferences.group_type.value}")

        if not parts:
            return "No specific preferences provided. Create a general-purpose travel brief."

        return "\n".join(parts)
