import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { useSendMessage } from "#/hooks/use-send-message";
import { useWsClient } from "#/context/ws-client-provider";
import { useActiveConversation } from "#/hooks/query/use-active-conversation";
import { useConversationWebSocket } from "#/contexts/conversation-websocket-context";
import { useConversationId } from "#/hooks/use-conversation-id";

vi.mock("#/context/ws-client-provider", () => ({
  useWsClient: vi.fn(),
}));

vi.mock("#/hooks/query/use-active-conversation", () => ({
  useActiveConversation: vi.fn(),
}));

vi.mock("#/contexts/conversation-websocket-context", () => ({
  useConversationWebSocket: vi.fn(),
}));

vi.mock("#/hooks/use-conversation-id", () => ({
  useConversationId: vi.fn(),
}));

const mockUseWsClient = vi.mocked(useWsClient);
const mockUseActiveConversation = vi.mocked(useActiveConversation);
const mockUseConversationWebSocket = vi.mocked(useConversationWebSocket);
const mockUseConversationId = vi.mocked(useConversationId);

describe("useSendMessage", () => {
  const v0Send = vi.fn();
  const sendMessage = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    mockUseConversationId.mockReturnValue({
      conversationId: "task-123",
    });
    mockUseActiveConversation.mockReturnValue({
      data: {
        conversation_version: "V1",
      },
    } as ReturnType<typeof useActiveConversation>);
    mockUseWsClient.mockReturnValue({
      send: v0Send,
    } as ReturnType<typeof useWsClient>);
    mockUseConversationWebSocket.mockReturnValue({
      sendMessage,
      connectionState: "OPEN",
      isLoadingHistory: false,
    } as ReturnType<typeof useConversationWebSocket>);
    sendMessage.mockResolvedValue({ queued: false });
  });

  it("sends image-only user messages through the V1 websocket path", async () => {
    const { result } = renderHook(() => useSendMessage());

    await act(async () => {
      await result.current.send({
        action: "message",
        args: {
          content: "",
          image_urls: ["data:image/png;base64,abc123"],
          file_urls: [],
        },
      });
    });

    expect(sendMessage).toHaveBeenCalledWith({
      role: "user",
      content: [
        {
          type: "image",
          image_urls: ["data:image/png;base64,abc123"],
        },
      ],
    });
    expect(v0Send).not.toHaveBeenCalled();
  });
});
