"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ReportViewerProps {
  report: string;
  sessionId: string;
  topic: string;
}

export function ReportViewer({ report, sessionId, topic }: ReportViewerProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadFormat, setDownloadFormat] = useState<"docx" | "pdf" | null>(null);
  
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  
  const handleDownload = async (format: "docx" | "pdf") => {
    setIsDownloading(true);
    setDownloadFormat(format);
    
    try {
      const response = await fetch(
        `${API_URL}/api/v1/research/${sessionId}/report/${format}`
      );
      
      if (!response.ok) {
        throw new Error(`Failed to download ${format.toUpperCase()}`);
      }
      
      // Get the blob
      const blob = await response.blob();
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `curriculum_research_${topic.replace(/[^\w\s-]/g, "").replace(/[-\s]+/g, "_")}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Download error:", error);
      alert(`Failed to download ${format.toUpperCase()}. Please try again.`);
    } finally {
      setIsDownloading(false);
      setDownloadFormat(null);
    }
  };
  
  return (
    <div className="space-y-4">
      {/* Download buttons */}
      <div className="flex items-center justify-between p-4 bg-background-tertiary border border-zinc-700 rounded-lg">
        <div>
          <h3 className="text-sm font-medium text-text-primary">
            Research Report Complete
          </h3>
          <p className="text-xs text-text-secondary mt-1">
            Download your comprehensive curriculum research report
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleDownload("docx")}
            disabled={isDownloading}
            className="px-4 py-2 bg-accent-primary hover:bg-accent-primary/80 text-white rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isDownloading && downloadFormat === "docx" ? (
              <>
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Downloading...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span>DOCX</span>
              </>
            )}
          </button>
          <button
            onClick={() => handleDownload("pdf")}
            disabled={isDownloading}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isDownloading && downloadFormat === "pdf" ? (
              <>
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Downloading...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
                <span>PDF</span>
              </>
            )}
          </button>
        </div>
      </div>
      
      {/* Report content */}
      <div className="prose prose-invert prose-sm max-w-none p-6 bg-background-secondary border border-zinc-700 rounded-lg">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {report}
        </ReactMarkdown>
      </div>
    </div>
  );
}



