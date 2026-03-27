/**
 * oh-stagehand MCP SHTTP server
 *
 * Minimal MCP server following the official @browserbasehq/mcp-server-browserbase
 * patterns (https://docs.stagehand.dev/v3/integrations/mcp/introduction).
 *
 * Adapted for LOCAL browser + custom LLM endpoint (LM Studio / Ollama / etc).
 *
 * Tools (matching official naming):
 *   browserbase_stagehand_navigate  — goto URL
 *   browserbase_stagehand_act       — perform a single action
 *   browserbase_stagehand_extract   — extract structured data
 *   browserbase_stagehand_observe   — observe interactive elements
 *   browserbase_screenshot          — take a screenshot
 *   browserbase_stagehand_get_url   — get current URL
 */

import dotenv from "dotenv";
dotenv.config({ path: ".env" });

import http from "node:http";
import crypto from "node:crypto";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
import { Stagehand, AISdkClient } from "@browserbasehq/stagehand";
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";

// ── Config from env ──────────────────────────────────────────────────────────
const MODEL_NAME = process.env.STAGEHAND_MODEL ?? "all-hands_openhands-lm-32b-v0.1";
const BASE_URL   = process.env.STAGEHAND_LLM_BASE_URL ?? "http://host.docker.internal:1234/v1";
const API_KEY    = process.env.STAGEHAND_LLM_API_KEY ?? "lm-studio";
const CHROME     = process.env.CHROME_PATH ?? "/usr/bin/chromium";
const HEADLESS   = process.env.HEADLESS !== "false";
const PORT       = parseInt(process.env.MCP_PORT ?? "3020", 10);

function log(msg: string) {
  process.stderr.write(`[stagehand-mcp] ${new Date().toISOString()} ${msg}\n`);
}

// ── Stagehand lifecycle ──────────────────────────────────────────────────────
// Per docs: use llmClient + AISdkClient for custom providers
// createOpenAI().chat() forces Chat Completions API (not Responses API)
let stagehand: Stagehand | null = null;

async function getStagehand(): Promise<Stagehand> {
  if (stagehand) return stagehand;

  log(`Initializing Stagehand: model=${MODEL_NAME} baseURL=${BASE_URL}`);

  const provider = createOpenAICompatible({
    name: "lm-studio",
    apiKey: API_KEY,
    baseURL: BASE_URL,
    supportsStructuredOutputs: true,
    fetch: async (url, init) => {
      log(`LLM request: ${url}`);
      if (init?.body) {
        const body = typeof init.body === 'string' ? init.body : JSON.stringify(init.body);
        log(`LLM body (first 2000): ${body.slice(0, 2000)}`);
      }
      const resp = await globalThis.fetch(url as any, init as any);
      // Clone and read body for logging
      const cloned = resp.clone();
      const text = await cloned.text();
      if (!resp.ok) {
        log(`LLM error ${resp.status}: ${text.slice(0, 500)}`);
      } else {
        log(`LLM response ${resp.status} (first 1000): ${text.slice(0, 1000)}`);
      }
      return resp;
    },
  });

  const llmClient = new AISdkClient({
    model: provider.chatModel(MODEL_NAME),
  });

  stagehand = new Stagehand({
    env: "LOCAL",
    llmClient,
    localBrowserLaunchOptions: {
      executablePath: CHROME,
      headless: HEADLESS,
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
      ],
    },
    verbose: 1,
    logger: (logLine) => {
      log(`Stagehand: ${logLine.message}`);
    },
  });

  await stagehand.init();
  log("Stagehand initialized");
  return stagehand;
}

async function closeStagehand(): Promise<void> {
  if (stagehand) {
    await stagehand.close().catch(() => {});
    stagehand = null;
  }
}

