import 'dotenv/config';
import { getTravelResearchFromApify } from '../lib/apify';

async function main() {
  const results = await getTravelResearchFromApify({
    destination: 'Mexico City',
    tripLength: '4 days',
    budget: 'mid-range',
    travelStyle: 'solo',
    interests: ['food', 'museums', 'photography'],
    notes: 'I want beautiful neighborhoods and local experiences.',
  });

  console.log(JSON.stringify(results, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});