/**
 * Model Router Proxy
 *
 * Sits between OpenHands/Stagehand and LM Studio.
 *
 * Behavior:
 * - Text requests default to the model that is currently loaded in LM Studio,
 *   unless TEXT_MODEL is explicitly set.
 * - Vision requests always use the pinned VL model.
 * - Image inputs are first converted to text by the VL model, then handed to
 *   the text model so the main chat model remains the one "driving" the chat.
 * - Only one model is ever kept resident on the GPU at a time. Every swap
 *   unloads the currently loaded model before loading the next one.
 */

import { serve } from "bun";
import { $ } from "bun";

const LMS = process.env.LMS_PATH || "/home/dev/.lmstudio/bin/lms";
const LM_STUDIO_URL = process.env.LM_STUDIO_URL || "http://localhost:1234";
const ROUTER_PORT = parseInt(process.env.ROUTER_PORT || "1235");
const TEXT_MODEL_OVERRIDE = (process.env.TEXT_MODEL || "").trim() || null;
const VL_MODEL = (process.env.VL_MODEL || "qwen/qwen3-vl-8b").trim();
const VISION_PROMPT = `
You are a vision-to-text preprocessing model for a coding assistant.

Your only job is to convert image inputs into a highly detailed, high-accuracy textual record for a downstream text model.

You must NOT solve the user's task, give advice, explain what to do next, or summarize aggressively.
You must only report what is visibly present in the image.

Priority order:
1. Exact visible text
2. Exact code / commands / terminal output
3. UI structure and screen state
4. Uncertainties and missing/cropped regions

Core rules:
- Treat screenshots like forensic captures of screen state.
- Prefer exact transcription over paraphrase whenever text is readable.
- Keep exact transcription separate from descriptive interpretation.
- Do not guess hidden, cropped, blurred, or occluded content.
- If something is uncertain, mark it explicitly instead of inventing content.
- If multiple images are provided, process each image separately and keep them clearly distinct.
- If multiple panes, windows, tabs, or sections are visible, describe each one separately.
- If code, terminal output, stack traces, diffs, logs, commands, filenames, URLs, labels, or error text are visible, transcribe them as exactly as possible.
- Preserve spelling, capitalization, punctuation, symbols, indentation, and line breaks when they materially affect meaning.
- If exact line breaks or indentation are unclear, say so explicitly.
- Do not merge separate windows, panes, or images into one combined description.
- Do not infer intent, hidden state, or off-screen content unless it is directly visible.

Output format:
For each image, use this structure exactly:

IMAGE <n>

1. Overall scene
- Brief description of what the image shows at a high level.

2. Exact visible text
- Transcribe all clearly readable visible text.
- Group by region/pane/window if needed.
- Use verbatim text where possible.

3. Code / commands / terminal / logs
- Transcribe visible code, shell commands, terminal output, stack traces, diffs, warnings, and errors exactly where possible.

4. UI structure and state
- Describe the visible application(s), panes, tabs, buttons, forms, cursor location, selected items, scroll position if apparent, and any visible state indicators.

5. Uncertainties
- List any blurry, cropped, partially hidden, obstructed, or ambiguous content.
- For uncertain text, use this format:
  [unclear: possible text here]

6. Do not solve
- Do not provide troubleshooting, conclusions, or next steps.
- Do not answer the user's actual task.
`.trim();

let currentModelKind: "text" | "vl" | "unknown" = "unknown";
let currentLoadedModelId: string | null = null;
let preferredTextModelId: string | null = TEXT_MODEL_OVERRIDE;
let swapInProgress = false;

async function log(msg: string) {
  const ts = new Date().toISOString();
  console.log(`[${ts}] ${msg}`);
}

async function getCurrentLoadedModel(): Promise<string | null> {
  try {
    const result = await $`${LMS} ps --json`.quiet();
    const data = JSON.parse(result.stdout.toString());
    if (Array.isArray(data) && data.length > 0) {
      const first = data[0];
      return first?.path || first?.model || first?.id || null;
    }
    return null;
  } catch {
    return null;
  }
}

function stripProviderPrefix(model: unknown): string | null {
  if (typeof model !== "string") {
    return null;
  }

  const trimmed = model.trim();
  if (!trimmed) {
    return null;
  }

  if (trimmed.startsWith("openai/")) {
    return trimmed.slice("openai/".length) || null;
  }

  return trimmed;
}

function classifyLoadedModel(modelId: string | null): "text" | "vl" | "unknown" {
  if (!modelId) {
    return "unknown";
  }
  if (modelId === VL_MODEL || /(?:^|[-_/])vl(?:[-_/]|$)/i.test(modelId)) {
    return "vl";
  }
  return "text";
}

