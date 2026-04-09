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
} from "lucide-react";
import { uploadDocument, getDocuments, type DocumentInfo } from "@/lib/api";
import { cn } from "@/lib/cn";

export default function GlassSidebar() {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{
    type: "ok" | "err";
    text: string;
  } | null>(null);
  const [dragging, setDragging] = useState(false);

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
        <div>
          <h1 className="heading-display text-[15px] leading-tight tracking-tight text-white">
            DocuRAG
          </h1>
          <p className="text-[11px] text-[var(--text-muted)]">
            Document Intelligence
          </p>
        </div>
      </div>

      <div className="mx-5 h-px bg-white/[0.04]" />

      {/* ── Dropzone ──────────────────────────────────────────────── */}
      <div className="px-5 pt-5">
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
            "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl px-4 py-6 text-center transition-all",
            dragging ? "dropzone-active" : "dropzone-idle"
          )}
        >
          {uploading ? (
            <Loader2 className="h-6 w-6 animate-spin text-[var(--accent-1)]" />
          ) : (
            <FileUp className="h-6 w-6 text-[var(--text-muted)]" />
          )}
          <span className="text-xs text-[var(--text-secondary)]">
            {uploading
              ? "Processing document…"
              : "Drop PDF, DOCX, or TXT here"}
          </span>
          <input
            type="file"
            className="hidden"
            accept=".pdf,.doc,.docx,.txt"
            onChange={(e) => handleFiles(e.target.files)}
          />
        </label>

        {/* Upload toast */}
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
                  "mt-3 flex items-center gap-2 rounded-lg px-3 py-2 text-xs",
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

      {/* ── Document list ─────────────────────────────────────────── */}
      <div className="mt-5 flex items-center gap-2 px-5">
        <Layers3 className="h-3.5 w-3.5 text-[var(--text-muted)]" />
        <span className="text-[11px] font-semibold uppercase tracking-widest text-[var(--text-muted)]">
          Knowledge Base
        </span>
      </div>

      <div className="mt-2 flex-1 overflow-y-auto px-3 pb-4">
        {docs.length === 0 && (
          <p className="px-2 pt-3 text-xs text-[var(--text-muted)]">
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
              className="group flex items-center gap-2.5 rounded-lg px-2 py-2 text-sm transition-colors hover:bg-white/[0.03]"
            >
              <FileText className="h-4 w-4 shrink-0 text-[var(--accent-1)] opacity-60 group-hover:opacity-100 transition-opacity" />
              <span className="truncate text-xs text-[var(--text-secondary)] group-hover:text-[var(--text-primary)] transition-colors">
                {doc.file_name}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
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