// ── MCP Server factory ──────────────────────────────────────────────────────
// Following official pattern from @browserbasehq/mcp-server-browserbase
function createMcpServer(): McpServer {
  const mcp = new McpServer({
    name: "stagehand-mcp",
    version: "0.3.0",
  });

  // --- browserbase_stagehand_navigate ---
  // Pattern: official navigate.js
  mcp.tool(
    "browserbase_stagehand_navigate",
    "Navigate to a URL in the browser. Only use this tool with URLs you're " +
    "confident will work and be up to date. Otherwise, use https://google.com as the starting point",
    { url: z.string().describe("The URL to navigate to") },
    async ({ url }) => {
      try {
        const sh = await getStagehand();
        const page = sh.context.pages()[0];
        if (!page) throw new Error("No active page available");
        await page.goto(url, { waitUntil: "domcontentloaded" });
        return { content: [{ type: "text" as const, text: `Navigated to: ${url}` }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to navigate: ${msg}`);
      }
    }
  );

  // --- browserbase_stagehand_act ---
  // Pattern: official act.js
  mcp.tool(
    "browserbase_stagehand_act",
    "Perform a single action on the page (e.g., click, type).",
    {
      action: z.string().describe(
        "The action to perform. Should be as atomic and specific as possible, " +
        "i.e. 'Click the sign in button' or 'Type hello into the search input'."
      ),
      variables: z.record(z.string()).optional().describe(
        "Variables used in the action template. ONLY use variables if you're dealing " +
        "with sensitive data or dynamic content."
      ),
    },
    async ({ action, variables }) => {
      try {
        const sh = await getStagehand();
        await sh.act(action, { variables });
        return { content: [{ type: "text" as const, text: `Action performed: ${action}` }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to perform action: ${msg}`);
      }
    }
  );

  // --- browserbase_stagehand_extract ---
  // Pattern: official extract.js
  mcp.tool(
    "browserbase_stagehand_extract",
    "Extract structured data or text from the current page using an instruction.",
    {
      instruction: z.string().describe(
        "The specific instruction for what information to extract from the current page. " +
        "Be as detailed and specific as possible about what you want to extract. For example: " +
        "'Extract all product names and prices from the listing page'."
      ),
    },
    async ({ instruction }) => {
      try {
        const sh = await getStagehand();
        const extraction = await sh.extract(instruction);
        return {
          content: [{
            type: "text" as const,
            text: `Extracted content:\n${JSON.stringify(extraction, null, 2)}`,
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to extract content: ${msg}`);
      }
    }
  );

  // --- browserbase_stagehand_observe ---
  // Pattern: official observe.js
  mcp.tool(
    "browserbase_stagehand_observe",
    "Find interactive elements on the page from an instruction; optionally return an action.",
    {
      instruction: z.string().describe(
        "Detailed instruction for what specific elements or components to observe on the web page. " +
        "This instruction must be extremely specific and descriptive. For example: " +
        "'Find the red login button in the top right corner' or 'Locate the search input field'."
      ),
    },
    async ({ instruction }) => {
      try {
        const sh = await getStagehand();
        const observations = await sh.observe(instruction);
        return {
          content: [{
            type: "text" as const,
            text: `Observations: ${JSON.stringify(observations)}`,
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        const stack = e instanceof Error ? e.stack : "";
        log(`observe error: ${msg}\n${stack}`);
        throw new Error(`Failed to observe: ${msg}`);
      }
    }
  );

  // --- browserbase_screenshot ---
  // Pattern: official screenshot.js (simplified — no sharp/resize for local use)
  mcp.tool(
    "browserbase_screenshot",
    "Capture a full-page screenshot and return it as a PNG image.",
    {
      name: z.string().optional().describe("The name of the screenshot"),
    },
    async ({ name: screenshotName }) => {
      try {
        const sh = await getStagehand();
        const page = sh.context.pages()[0];
        if (!page) throw new Error("No active page available");
        const buf = await page.screenshot({ fullPage: true, type: "png" });
        const finalName = screenshotName ?? `screenshot-${new Date().toISOString().replace(/:/g, "-")}`;
        return {
          content: [
            { type: "text" as const, text: `Screenshot taken with name: ${finalName}` },
            { type: "image" as const, data: buf.toString("base64"), mimeType: "image/png" },
          ],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to take screenshot: ${msg}`);
      }
    }
  );

  // --- browserbase_stagehand_get_url ---
  // Pattern: official url.js
  mcp.tool(
    "browserbase_stagehand_get_url",
    "Return the current page URL (full URL with query/fragment).",
    {},
    async () => {
      try {
        const sh = await getStagehand();
        const page = sh.context.pages()[0];
        if (!page) throw new Error("No active page available");
        return { content: [{ type: "text" as const, text: page.url() }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to get current URL: ${msg}`);
      }
    }
  );

  return mcp;
}

// ── SHTTP transport ─────────────────────────────────────────────────────────
// Pattern: official transport.js  handleStreamable + startHttpTransport
const sessions = new Map<string, StreamableHTTPServerTransport>();

async function handleStreamable(
  req: http.IncomingMessage,
  res: http.ServerResponse,
) {
  const sessionId = req.headers["mcp-session-id"] as string | undefined;

  if (sessionId) {
    const transport = sessions.get(sessionId);
    if (!transport) {
      res.statusCode = 404;
      res.end("Session not found");
      return;
    }
    return await transport.handleRequest(req, res);
  }

  if (req.method === "POST") {
    const newId = crypto.randomUUID();
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => newId,
    });
    sessions.set(newId, transport);
    transport.onclose = () => {
      if (transport.sessionId) sessions.delete(transport.sessionId);
    };
    const mcp = createMcpServer();
    await mcp.connect(transport);
    return await transport.handleRequest(req, res);
  }

  res.statusCode = 400;
  res.end("Invalid request");
}

// ── HTTP server ─────────────────────────────────────────────────────────────
const httpServer = http.createServer(async (req, res) => {
  if (!req.url) {
    res.statusCode = 400;
    res.end("Bad request: missing URL");
    return;
  }

  const url = new URL(`http://localhost${req.url}`);

  // Health endpoint
  if (url.pathname === "/healthz") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ status: "ok", timestamp: new Date().toISOString() }));
    return;
  }

  // MCP endpoint
  if (url.pathname.startsWith("/mcp")) {
    await handleStreamable(req, res);
    return;
  }

  res.statusCode = 404;
  res.end("Not found");
});

// ── Lifecycle ────────────────────────────────────────────────────────────────
httpServer.listen(PORT, "0.0.0.0", () => {
  log(`Ready on port ${PORT}`);
  log(`MCP endpoint: http://0.0.0.0:${PORT}/mcp`);
  log(`Model: ${MODEL_NAME} via ${BASE_URL}`);
});

const shutdown = async () => {
  log("Shutting down...");
  await closeStagehand();
  httpServer.close();
  process.exit(0);
};

process.on("SIGTERM", () => shutdown().catch(() => process.exit(1)));
process.on("SIGINT", () => shutdown().catch(() => process.exit(1)));
