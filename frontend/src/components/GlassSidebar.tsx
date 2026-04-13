"use client";

import React, { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileUp,
  FileText,
  Loader2,
  CheckCircle2,
  XCircle,
  Layers3,
  Sparkles,
  Plus,
  MessageSquare,
  Trash2,
  FileAudio,
  Image as ImageIcon,
} from "lucide-react";
import { uploadDocument, getDocuments, deleteDocument, type DocumentInfo } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Conversation } from "@/lib/conversations";

interface SidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onNewChat: () => void;
  onSelectChat: (id: string) => void;
  onDeleteChat: (id: string) => void;
}

export default function GlassSidebar({
  conversations,
  activeId,
  onNewChat,
  onSelectChat,
  onDeleteChat,
}: SidebarProps) {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{
    type: "ok" | "err";
    text: string;
  } | null>(null);
  const [dragging, setDragging] = useState(false);
  const [activeTab, setActiveTab] = useState<"chats" | "docs">("chats");

  const fetchDocs = useCallback(async () => {
    const d = await getDocuments();
    setDocs(d);
  }, []);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  // ── Upload handler ───────────────────────────────────────────────
  const handleFiles = useCallback(
    async (files: FileList | null) => {
      if (!files || files.length === 0) return;
      setUploading(true);
      setUploadMsg(null);

      try {
        const res = await uploadDocument(files[0]);
        setUploadMsg({ type: "ok", text: `${res.file_name} ingested` });
        fetchDocs();
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Upload failed";
        setUploadMsg({ type: "err", text: msg });
      } finally {
        setUploading(false);
        setTimeout(() => setUploadMsg(null), 4000);
      }
    },
    [fetchDocs]
  );
  
  // ── Delete handler ───────────────────────────────────────────────
  const handleDeleteDoc = useCallback(
    async (id: number, fileName: string) => {
      const confirmDelete = window.confirm(`Are you sure you want to permanently delete "${fileName}" and all its vector chunks? This cannot be undone.`);
      if (!confirmDelete) return;
      
      try {
        await deleteDocument(id);
        fetchDocs(); // Refresh the list
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Delete failed";
        alert(`Failed to delete document: ${msg}`);
      }
    },
    [fetchDocs]
  );

  // ── Drag & drop ──────────────────────────────────────────────────
  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="glass flex w-[300px] shrink-0 flex-col rounded-2xl m-4 mr-0 overflow-hidden"
    >
      {/* ── Header ────────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 px-5 pt-6 pb-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--accent-1)] to-[var(--accent-2)]">
          <Sparkles className="h-4 w-4 text-white" />
        </div>
        <div className="flex-1">
          <h1 className="heading-display text-[15px] leading-tight tracking-tight text-[var(--text-primary)]">
            DocuRAG
          </h1>
          <p className="text-[11px] text-[var(--text-muted)]">
            Document Intelligence
          </p>
        </div>
      </div>

      {/* ── New Chat Button ───────────────────────────────────────── */}
      <div className="px-4 pb-3">
        <button
          onClick={onNewChat}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-white/[0.08] bg-[var(--surface-1)] px-4 py-2.5 text-xs font-medium text-[var(--text-primary)] transition-all hover:border-[var(--accent-1)]/30 hover:bg-[var(--accent-1)]/5 hover:shadow-lg hover:shadow-[var(--accent-glow)]/10"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </button>
      </div>

      <div className="mx-5 h-px bg-white/[0.04]" />

      {/* ── Tab Switcher ──────────────────────────────────────────── */}
      <div className="flex px-4 pt-3 gap-1">
        <button
          onClick={() => setActiveTab("chats")}
          className={cn(
            "flex-1 rounded-lg px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider transition-all",
            activeTab === "chats"
              ? "bg-[var(--accent-1)]/10 text-[var(--accent-3)]"
              : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
          )}
        >
          Chats
        </button>
        <button
          onClick={() => setActiveTab("docs")}
          className={cn(
            "flex-1 rounded-lg px-3 py-1.5 text-[11px] font-medium uppercase tracking-wider transition-all",
            activeTab === "docs"
              ? "bg-[var(--accent-1)]/10 text-[var(--accent-3)]"
              : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
          )}
        >
          Documents
        </button>
      </div>

      {/* ── Content Area ──────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-3 pt-2 pb-3">
        {activeTab === "chats" ? (
          /* ── Conversation List ─────────────────────────────────── */
          <div className="space-y-0.5">
            {conversations.length === 0 && (
              <p className="px-2 pt-3 text-xs text-[var(--text-muted)]">
                No conversations yet.
              </p>
            )}
            <AnimatePresence>
              {conversations.map((convo, i) => (
                <motion.div
                  key={convo.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ delay: i * 0.02, duration: 0.25 }}
                  onClick={() => onSelectChat(convo.id)}
                  className={cn(
                    "group flex cursor-pointer items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm transition-all",
                    convo.id === activeId
                      ? "bg-[var(--accent-1)]/10 border border-[var(--accent-1)]/15"
                      : "hover:bg-[var(--surface-1)] border border-transparent"
                  )}
                >
                  <MessageSquare
                    className={cn(
                      "h-4 w-4 shrink-0 transition-colors",
                      convo.id === activeId
                        ? "text-[var(--accent-1)]"
                        : "text-[var(--text-muted)] group-hover:text-[var(--text-secondary)]"
                    )}
                  />
                  <span className="flex-1 truncate text-xs text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">
                    {convo.title}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteChat(convo.id);
                    }}
                    className="hidden group-hover:flex h-6 w-6 items-center justify-center rounded-md text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10 transition-all"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        ) : (
          /* ── Documents List ────────────────────────────────────── */
          <>
            {/* Dropzone */}
            <div className="pt-2 pb-3">
              <label
                role="button"
                tabIndex={0}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
                className={cn(
                  "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl px-4 py-5 text-center transition-all",
                  dragging ? "dropzone-active" : "dropzone-idle"
                )}
              >
                {uploading ? (
                  <Loader2 className="h-5 w-5 animate-spin text-[var(--accent-1)]" />
                ) : (
                  <FileUp className="h-5 w-5 text-[var(--text-muted)]" />
                )}
                <span className="text-[11px] text-[var(--text-secondary)]">
                  {uploading
                    ? "Processing..."
                    : "Drop Image, Audio, PDF, DOCX, or TXT"}
                </span>
                <input
                  type="file"
                  className="hidden"
                  accept=".pdf,.doc,.docx,.txt,audio/*,.mp3,.wav,.m4a,image/*,.png,.jpg,.jpeg,.webp"
                  onChange={(e) => handleFiles(e.target.files)}
                />
              </label>

              <AnimatePresence>
                {uploadMsg && (
                  <motion.div
                    key="upload-toast"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div
                      className={cn(
                        "mt-2 flex items-center gap-2 rounded-lg px-3 py-2 text-xs",
                        uploadMsg.type === "ok"
                          ? "bg-emerald-500/10 text-emerald-400"
                          : "bg-red-500/10 text-red-400"
                      )}
                    >
                      {uploadMsg.type === "ok" ? (
                        <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                      ) : (
                        <XCircle className="h-3.5 w-3.5 shrink-0" />
                      )}
                      <span className="truncate">{uploadMsg.text}</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* File list */}
            <div className="flex items-center gap-2 px-2 pb-2">
              <Layers3 className="h-3 w-3 text-[var(--text-muted)]" />
              <span className="text-[10px] font-semibold uppercase tracking-widest text-[var(--text-muted)]">
                Knowledge Base
              </span>
            </div>

            {docs.length === 0 && (
              <p className="px-2 text-xs text-[var(--text-muted)]">
                No documents ingested yet.
              </p>
            )}

            <AnimatePresence>
              {docs.map((doc, i) => (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04, duration: 0.3 }}
                  className="group flex items-center gap-2.5 rounded-lg px-2 py-2 text-sm transition-colors hover:bg-[var(--surface-1)]"
                >
                  {doc.file_name.toLowerCase().match(/\.(mp3|wav|m4a)$/) ? (
                    <FileAudio className="h-4 w-4 shrink-0 text-[var(--accent-1)] opacity-60 group-hover:opacity-100 transition-opacity" />
                  ) : doc.file_name.toLowerCase().match(/\.(png|jpg|jpeg|webp)$/) ? (
                    <ImageIcon className="h-4 w-4 shrink-0 text-[var(--accent-1)] opacity-60 group-hover:opacity-100 transition-opacity" />
                  ) : (
                    <FileText className="h-4 w-4 shrink-0 text-[var(--accent-1)] opacity-60 group-hover:opacity-100 transition-opacity" />
                  )}
                  <span className="flex-1 truncate text-xs text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">
                    {doc.file_name}
                  </span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteDoc(doc.id, doc.file_name);
                    }}
                    className="hidden group-hover:flex h-6 w-6 items-center justify-center rounded-md text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10 transition-all"
                    title="Permanently delete document"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
          </>
        )}
      </div>

      {/* ── Footer ────────────────────────────────────────────────── */}
      <div className="glass border-t border-white/[0.04] px-5 py-3">
        <p className="text-[10px] text-[var(--text-muted)] text-center">
          Powered by DuckDB · Ollama · FastAPI
        </p>
      </div>
    </motion.aside>
  );
}
