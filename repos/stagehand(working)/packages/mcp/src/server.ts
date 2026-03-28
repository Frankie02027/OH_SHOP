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
// Model & LLM settings
const MODEL_NAME = (process.env.STAGEHAND_MODEL ?? "").trim();
const BASE_URL   = process.env.STAGEHAND_LLM_BASE_URL ?? "http://localhost:1235/v1";
const API_KEY    = process.env.STAGEHAND_LLM_API_KEY ?? "lm-studio";

// Browser settings
const CHROME     = process.env.CHROME_PATH ?? "/usr/bin/chromium";
const HEADLESS   = process.env.HEADLESS !== "false";
const BROWSER_WIDTH  = parseInt(process.env.BROWSER_WIDTH ?? "1288", 10);
const BROWSER_HEIGHT = parseInt(process.env.BROWSER_HEIGHT ?? "711", 10);
const DEVTOOLS   = process.env.DEVTOOLS === "true";

// Server settings
const HOST       = process.env.MCP_HOST ?? "0.0.0.0";
const PORT       = parseInt(process.env.MCP_PORT ?? "3020", 10);

// Feature flags (match official MCP server)
const EXPERIMENTAL = process.env.EXPERIMENTAL === "true";

function log(msg: string) {
  process.stderr.write(`[stagehand-mcp] ${new Date().toISOString()} ${msg}\n`);
}

// ── Stagehand lifecycle ──────────────────────────────────────────────────────
// Per docs: use llmClient + AISdkClient for custom providers
// createOpenAI().chat() forces Chat Completions API (not Responses API)
let stagehand: Stagehand | null = null;
let resolvedModelName: string | null = null;

async function getStagehandModelName(): Promise<string> {
  if (resolvedModelName) return resolvedModelName;

  if (MODEL_NAME) {
    resolvedModelName = MODEL_NAME;
    return resolvedModelName;
  }

  const modelsUrl = `${BASE_URL.replace(/\/$/, "")}/models`;
  const resp = await globalThis.fetch(modelsUrl);
  if (!resp.ok) {
    throw new Error(
      `Failed to auto-detect Stagehand model from ${modelsUrl}: HTTP ${resp.status}`,
    );
  }

  const payload = await resp.json() as {
    data?: Array<{ id?: unknown }>;
  };
  const detected = payload.data?.find((entry) => typeof entry?.id === "string")?.id;
  if (typeof detected !== "string" || !detected.trim()) {
    throw new Error(
      `No model ID reported by ${modelsUrl}; set STAGEHAND_MODEL explicitly or load a model in LM Studio before startup.`,
    );
  }

  resolvedModelName = detected.trim();
  log(`Auto-detected Stagehand model: ${resolvedModelName}`);
  return resolvedModelName;
}

