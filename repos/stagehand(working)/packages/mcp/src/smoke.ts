/**
 * Phase 0 smoke test — verifies Stagehand + LM Studio before Docker build.
 * Run on host: cd packages/mcp && npx tsx src/smoke.ts
 */
import { Stagehand } from "@browserbasehq/stagehand";

const MODEL    = process.env.STAGEHAND_MODEL         ?? "openai/all-hands_openhands-lm-32b-v0.1";
const BASE_URL = process.env.STAGEHAND_LLM_BASE_URL  ?? "http://localhost:1234/v1";
const API_KEY  = process.env.STAGEHAND_LLM_API_KEY    ?? "lm-studio";
const CHROME   = process.env.CHROME_PATH              ?? "/usr/bin/chromium";

async function main() {
  console.log("=== Phase 0 smoke test ===");
  console.log(`model:   ${MODEL}`);
  console.log(`baseURL: ${BASE_URL}`);

  // 1. LM Studio reachable?
  const resp = await fetch(`${BASE_URL}/models`);
  if (!resp.ok) throw new Error(`LM Studio unreachable: ${resp.status}`);
  const models = await resp.json() as { data: { id: string }[] };
  const found = models.data.find((m: { id: string }) => MODEL.includes(m.id));
  console.log(`LM Studio models: ${models.data.map((m: { id: string }) => m.id).join(", ")}`);
  if (!found) throw new Error(`Model ${MODEL} not found in LM Studio`);
  console.log("✓ LM Studio OK");

  // 2. Init Stagehand
  const stagehand = new Stagehand({
    env: "LOCAL",
    model: { modelName: MODEL, apiKey: API_KEY, baseURL: BASE_URL },
    localBrowserLaunchOptions: {
      executablePath: CHROME,
      headless: true,
      args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
    },
    verbose: 1,
    disablePino: true,
  });
  await stagehand.init();
  console.log("✓ Stagehand init OK");

  // 3. Navigate
  const page = stagehand.context.pages()[0];
  await page.goto("https://example.com", { waitUntil: "domcontentloaded" });
  const title = await page.title();
  console.log(`✓ page.goto OK — title: "${title}"`);

  // 4. Extract
  const result = await stagehand.extract("What is the heading on this page?");
  console.log("✓ extract() OK:", JSON.stringify(result));

  await stagehand.close();
  console.log("\n=== Phase 0 PASSED ===");
}

main().catch((err) => {
  console.error("\n=== Phase 0 FAILED ===", err);
  process.exit(1);
});
