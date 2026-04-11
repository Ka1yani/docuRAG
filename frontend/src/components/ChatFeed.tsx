"use client";

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Loader2,
  BotMessageSquare,
  User,
  BookOpen,
  Zap,
  Database,
  Cpu,
  Sun,
  Moon,
} from "lucide-react";
import { askQuestion, type AskResponse, type Citation } from "@/lib/api";
import { cn } from "@/lib/cn";
import { uid, type Message } from "@/lib/conversations";

// ── Props ──────────────────────────────────────────────────────────
interface ChatFeedProps {
  messages: Message[];
  onMessagesChange: (updater: (prev: Message[]) => Message[]) => void;
  theme: "dark" | "light";
  onThemeToggle: () => void;
}

// ── Chat Component ─────────────────────────────────────────────────
export default function ChatFeed({ messages, onMessagesChange, theme, onThemeToggle }: ChatFeedProps) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    const query = input.trim();
    if (!query || loading) return;

    const userMsg: Message = { id: uid(), role: "user", content: query };
    onMessagesChange((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const t0 = performance.now();

    try {
      const data: AskResponse = await askQuestion(query);
      const elapsed = (performance.now() - t0) / 1000;

      const botMsg: Message = {
        id: uid(),
        role: "assistant",
        content: data.final_answer,
        citations: data.citations,
        timing: { question: elapsed, total: elapsed },
      };
      onMessagesChange((prev) => [...prev, botMsg]);
    } catch (err: unknown) {
      const errText =
        err instanceof Error ? err.message : "Something went wrong";
      onMessagesChange((prev) => [
        ...prev,
        { id: uid(), role: "assistant", content: `⚠️ ${errText}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col p-4 pl-4 relative">
      {/* ── Theme Toggle ────────────────────────────────────────────── */}
      <button
        onClick={onThemeToggle}
        className="absolute top-6 right-8 z-50 flex h-9 w-9 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.03] text-[var(--text-muted)] backdrop-blur-md transition-all hover:bg-white/[0.08] hover:text-[var(--text-primary)] shadow-sm"
      >
        {theme === "dark" ? (
          <Sun className="h-4 w-4" />
        ) : (
          <Moon className="h-4 w-4" />
        )}
      </button>

      {/* ── Chat container ──────────────────────────────────────── */}
      <div className="glass flex flex-1 flex-col rounded-2xl overflow-hidden shadow-lg relative">
        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-6 pt-14 pb-6 space-y-1">
          {messages.length === 0 && <EmptyState />}

          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, ease: "easeOut" }}
                className={cn(
                  "flex gap-3 py-4",
                  msg.role === "user" ? "justify-end" : "justify-start"
                )}
              >
                {msg.role === "assistant" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--accent-1)] to-[var(--accent-3)] mt-0.5">
                    <BotMessageSquare className="h-4 w-4 text-white" />
                  </div>
                )}

                <div
                  className={cn(
                    "max-w-[720px] rounded-2xl px-5 py-3.5 text-sm leading-relaxed",
                    msg.role === "user"
                      ? "bg-gradient-to-r from-[var(--accent-1)]/20 to-[var(--accent-2)]/10 border border-[var(--accent-1)]/20 text-[var(--text-primary)]"
                      : "bg-[var(--surface-1)] border border-white/[0.04] text-[var(--text-primary)]"
                  )}
                >
                  <div className="prose-answer whitespace-pre-wrap">
                    {msg.content}
                  </div>

                  {/* Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2 border-t border-white/[0.05] pt-3">
                      {msg.citations.map((c, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--accent-1)]/10 px-2.5 py-1 text-[11px] text-[var(--accent-3)]"
                        >
                          <BookOpen className="h-3 w-3" />
                          {c.file_name}
                          <span className="text-[var(--text-muted)]">
                            p.{c.page_number}
                          </span>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Timing */}
                  {msg.timing && (
                    <div className="mt-3 border-t border-white/[0.05] pt-3">
                      <div className="flex items-center gap-1.5 text-[10px] text-[var(--text-muted)]">
                        <Zap className="h-3 w-3" />
                        Answered in {msg.timing.total.toFixed(1)}s
                      </div>
                    </div>
                  )}
                </div>

                {msg.role === "user" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[var(--surface-2)] border border-white/[0.08] mt-0.5">
                    <User className="h-4 w-4 text-[var(--text-secondary)]" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Typing indicator */}
          <AnimatePresence>
            {loading && (
              <motion.div
                key="loader"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-3 py-4"
              >
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--accent-1)] to-[var(--accent-3)]">
                  <BotMessageSquare className="h-4 w-4 text-white" />
                </div>
                <div className="glass flex items-center gap-3 rounded-2xl px-5 py-3.5">
                  <Loader2 className="h-4 w-4 animate-spin text-[var(--accent-1)]" />
                  <span className="text-xs text-[var(--text-secondary)]">
                    Searching documents & generating answer…
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div ref={endRef} />
        </div>

        {/* ── Input Bar ─────────────────────────────────────────── */}
        <div className="border-t border-white/[0.04] px-4 py-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="glass flex items-center gap-3 rounded-xl px-4 py-2.5 transition-all focus-within:border-[var(--accent-1)]/30"
          >
            <input
              id="chat-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything about your documents…"
              disabled={loading}
              className="flex-1 bg-transparent text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className={cn(
                "flex h-9 w-9 items-center justify-center rounded-lg transition-all",
                input.trim()
                  ? "bg-gradient-to-r from-[var(--accent-1)] to-[var(--accent-2)] text-white shadow-lg shadow-[var(--accent-glow)] hover:scale-105"
                  : "bg-[var(--surface-2)] text-[var(--text-muted)]"
              )}
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

// ── Empty State ────────────────────────────────────────────────────
function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="flex h-full flex-col items-center justify-center gap-6 py-20"
    >
      <div className="relative">
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-[var(--accent-1)] to-[var(--accent-3)] opacity-20 blur-2xl" />
        <div className="relative flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-[var(--accent-1)]/20 to-[var(--accent-2)]/10 border border-white/[0.06]">
          <BotMessageSquare className="h-9 w-9 text-[var(--accent-1)]" />
        </div>
      </div>

      <div className="text-center max-w-sm">
        <h2 className="heading-display text-xl text-[var(--text-primary)] mb-2">
          Ask your documents anything
        </h2>
        <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
          Upload a PDF, DOCX, or TXT to your knowledge base, then query it with
          natural language. Powered by semantic vector search and a local LLM.
        </p>
      </div>

      <div className="flex gap-4 text-[11px] text-[var(--text-muted)]">
        <span className="flex items-center gap-1.5">
          <Database className="h-3.5 w-3.5" /> DuckDB
        </span>
        <span className="flex items-center gap-1.5">
          <Cpu className="h-3.5 w-3.5" /> Ollama LLM
        </span>
        <span className="flex items-center gap-1.5">
          <Zap className="h-3.5 w-3.5" /> Semantic Cache
        </span>
      </div>
    </motion.div>
  );
}
