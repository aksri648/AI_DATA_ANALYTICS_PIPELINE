import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  chart?: string;
  insights?: string;
  timestamp: string;
}

interface ChatStore {
  messages: ChatMessage[];
  addMessage: (msg: Omit<ChatMessage, "timestamp">) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set) => ({
      messages: [],
      addMessage: (msg) =>
        set((state) => ({
          messages: [
            ...state.messages,
            { ...msg, timestamp: new Date().toISOString() },
          ],
        })),
      clearMessages: () => set({ messages: [] }),
    }),
    {
      name: "analytics-chat-history",
    }
  )
);
