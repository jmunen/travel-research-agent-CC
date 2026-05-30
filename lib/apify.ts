import { ApifyClient } from 'apify-client';
import type { ResearchResult, TravelResearchInput } from './types';

function getApifyToken() {
    const token = process.env.APIFY_TOKEN;
  
    if (!token) {
      throw new Error('Missing APIFY_TOKEN in .env.local');
    }
  
    return token;
  }
  
  function getApifyClient() {
    return new ApifyClient({
      token: getApifyToken(),
    });
  }

function buildTravelQueries(input: TravelResearchInput): string[] {
  const destination = input.destination.trim();

  const queries = [
    `best things to do in ${destination} travel guide`,
    `best restaurants in ${destination} travel guide`,
    `${destination} neighborhoods to visit`,
    `${destination} safety tips for travelers`,
  ];

  if (input.tripLength) {
    queries.push(`${destination} ${input.tripLength} itinerary`);
  }

  if (input.interests && input.interests.length > 0) {
    queries.push(`${destination} ${input.interests.join(' ')} travel recommendations`);
  }

  return queries;
}

export async function getTravelResearchFromApify(
  input: TravelResearchInput
): Promise<ResearchResult[]> {
  const client = getApifyClient();
  const queries = buildTravelQueries(input);

  const actorId = 'apify/google-search-scraper';

  const actorInput = {
    queries,
    maxPagesPerQuery: 1,
    resultsPerPage: 3,
  };

  const run = await client.actor(actorId).call(actorInput);

  if (!run.defaultDatasetId) {
    throw new Error('Apify run did not return a default dataset ID.');
  }

  const { items } = await client.dataset(run.defaultDatasetId).listItems();

  const results: ResearchResult[] = items
    .map((item: any) => {
      const title =
        item.title ||
        item.name ||
        item.pageTitle ||
        'Untitled source';

      const url =
        item.url ||
        item.link ||
        item.displayedUrl ||
        '';

      const text =
        item.description ||
        item.snippet ||
        item.text ||
        item.content ||
        '';

      return {
        title,
        url,
        text,
        source: 'Apify',
      };
    })
    .filter((item) => item.url && item.text)
    .slice(0, 10);

  return results;
}