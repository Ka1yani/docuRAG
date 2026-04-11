import type { Metadata } from "next";
import { Outfit, DM_Sans } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
  weight: ["400", "500", "600", "700", "800"],
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "DocuRAG — Intelligent Document Intelligence",
  description:
    "Upload your private documents and query them with AI-powered semantic search. Enterprise-grade retrieval-augmented generation, running entirely on your infrastructure.",
  keywords: ["RAG", "document AI", "semantic search", "LLM", "DuckDB"],
  openGraph: {
    title: "DocuRAG",
    description: "Enterprise AI Document Intelligence",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${outfit.variable} ${dmSans.variable}`}>
      <body className="h-screen overflow-hidden antialiased">
        {/* Animated cosmic background */}
        <div className="animated-bg" aria-hidden="true" />

        {/* Application shell */}
        <div className="relative z-10 flex h-full">
          {children}
        </div>
      </body>
    </html>
  );
}