async function getStagehand(): Promise<Stagehand> {
  if (stagehand) return stagehand;

  const modelName = await getStagehandModelName();
  log(`Initializing Stagehand: model=${modelName} baseURL=${BASE_URL}`);

  const provider = createOpenAICompatible({
    name: "lm-studio",
    apiKey: API_KEY,
    baseURL: BASE_URL,
    supportsStructuredOutputs: true,
    fetch: async (url, init) => {
      // LM Studio requires "strict": true in json_schema to enforce grammar constraint.
      // @ai-sdk/openai-compatible does not set it. Inject it in the request body.
      if (init?.body) {
        let body = typeof init.body === 'string' ? init.body : new TextDecoder().decode(init.body as any);
        if (body.includes('"json_schema"')) {
          try {
            const parsed = JSON.parse(body);
            if (parsed.response_format?.json_schema) {
              parsed.response_format.json_schema.strict = true;
              // Strip fields that LM Studio grammar engine can't handle
              function cleanSchema(obj: any) {
                if (obj && typeof obj === 'object') {
                  delete obj.$schema;   // JSON Schema meta-field
                  delete obj.pattern;   // regex patterns not supported by GBNF grammar
                  for (const val of Object.values(obj)) cleanSchema(val);
                }
              }
              cleanSchema(parsed.response_format.json_schema.schema);
              body = JSON.stringify(parsed);
              init = { ...init, body };
              // strict:true injected, schema cleaned
            }
          } catch { /* ignore parse errors */ }
        }
      }
      const resp = await globalThis.fetch(url as any, init as any);
      // Log non-2xx responses for debugging
      if (!resp.ok) {
        const clone = resp.clone();
        clone.text().then(t => log(`LLM error ${resp.status}: ${t.substring(0, 500)}`)).catch(() => {});
      }
      // Fix response: strip brackets from elementId values so they match pattern ^\\d+-\\d+$
      const ct = resp.headers.get('content-type') || '';
      if (!ct.includes('event-stream') && init?.body) {
        const bodyStr = typeof init.body === 'string' ? init.body : '';
        if (bodyStr.includes('"json_schema"')) {
          const clone = resp.clone();
          try {
            const text = await clone.text();
            const parsed = JSON.parse(text);
            const content = parsed.choices?.[0]?.message?.content;
            if (content && typeof content === 'string') {
              // Fix elementId: "[0-18]" -> "0-18"
              const fixed = content.replace(/\[(\d+-\d+)\]/g, '$1');
              if (fixed !== content) {
                parsed.choices[0].message.content = fixed;
                // elementId brackets fixed
                return new Response(JSON.stringify(parsed), {
                  status: resp.status,
                  statusText: resp.statusText,
                  headers: resp.headers,
                });
              }
            }
          } catch { /* use original response */ }
        }
      }
      return resp;
    },
  });

  const llmClient = new AISdkClient({
    model: provider.chatModel(modelName),
  });

  stagehand = new Stagehand({
    env: "LOCAL",
    llmClient,
    localBrowserLaunchOptions: {
      executablePath: CHROME,
      headless: HEADLESS,
      devtools: DEVTOOLS,
      viewport: {
        width: BROWSER_WIDTH,
        height: BROWSER_HEIGHT,
      },
      deviceScaleFactor: 1,
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        `--window-size=${BROWSER_WIDTH},${BROWSER_HEIGHT}`,
      ],
    },
    experimental: EXPERIMENTAL,
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
    {
      url: z.string().describe("The URL to navigate to"),
      tabIndex: z.number().optional().describe("Tab index to navigate (default: 0). Use browserbase_tabs_list to see tabs."),
    },
    async ({ url, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        if (idx < 0 || idx >= pages.length) throw new Error(`Tab index ${idx} out of range`);
        const page = pages[idx];
        await page.goto(url, { waitUntil: "domcontentloaded" });
        return { content: [{ type: "text" as const, text: `Tab ${idx}: Navigated to: ${url}` }] };
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
      tabIndex: z.number().optional().describe("Tab index to act on (default: 0)"),
    },
    async ({ action, variables, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        const page = idx < pages.length ? pages[idx] : undefined;
        await sh.act(action, { variables, page });
        return { content: [{ type: "text" as const, text: `Tab ${idx}: Action performed: ${action}` }] };
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
      tabIndex: z.number().optional().describe("Tab index to extract from (default: 0)"),
    },
    async ({ instruction, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        const page = idx < pages.length ? pages[idx] : undefined;
        const extraction = await sh.extract(instruction, { page });
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
      tabIndex: z.number().optional().describe("Tab index to observe (default: 0)"),
    },
    async ({ instruction, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        const page = idx < pages.length ? pages[idx] : undefined;
        const observations = await sh.observe(instruction, { page });
        return {
          content: [{
            type: "text" as const,
            text: `Tab ${idx} observations: ${JSON.stringify(observations)}`,
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
      tabIndex: z.number().optional().describe("Tab index to screenshot (default: 0)"),
    },
    async ({ name: screenshotName, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        if (idx < 0 || idx >= pages.length) throw new Error(`Tab index ${idx} out of range`);
        const page = pages[idx];
        const buf = await page.screenshot({ fullPage: true, type: "png" });
        const finalName = screenshotName ?? `screenshot-${new Date().toISOString().replace(/:/g, "-")}`;
        return {
          content: [
            { type: "text" as const, text: `Tab ${idx}: Screenshot taken with name: ${finalName}` },
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
    {
      tabIndex: z.number().optional().describe("Tab index to get URL from (default: 0)"),
    },
    async ({ tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        if (idx < 0 || idx >= pages.length) throw new Error(`Tab index ${idx} out of range`);;
        const page = pages[idx];
        return { content: [{ type: "text" as const, text: `Tab ${idx}: ${page.url()}` }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to get current URL: ${msg}`);
      }
    }
  );

  // --- browserbase_session_create ---
  // Reset/create a fresh browser session (closes existing and starts new)
  mcp.tool(
    "browserbase_session_create",
    "Create a new browser session (resets browser state). Closes any existing session and starts fresh. " +
    "Useful when you need a clean slate without cookies/history from previous actions.",
    {},
    async () => {
      try {
        await closeStagehand();
        const sh = await getStagehand();
        const pages = sh.context.pages();
        return {
          content: [{
            type: "text" as const,
            text: JSON.stringify({
              success: true,
              message: "New browser session created",
              config: {
                viewport: `${BROWSER_WIDTH}x${BROWSER_HEIGHT}`,
                headless: HEADLESS,
                experimental: EXPERIMENTAL,
              },
              tabs: pages.length,
            }, null, 2),
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to create session: ${msg}`);
      }
    }
  );

  // --- browserbase_session_close ---
  // Close the current browser session
  mcp.tool(
    "browserbase_session_close",
    "Close the current browser session. Frees resources and closes the browser. " +
    "A new session will be created automatically on the next tool call.",
    {},
    async () => {
      try {
        await closeStagehand();
        return {
          content: [{
            type: "text" as const,
            text: JSON.stringify({
              success: true,
              message: "Browser session closed",
            }, null, 2),
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to close session: ${msg}`);
      }
    }
  );

  // --- browserbase_get_config ---
  // Get current server configuration
  mcp.tool(
    "browserbase_get_config",
    "Get current MCP server configuration including model, viewport, and feature flags.",
    {},
    async () => {
      const sh = stagehand; // May be null if not initialized
      const pages = sh?.context?.pages() ?? [];
      return {
        content: [{
          type: "text" as const,
          text: JSON.stringify({
            server: {
              host: HOST,
              port: PORT,
              version: "0.3.0",
            },
            model: {
              name: MODEL_NAME,
              baseUrl: BASE_URL,
            },
            browser: {
              viewport: { width: BROWSER_WIDTH, height: BROWSER_HEIGHT },
              headless: HEADLESS,
              devtools: DEVTOOLS,
              executablePath: CHROME,
            },
            features: {
              experimental: EXPERIMENTAL,
            },
            session: {
              active: !!sh,
              tabs: pages.length,
            },
          }, null, 2),
        }],
      };
    }
  );

  // --- browserbase_get_connect_url ---
  // Get WebSocket URL for external Puppeteer/Playwright connections
  mcp.tool(
    "browserbase_get_connect_url",
    "Get the WebSocket URL to connect external Puppeteer or Playwright to Stagehand's browser. " +
    "Use with puppeteer.connect({ browserWSEndpoint: url }) or playwright.chromium.connectOverCDP(url).",
    {},
    async () => {
      try {
        const sh = await getStagehand();
        const connectUrl = sh.connectURL();
        return {
          content: [{
            type: "text" as const,
            text: JSON.stringify({
              connectUrl,
              usage: {
                puppeteer: `puppeteer.connect({ browserWSEndpoint: "${connectUrl}", defaultViewport: null })`,
                playwright: `chromium.connectOverCDP("${connectUrl}")`,
              },
            }, null, 2),
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to get connect URL: ${msg}`);
      }
    }
  );

  // --- browserbase_tabs_list ---
  // List all open tabs with their indexes and URLs
  mcp.tool(
    "browserbase_tabs_list",
    "List all open browser tabs with their index and URL.",
    {},
    async () => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const tabs = pages.map((page, index) => ({
          index,
          url: page.url(),
          title: "", // Playwright page.title() is async, keeping it simple
        }));
        return {
          content: [{
            type: "text" as const,
            text: JSON.stringify({ tabCount: tabs.length, tabs }, null, 2),
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to list tabs: ${msg}`);
      }
    }
  );

  // --- browserbase_tab_new ---
  // Create a new browser tab
  mcp.tool(
    "browserbase_tab_new",
    "Create a new browser tab, optionally navigating to a URL.",
    {
      url: z.string().optional().describe("URL to navigate to in the new tab (optional)"),
    },
    async ({ url }) => {
      try {
        const sh = await getStagehand();
        const newPage = await sh.context.newPage();
        if (url) {
          await newPage.goto(url, { waitUntil: "domcontentloaded" });
        }
        const pages = sh.context.pages();
        const newIndex = pages.indexOf(newPage);
        return {
          content: [{
            type: "text" as const,
            text: `New tab created at index ${newIndex}${url ? `, navigated to: ${url}` : ""}`,
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to create new tab: ${msg}`);
      }
    }
  );

  // --- browserbase_tab_focus ---
  // Focus/switch to a specific tab by index
  mcp.tool(
    "browserbase_tab_focus",
    "Focus/switch to a specific browser tab by index. Use browserbase_tabs_list to see available tabs.",
    {
      index: z.number().describe("The index of the tab to focus (0-based)"),
    },
    async ({ index }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        if (index < 0 || index >= pages.length) {
          throw new Error(`Tab index ${index} out of range (0-${pages.length - 1})`);
        }
        const page = pages[index];
        // Stagehand Page doesn't have bringToFront, so we reload to activate
        // This effectively makes it the "active" page for subsequent operations
        const currentUrl = page.url();
        return {
          content: [{
            type: "text" as const,
            text: `Tab ${index} selected: ${currentUrl}\nNote: Use tabIndex parameter in other tools to operate on this tab.`,
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to focus tab: ${msg}`);
      }
    }
  );

  // --- browserbase_tab_close ---
  // Close a specific tab by index
  mcp.tool(
    "browserbase_tab_close",
    "Close a browser tab by index. Cannot close the last remaining tab.",
    {
      index: z.number().describe("The index of the tab to close (0-based)"),
    },
    async ({ index }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        if (pages.length <= 1) {
          throw new Error("Cannot close the last remaining tab");
        }
        if (index < 0 || index >= pages.length) {
          throw new Error(`Tab index ${index} out of range (0-${pages.length - 1})`);
        }
        const page = pages[index];
        const url = page.url();
        await page.close();
        return {
          content: [{
            type: "text" as const,
            text: `Closed tab ${index}: ${url}`,
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to close tab: ${msg}`);
      }
    }
  );

  // ══════════════════════════════════════════════════════════════════════════
  // Context Tools - Cookie, Headers, Init Script management
  // ══════════════════════════════════════════════════════════════════════════

  // --- browserbase_cookies_get ---
  // Get browser cookies
  mcp.tool(
    "browserbase_cookies_get",
    "Get browser cookies, optionally filtered by URL. Returns all cookies or only those matching the URL domain/path.",
    {
      url: z.string().optional().describe("Optional URL to filter cookies by domain/path"),
    },
    async ({ url }) => {
      try {
        const sh = await getStagehand();
        const cookies = url 
          ? await sh.context.cookies(url)
          : await sh.context.cookies();
        return {
          content: [{
            type: "text" as const,
            text: JSON.stringify({
              count: cookies.length,
              cookies: cookies.map(c => ({
                name: c.name,
                value: c.value.substring(0, 50) + (c.value.length > 50 ? '...' : ''),
                domain: c.domain,
                path: c.path,
                expires: c.expires,
                httpOnly: c.httpOnly,
                secure: c.secure,
                sameSite: c.sameSite,
              })),
            }, null, 2),
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to get cookies: ${msg}`);
      }
    }
  );

  // --- browserbase_cookies_set ---
  // Set browser cookies
  mcp.tool(
    "browserbase_cookies_set",
    "Set one or more browser cookies. Use for authentication, session management, or preferences.",
    {
      cookies: z.array(z.object({
        name: z.string().describe("Cookie name"),
        value: z.string().describe("Cookie value"),
        url: z.string().optional().describe("URL (used to derive domain/path). Provide either url OR domain+path"),
        domain: z.string().optional().describe("Cookie domain (e.g., '.example.com')"),
        path: z.string().optional().default("/").describe("Cookie path"),
        expires: z.number().optional().describe("Unix timestamp in seconds. Omit for session cookie"),
        httpOnly: z.boolean().optional().describe("HTTP only flag"),
        secure: z.boolean().optional().describe("Secure flag (required if sameSite='None')"),
        sameSite: z.enum(["Strict", "Lax", "None"]).optional().describe("SameSite policy"),
      })).describe("Array of cookies to set"),
    },
    async ({ cookies }) => {
      try {
        const sh = await getStagehand();
        await sh.context.addCookies(cookies as any);
        return {
          content: [{
            type: "text" as const,
            text: `Set ${cookies.length} cookie(s): ${cookies.map(c => c.name).join(', ')}`,
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to set cookies: ${msg}`);
      }
    }
  );

  // --- browserbase_cookies_clear ---
  // Clear browser cookies
  mcp.tool(
    "browserbase_cookies_clear",
    "Clear browser cookies. Can clear all cookies or filter by name/domain/path patterns.",
    {
      name: z.string().optional().describe("Cookie name to clear (exact match)"),
      domain: z.string().optional().describe("Domain pattern to clear"),
      path: z.string().optional().describe("Path pattern to clear"),
    },
    async ({ name, domain, path }) => {
      try {
        const sh = await getStagehand();
        const options: any = {};
        if (name) options.name = name;
        if (domain) options.domain = domain;
        if (path) options.path = path;
        
        await sh.context.clearCookies(Object.keys(options).length > 0 ? options : undefined);
        const filterDesc = Object.keys(options).length > 0 
          ? `matching ${JSON.stringify(options)}`
          : "all";
        return {
          content: [{
            type: "text" as const,
            text: `Cleared ${filterDesc} cookies`,
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to clear cookies: ${msg}`);
      }
    }
  );

  // --- browserbase_set_headers ---
  // Set extra HTTP headers for all requests
  mcp.tool(
    "browserbase_set_headers",
    "Set custom HTTP headers that will be included in every request from all pages. " +
    "Use for auth tokens, custom headers, etc. Call with empty object to clear.",
    {
      headers: z.record(z.string()).describe(
        "Object of header name-value pairs. Example: {\"Authorization\": \"Bearer token\", \"X-Custom\": \"value\"}"
      ),
    },
    async ({ headers }) => {
      try {
        const sh = await getStagehand();
        await sh.context.setExtraHTTPHeaders(headers);
        const headerCount = Object.keys(headers).length;
        return {
          content: [{
            type: "text" as const,
            text: headerCount > 0
              ? `Set ${headerCount} custom header(s): ${Object.keys(headers).join(', ')}`
              : "Cleared all custom headers",
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to set headers: ${msg}`);
      }
    }
  );

  // --- browserbase_add_init_script ---
  // Inject JavaScript to run before page scripts
  mcp.tool(
    "browserbase_add_init_script",
    "Inject JavaScript that runs before any page scripts on every navigation. " +
    "Use for: disabling dialogs, mocking APIs, adding polyfills, etc. " +
    "Applied to all existing and future pages.",
    {
      script: z.string().describe(
        "JavaScript code to inject. Runs at document start before page scripts. " +
        "Example: 'window.alert = () => {};' to disable alerts"
      ),
    },
    async ({ script }) => {
      try {
        const sh = await getStagehand();
        await sh.context.addInitScript(script);
        return {
          content: [{
            type: "text" as const,
            text: `Init script added (${script.length} chars). Will run on all page navigations.`,
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Failed to add init script: ${msg}`);
      }
    }
  );

  // ══════════════════════════════════════════════════════════════════════════
  // Direct Playwright Tools - Low-level browser control
  // ══════════════════════════════════════════════════════════════════════════

  // --- browserbase_evaluate ---
  // Run JavaScript in the page context
  mcp.tool(
    "browserbase_evaluate",
    "Execute JavaScript code in the browser page context. Returns the result as JSON.",
    {
      script: z.string().describe("JavaScript code to execute in page context (will be wrapped in a function)"),
      tabIndex: z.number().optional().describe("Tab index (default: 0)"),
    },
    async ({ script, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        if (idx < 0 || idx >= pages.length) throw new Error(`Tab index ${idx} out of range`);
        const page = pages[idx];
        // Wrap script in a function that evaluates and returns
        const result = await page.evaluate(`(() => { ${script} })()`);
        return {
          content: [{
            type: "text" as const,
            text: JSON.stringify(result, null, 2),
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Evaluate failed: ${msg}`);
      }
    }
  );

  // --- browserbase_click_selector ---
  // Click element by CSS selector
  mcp.tool(
    "browserbase_click_selector",
    "Click an element by CSS selector. Use for precise element targeting.",
    {
      selector: z.string().describe("CSS selector for the element to click"),
      tabIndex: z.number().optional().describe("Tab index (default: 0)"),
    },
    async ({ selector, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        if (idx < 0 || idx >= pages.length) throw new Error(`Tab index ${idx} out of range`);
        const page = pages[idx];
        await page.locator(selector).click();
        return { content: [{ type: "text" as const, text: `Clicked: ${selector}` }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Click failed: ${msg}`);
      }
    }
  );

  // --- browserbase_fill ---
  // Fill an input field by CSS selector (via JS)
  mcp.tool(
    "browserbase_fill",
    "Fill text into an input field by CSS selector.",
    {
      selector: z.string().describe("CSS selector for the input field"),
      text: z.string().describe("Text to fill into the field"),
      tabIndex: z.number().optional().describe("Tab index (default: 0)"),
    },
    async ({ selector, text, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        if (idx < 0 || idx >= pages.length) throw new Error(`Tab index ${idx} out of range`);
        const page = pages[idx];
        // Use evaluate to fill the input
        const escapedText = text.replace(/'/g, "\\'").replace(/\n/g, "\\n");
        await page.evaluate(`(() => {
          const el = document.querySelector('${selector}');
          if (!el) throw new Error('Element not found: ${selector}');
          el.focus();
          el.value = '${escapedText}';
          el.dispatchEvent(new Event('input', { bubbles: true }));
          el.dispatchEvent(new Event('change', { bubbles: true }));
        })()`);
        return { content: [{ type: "text" as const, text: `Filled ${selector} with "${text}"` }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Fill failed: ${msg}`);
      }
    }
  );

  // --- browserbase_keyboard_type ---
  // Type text by dispatching key events
  mcp.tool(
    "browserbase_keyboard_type",
    "Type text character by character. Works on the currently focused element.",
    {
      text: z.string().describe("Text to type"),
      tabIndex: z.number().optional().describe("Tab index (default: 0)"),
    },
    async ({ text, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        if (idx < 0 || idx >= pages.length) throw new Error(`Tab index ${idx} out of range`);
        const page = pages[idx];
        // Type by setting value and dispatching events
        const escapedText = text.replace(/'/g, "\\'").replace(/\n/g, "\\n");
        await page.evaluate(`(() => {
          const el = document.activeElement;
          if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable)) {
            el.value = (el.value || '') + '${escapedText}';
            el.dispatchEvent(new Event('input', { bubbles: true }));
          }
        })()`);
        return { content: [{ type: "text" as const, text: `Typed: "${text}"` }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Keyboard type failed: ${msg}`);
      }
    }
  );

  // --- browserbase_keyboard_press ---
  // Press a key by dispatching events
  mcp.tool(
    "browserbase_keyboard_press",
    "Press a keyboard key (Enter, Tab, Escape, etc.) via key events.",
    {
      key: z.string().describe("Key to press (e.g., 'Enter', 'Tab', 'Escape', 'ArrowDown')"),
      tabIndex: z.number().optional().describe("Tab index (default: 0)"),
    },
    async ({ key, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        if (idx < 0 || idx >= pages.length) throw new Error(`Tab index ${idx} out of range`);
        const page = pages[idx];
        await page.evaluate(`(() => {
          const el = document.activeElement || document.body;
          el.dispatchEvent(new KeyboardEvent('keydown', { key: '${key}', bubbles: true }));
          el.dispatchEvent(new KeyboardEvent('keyup', { key: '${key}', bubbles: true }));
          if ('${key}' === 'Enter') {
            const form = el.closest('form');
            if (form) form.submit();
          }
        })()`);
        return { content: [{ type: "text" as const, text: `Pressed: ${key}` }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Keyboard press failed: ${msg}`);
      }
    }
  );

  // --- browserbase_mouse_click ---
  // Click at coordinates via JS
  mcp.tool(
    "browserbase_mouse_click",
    "Click at specific x,y coordinates on the page.",
    {
      x: z.number().describe("X coordinate"),
      y: z.number().describe("Y coordinate"),
      tabIndex: z.number().optional().describe("Tab index (default: 0)"),
    },
    async ({ x, y, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        if (idx < 0 || idx >= pages.length) throw new Error(`Tab index ${idx} out of range`);
        const page = pages[idx];
        await page.evaluate(`(() => {
          const el = document.elementFromPoint(${x}, ${y});
          if (el) {
            el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: ${x}, clientY: ${y} }));
          }
        })()`);
        return { content: [{ type: "text" as const, text: `Clicked at (${x}, ${y})` }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Mouse click failed: ${msg}`);
      }
    }
  );

  // --- browserbase_scroll ---
  // Scroll the page via JS
  mcp.tool(
    "browserbase_scroll",
    "Scroll the page by pixels.",
    {
      deltaX: z.number().optional().default(0).describe("Horizontal scroll amount in pixels"),
      deltaY: z.number().optional().default(0).describe("Vertical scroll amount in pixels (positive = down)"),
      tabIndex: z.number().optional().describe("Tab index (default: 0)"),
    },
    async ({ deltaX, deltaY, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        if (idx < 0 || idx >= pages.length) throw new Error(`Tab index ${idx} out of range`);
        const page = pages[idx];
        await page.evaluate(`window.scrollBy(${deltaX ?? 0}, ${deltaY ?? 0})`);
        return { content: [{ type: "text" as const, text: `Scrolled by (${deltaX}, ${deltaY})` }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Scroll failed: ${msg}`);
      }
    }
  );

  // --- browserbase_wait_for_selector ---
  // Wait for an element to appear
  mcp.tool(
    "browserbase_wait_for_selector",
    "Wait for an element matching the selector to appear in the DOM.",
    {
      selector: z.string().describe("CSS selector to wait for"),
      timeout: z.number().optional().default(30000).describe("Timeout in milliseconds (default: 30000)"),
      tabIndex: z.number().optional().describe("Tab index (default: 0)"),
    },
    async ({ selector, timeout, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        if (idx < 0 || idx >= pages.length) throw new Error(`Tab index ${idx} out of range`);
        const page = pages[idx];
        await page.waitForSelector(selector, { timeout });
        return { content: [{ type: "text" as const, text: `Element found: ${selector}` }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Wait for selector failed: ${msg}`);
      }
    }
  );

  // --- browserbase_wait_for_timeout ---
  // Wait for a specified duration
  mcp.tool(
    "browserbase_wait_for_timeout",
    "Wait for a specified number of milliseconds.",
    {
      timeout: z.number().describe("Duration to wait in milliseconds"),
    },
    async ({ timeout }) => {
      try {
        const sh = await getStagehand();
        const page = sh.context.pages()[0];
        await page.waitForTimeout(timeout);
        return { content: [{ type: "text" as const, text: `Waited ${timeout}ms` }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Wait failed: ${msg}`);
      }
    }
  );

  // --- browserbase_get_html ---
  // Get page HTML content via JS
  mcp.tool(
    "browserbase_get_html",
    "Get the HTML content of the page or a specific element.",
    {
      selector: z.string().optional().describe("CSS selector (omit for full page HTML)"),
      tabIndex: z.number().optional().describe("Tab index (default: 0)"),
    },
    async ({ selector, tabIndex }) => {
      try {
        const sh = await getStagehand();
        const pages = sh.context.pages();
        const idx = tabIndex ?? 0;
        if (idx < 0 || idx >= pages.length) throw new Error(`Tab index ${idx} out of range`);
        const page = pages[idx];
        let html: string;
        if (selector) {
          html = await page.evaluate(`document.querySelector('${selector}')?.innerHTML || ''`) as string;
        } else {
          html = await page.evaluate(`document.documentElement.outerHTML`) as string;
        }
        // Truncate if too long
        const maxLen = 50000;
        const truncated = html.length > maxLen ? html.substring(0, maxLen) + "\n... (truncated)" : html;
        return { content: [{ type: "text" as const, text: truncated }] };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        throw new Error(`Get HTML failed: ${msg}`);
      }
    }
  );

  // --- browserbase_stagehand_agent ---
  // Agent mode: autonomous multi-step task execution using same llmClient
  mcp.tool(
    "browserbase_stagehand_agent",
    "Execute an autonomous agent to complete a complex multi-step task. " +
    "The agent uses the same LLM provider as other tools. " +
    "Use for complex tasks requiring multiple actions, navigation, and decision-making.",
    {
      instruction: z.string().describe(
        "A detailed instruction of the task for the agent to complete. " +
        "Be specific about the goal and any constraints. For example: " +
        "'Go to google.com, search for Stagehand AI, and extract the first 3 results'."
      ),
      maxSteps: z.number().optional().default(10).describe(
        "Maximum number of steps the agent can take (default: 10). " +
        "Each step is one LLM call + tool execution."
      ),
      mode: z.enum(["dom", "hybrid"]).optional().default("dom").describe(
        "Agent tool mode: 'dom' (default) uses DOM-based tools for structured interactions, " +
        "'hybrid' adds coordinate-based tools for visual interactions."
      ),
    },
    async ({ instruction, maxSteps, mode }) => {
      try {
        const sh = await getStagehand();
        log(`Agent starting: instruction="${instruction.substring(0, 100)}..." maxSteps=${maxSteps} mode=${mode}`);
        
        // Agent SDK requires supported provider prefix. For OpenAI-compatible endpoints (LM Studio),
        // use "openai/<model>" with custom baseURL. The actual model is served locally.
        // Extract just the model name without provider prefix for the openai format.
        const agentModelName = await getStagehandModelName();
        const modelNameOnly = agentModelName.includes("/") ? agentModelName.split("/").pop()! : agentModelName;
        const agent = sh.agent({
          mode: mode as "dom" | "hybrid",
          model: {
            modelName: `openai/${modelNameOnly}`,
            apiKey: API_KEY,
            baseURL: BASE_URL,
          },
        });
        const result = await agent.execute({
          instruction,
          maxSteps,
        });

        log(`Agent completed: success=${result.success} actions=${result.actions.length} completed=${result.completed}`);

        return {
          content: [{
            type: "text" as const,
            text: JSON.stringify({
              success: result.success,
              message: result.message,
              completed: result.completed,
              actionsCount: result.actions.length,
              actions: result.actions,
              usage: result.usage,
            }, null, 2),
          }],
        };
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        const stack = e instanceof Error ? e.stack : "";
        log(`Agent error: ${msg}\n${stack}`);
        throw new Error(`Agent failed: ${msg}`);
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
httpServer.listen(PORT, HOST, () => {
  log(`Ready on ${HOST}:${PORT}`);
  log(`MCP endpoint: http://${HOST}:${PORT}/mcp`);
  log(`Model: ${MODEL_NAME || "(auto-detect from provider)"} via ${BASE_URL}`);
  log(`Browser: ${BROWSER_WIDTH}x${BROWSER_HEIGHT} headless=${HEADLESS} experimental=${EXPERIMENTAL}`);
});

const shutdown = async () => {
  log("Shutting down...");
  await closeStagehand();
  httpServer.close();
  process.exit(0);
};

process.on("SIGTERM", () => shutdown().catch(() => process.exit(1)));
process.on("SIGINT", () => shutdown().catch(() => process.exit(1)));
