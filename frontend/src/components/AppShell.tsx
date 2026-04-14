"use client";

import React, { useState, useEffect, useCallback } from "react";
import GlassSidebar from "./GlassSidebar";
import ChatFeed from "./ChatFeed";
import {
  loadConversations,
  saveConversations,
  createConversation,
  deriveTitle,
  type Conversation,
  type Message,
} from "@/lib/conversations";

export default function AppShell() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [hydrated, setHydrated] = useState(false);

  // Hydrate from localStorage on mount
  useEffect(() => {
    // History
    const stored = loadConversations();
    if (stored.length > 0) {
      setConversations(stored);
      setActiveId(stored[0].id);
    } else {
      const first = createConversation();
      setConversations([first]);
      setActiveId(first.id);
    }

    // Theme
    const storedTheme = localStorage.getItem("docurag_theme") as "dark" | "light";
    if (storedTheme) setTheme(storedTheme);

    setHydrated(true);
  }, []);

  // Persist whenever conversations change
  useEffect(() => {
    if (hydrated) saveConversations(conversations);
  }, [conversations, hydrated]);

  // Persist and apply theme
  useEffect(() => {
    if (!hydrated) return;
    localStorage.setItem("docurag_theme", theme);
    if (theme === "light") {
      document.documentElement.classList.add("light");
    } else {
      document.documentElement.classList.remove("light");
    }
  }, [theme, hydrated]);

  const activeConvo = conversations.find((c) => c.id === activeId) ?? null;

  // ── Handlers ─────────────────────────────────────────────────────
  const handleNewChat = useCallback(() => {
    const newConvo = createConversation();
    setConversations((prev) => [newConvo, ...prev]);
    setActiveId(newConvo.id);
  }, []);

  const handleChatWithDocument = useCallback((doc: any) => {
    const newConvo = createConversation(doc.id, doc.file_name);
    setConversations((prev) => [newConvo, ...prev]);
    setActiveId(newConvo.id);
  }, []);

  const handleSelectChat = useCallback((id: string) => {
    setActiveId(id);
  }, []);

  const handleDeleteChat = useCallback(
    (id: string) => {
      setConversations((prev) => {
        const filtered = prev.filter((c) => c.id !== id);
        // If we deleted the active chat, switch to the first one or create a new one
        if (id === activeId) {
          if (filtered.length > 0) {
            setActiveId(filtered[0].id);
          } else {
            const fresh = createConversation();
            filtered.push(fresh);
            setActiveId(fresh.id);
          }
        }
        return filtered;
      });
    },
    [activeId]
  );

  const handleMessagesChange = useCallback(
    (updater: (prev: Message[]) => Message[]) => {
      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== activeId) return c;
          const updated = updater(c.messages);
          // Auto-title from first user message
          const firstUser = updated.find((m) => m.role === "user");
          const title =
            c.title === "New Chat" && firstUser
              ? deriveTitle(firstUser.content)
              : c.title;
          return { ...c, messages: updated, title };
        })
      );
    },
    [activeId]
  );

  if (!hydrated) return null;

  return (
    <>
      <GlassSidebar
        conversations={conversations}
        activeId={activeId}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
        onDeleteChat={handleDeleteChat}
        onChatWithDocument={handleChatWithDocument}
      />
      <ChatFeed
        messages={activeConvo?.messages ?? []}
        onMessagesChange={handleMessagesChange}
        theme={theme}
        onThemeToggle={() => setTheme(theme === "dark" ? "light" : "dark")}
        documentId={activeConvo?.documentId}
        documentName={activeConvo?.documentName}
      />
    </>
  );
}