async function refreshCurrentLoadedModel(): Promise<string | null> {
  currentLoadedModelId = await getCurrentLoadedModel();
  currentModelKind = classifyLoadedModel(currentLoadedModelId);
  if (currentModelKind === "text" && currentLoadedModelId) {
    preferredTextModelId = currentLoadedModelId;
  }
  return currentLoadedModelId;
}

async function resolveTextModelId(requestedModel: unknown): Promise<string | null> {
  if (TEXT_MODEL_OVERRIDE) {
    preferredTextModelId = TEXT_MODEL_OVERRIDE;
    return TEXT_MODEL_OVERRIDE;
  }

  const loaded = await refreshCurrentLoadedModel();
  if (loaded && loaded !== VL_MODEL) {
    preferredTextModelId = loaded;
    return loaded;
  }

  if (preferredTextModelId) {
    return preferredTextModelId;
  }

  const requested = stripProviderPrefix(requestedModel);
  if (requested) {
    preferredTextModelId = requested;
    return requested;
  }

  return null;
}

async function swapModel(
  target: "text" | "vl",
  targetModelId: string,
): Promise<boolean> {
  if (swapInProgress) {
    await log("Swap already in progress, waiting...");
    while (swapInProgress) {
      await Bun.sleep(500);
    }
    return currentLoadedModelId === targetModelId;
  }

  const loaded = await refreshCurrentLoadedModel();
  if (loaded === targetModelId) {
    return true;
  }

  swapInProgress = true;

  try {
    await log(`Preparing GPU for ${target} model (${targetModelId})...`);

    if (loaded) {
      await log(`Unloading current model: ${loaded}`);
      await $`${LMS} unload --all`.quiet();
      await Bun.sleep(2000);
    }

    await log(`Loading ${target} model: ${targetModelId}`);
    await $`${LMS} load ${targetModelId} --yes`.quiet();
    await Bun.sleep(3000);

    currentLoadedModelId = targetModelId;
    currentModelKind = target;
    if (target === "text") {
      preferredTextModelId = targetModelId;
    }

    await log(`Model swap complete: ${targetModelId}`);
    return true;
  } catch (e) {
    await log(`Model swap failed: ${e}`);
    return false;
  } finally {
    swapInProgress = false;
  }
}

function extractImageParts(messages: unknown): Array<Record<string, unknown>> {
  if (!Array.isArray(messages)) {
    return [];
  }

  const imageParts: Array<Record<string, unknown>> = [];
  for (const message of messages) {
    if (!message || typeof message !== "object") {
      continue;
    }
    const content = (message as { content?: unknown }).content;
    if (!Array.isArray(content)) {
      continue;
    }
    for (const part of content) {
      if (!part || typeof part !== "object") {
        continue;
      }
      const type = (part as { type?: unknown }).type;
      if (type === "image_url" || type === "image") {
        imageParts.push(part as Record<string, unknown>);
      }
    }
  }
  return imageParts;
}

function extractTextContext(messages: unknown): string {
  if (!Array.isArray(messages)) {
    return "";
  }

  const parts: string[] = [];
  for (const message of messages) {
    if (!message || typeof message !== "object") {
      continue;
    }

    const role = (message as { role?: unknown }).role;
    const content = (message as { content?: unknown }).content;

    if (typeof content === "string" && content.trim()) {
      parts.push(`${String(role || "user")}: ${content.trim()}`);
      continue;
    }

    if (!Array.isArray(content)) {
      continue;
    }

    const textBits: string[] = [];
    for (const part of content) {
      if (!part || typeof part !== "object") {
        continue;
      }
      if ((part as { type?: unknown }).type === "text") {
        const text = (part as { text?: unknown }).text;
        if (typeof text === "string" && text.trim()) {
          textBits.push(text.trim());
        }
      }
    }

    if (textBits.length > 0) {
      parts.push(`${String(role || "user")}: ${textBits.join("\n")}`);
    }
  }

  return parts.join("\n\n");
}

function rewriteBodyForTextModel(
  body: any,
  description: string,
  textModelId: string,
): any {
  const rewritten = JSON.parse(JSON.stringify(body));
  const originalMessages = Array.isArray(rewritten.messages) ? rewritten.messages : [];

  rewritten.model = textModelId;
  rewritten.messages = [
    {
      role: "system",
      content: [
        "Vision bridge note:",
        "The original image inputs were converted to text by the pinned VL model.",
        "Use this description as the authoritative substitute for the uploaded images:",
        description,
      ].join("\n\n"),
    },
    ...originalMessages.map((message: any) => {
      if (!Array.isArray(message?.content)) {
        return message;
      }

      const textParts: string[] = [];
      for (const part of message.content) {
        if (!part || typeof part !== "object") {
          continue;
        }
        if (part.type === "text" && typeof part.text === "string" && part.text.trim()) {
          textParts.push(part.text.trim());
        }
      }

      return {
        ...message,
        content: textParts.join("\n\n") || "Refer to the vision bridge description above.",
      };
    }),
  ];

  return rewritten;
}

