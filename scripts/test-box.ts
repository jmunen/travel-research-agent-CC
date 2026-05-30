import dotenv from 'dotenv';

dotenv.config({ path: '.env.local' });

async function main() {
  const { saveTravelBriefToBox } = await import('../lib/box');

  const result = await saveTravelBriefToBox({
    destination: 'Mexico City',
    briefMarkdown: `# Mexico City Travel Brief

This is a test file from the Travel Research Agent hackathon app.

## Best Things to Do
- Visit museums
- Try local food
- Explore beautiful neighborhoods

## Saved By
Travel Research Agent
`,
  });

  console.log(result);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});