async function describeImagesWithVision(targetUrl: string, body: any): Promise<string> {
  const imageParts = extractImageParts(body?.messages);
  if (imageParts.length === 0) {
    throw new Error("No image inputs found for vision preprocessing.");
  }

  const swapped = await swapModel("vl", VL_MODEL);
  if (!swapped) {
    throw new Error(`Failed to load pinned VL model ${VL_MODEL}.`);
  }

  const textContext = extractTextContext(body?.messages);
  const visionPayload = {
    model: VL_MODEL,
    stream: false,
    temperature: 0,
    messages: [
      {
        role: "system",
        content: VISION_PROMPT,
      },
      {
        role: "user",
        content: [
          {
            type: "text",
            text: textContext
              ? `User text context:\n${textContext}\n\nDescribe the attached image inputs in detail.`
              : "Describe the attached image inputs in detail.",
          },
          ...imageParts,
        ],
      },
    ],
  };

  const response = await fetch(targetUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(visionPayload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Vision preprocessing failed with HTTP ${response.status}: ${detail}`);
  }

  const payload = await response.json();
  const description = payload?.choices?.[0]?.message?.content;
  if (typeof description !== "string" || !description.trim()) {
    throw new Error("Vision preprocessing returned no usable description.");
  }

  return description.trim();
}

async function proxyRequest(req: Request): Promise<Response> {
  const url = new URL(req.url);
  const targetUrl = `${LM_STUDIO_URL}${url.pathname}${url.search}`;

  if (!url.pathname.includes("/chat/completions")) {
    return fetch(targetUrl, {
      method: req.method,
      headers: req.headers,
      body: req.body,
    });
  }

  let body: any;
  try {
    body = await req.json();
  } catch {
    return new Response("Invalid JSON", { status: 400 });
  }

  const requestedModel = body?.model;
  const hasImages = extractImageParts(body?.messages).length > 0;

  if (hasImages) {
    await log("Image input detected. Unloading current model, loading pinned VL model, generating description, then handing off to the text model.");

    const description = await describeImagesWithVision(targetUrl, body);
    const textModelId = await resolveTextModelId(requestedModel);
    if (!textModelId) {
      return new Response(
        "No text model is available for the post-vision handoff.",
        { status: 503 },
      );
    }

    const textReady = await swapModel("text", textModelId);
    if (!textReady) {
      return new Response(
        `Failed to reload the text model ${textModelId} after the vision pass.`,
        { status: 503 },
      );
    }

    body = rewriteBodyForTextModel(body, description, textModelId);
  } else {
    const textModelId = await resolveTextModelId(requestedModel);
    if (!textModelId) {
      return new Response(
        "No text model is loaded or configured for chat requests.",
        { status: 503 },
      );
    }

    await log(`Text request using ${textModelId}`);
    const textReady = await swapModel("text", textModelId);
    if (!textReady) {
      return new Response(
        `Failed to load text model ${textModelId}.`,
        { status: 503 },
      );
    }

    body.model = textModelId;
  }

  return fetch(targetUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function init() {
  const loaded = await refreshCurrentLoadedModel();
  if (loaded) {
    await log(`Detected current LM Studio model: ${loaded} (${currentModelKind})`);
  } else {
    await log("No model is currently loaded in LM Studio.");
  }

  if (TEXT_MODEL_OVERRIDE) {
    preferredTextModelId = TEXT_MODEL_OVERRIDE;
    await log(`Text model override pinned via TEXT_MODEL=${TEXT_MODEL_OVERRIDE}`);
  } else if (preferredTextModelId) {
    await log(`Default text model will follow the currently loaded LM Studio model: ${preferredTextModelId}`);
  } else {
    await log("Default text model is dynamic and will follow the currently loaded LM Studio model.");
  }
}

await init();

serve({
  port: ROUTER_PORT,
  async fetch(req) {
    try {
      return await proxyRequest(req);
    } catch (e) {
      await log(`Proxy error: ${e}`);
      return new Response(`Proxy error: ${e}`, { status: 500 });
    }
  },
});

await log(`Model Router listening on port ${ROUTER_PORT}`);
await log(`Proxying to LM Studio at ${LM_STUDIO_URL}`);
await log(
  TEXT_MODEL_OVERRIDE
    ? `Text model override: ${TEXT_MODEL_OVERRIDE}`
    : "Text model source: current LM Studio load / request model",
);
await log(`Pinned VL model: ${VL_MODEL}`);
