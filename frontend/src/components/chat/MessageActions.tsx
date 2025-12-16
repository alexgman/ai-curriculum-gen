"use client";

import { useState } from "react";

interface MessageActionsProps {
  content: string;
  messageId: string;
}

export function MessageActions({ content, messageId }: MessageActionsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Professional markdown to HTML converter
  const convertMarkdownToHtml = (markdown: string): string => {
    let html = markdown;
    
    // Process tables first (more complex)
    html = processMarkdownTables(html);
    
    // Headers with proper styling - process from most # to least # to avoid conflicts
    html = html.replace(/^###### (.*$)/gim, '<h6 class="sub-sub-header">$1</h6>');
    html = html.replace(/^##### (.*$)/gim, '<h5 class="sub-sub-header">$1</h5>');
    html = html.replace(/^#### (.*$)/gim, '<h4 class="sub-section-header">$1</h4>');
    html = html.replace(/^### (.*$)/gim, '<h3 class="section-header">$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2 class="main-header">$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1 class="title-header">$1</h1>');
    
    // Bold and italic
    html = html.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="link">$1</a>');
    
    // Blockquotes
    html = html.replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>');
    
    // Horizontal rules
    html = html.replace(/^---$/gim, '<hr class="section-divider">');
    html = html.replace(/^___$/gim, '<hr class="section-divider">');
    
    // Process lists
    html = processMarkdownLists(html);
    
    // Paragraphs - wrap loose text in p tags
    html = html.split('\n').map(line => {
      const trimmed = line.trim();
      if (!trimmed) return '<br>';
      if (trimmed.startsWith('<')) return line; // Already HTML
      return `<p>${line}</p>`;
    }).join('\n');
    
    // Clean up
    html = html.replace(/<br>\s*<br>\s*<br>/g, '<br><br>');
    html = html.replace(/<p><\/p>/g, '');
    html = html.replace(/<p>\s*<\/p>/g, '');
    
    return html;
  };

  const processMarkdownTables = (text: string): string => {
    const lines = text.split('\n');
    let result: string[] = [];
    let inTable = false;
    let tableRows: string[] = [];
    let headerProcessed = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      if (line.startsWith('|') && line.endsWith('|')) {
        if (!inTable) {
          inTable = true;
          tableRows = [];
          headerProcessed = false;
        }
        
        // Check if separator row
        const isSeparator = line.match(/^\|[\s\-:|]+\|$/);
        
        if (isSeparator) {
          // Mark that header is done
          headerProcessed = true;
          continue;
        }
        
        // Parse cells
        const cells = line.split('|').filter(c => c.trim()).map(c => c.trim());
        
        if (!headerProcessed) {
          // This is header row
          tableRows.push(`<thead><tr>${cells.map(c => `<th>${c}</th>`).join('')}</tr></thead><tbody>`);
        } else {
          // Body row
          tableRows.push(`<tr>${cells.map(c => `<td>${c}</td>`).join('')}</tr>`);
        }
      } else {
        if (inTable) {
          // End of table
          result.push(`<table class="data-table">${tableRows.join('')}</tbody></table>`);
          inTable = false;
          tableRows = [];
        }
        result.push(line);
      }
    }
    
    // Handle table at end of content
    if (inTable) {
      result.push(`<table class="data-table">${tableRows.join('')}</tbody></table>`);
    }
    
    return result.join('\n');
  };

  const processMarkdownLists = (text: string): string => {
    const lines = text.split('\n');
    let result: string[] = [];
    let inList = false;
    let listItems: string[] = [];
    let listType: 'ul' | 'ol' = 'ul';
    
    for (const line of lines) {
      const unorderedMatch = line.match(/^(\s*)[-*]\s+(.*)$/);
      const orderedMatch = line.match(/^(\s*)\d+\.\s+(.*)$/);
      
      if (unorderedMatch || orderedMatch) {
        if (!inList) {
          inList = true;
          listItems = [];
          listType = orderedMatch ? 'ol' : 'ul';
        }
        const content = unorderedMatch ? unorderedMatch[2] : orderedMatch![2];
        listItems.push(`<li>${content}</li>`);
      } else {
        if (inList) {
          result.push(`<${listType} class="styled-list">${listItems.join('')}</${listType}>`);
          inList = false;
          listItems = [];
        }
        result.push(line);
      }
    }
    
    if (inList) {
      result.push(`<${listType} class="styled-list">${listItems.join('')}</${listType}>`);
    }
    
    return result.join('\n');
  };

  const getDocumentStyles = () => `
    @page {
      margin: 1in;
      size: letter;
    }
    
    body {
      font-family: 'Segoe UI', Calibri, Arial, sans-serif;
      font-size: 11pt;
      line-height: 1.6;
      color: #1a1a1a;
      max-width: 8.5in;
      margin: 0 auto;
      padding: 0.5in;
    }
    
    .title-header {
      font-size: 22pt;
      font-weight: 700;
      color: #1e3a5f;
      margin: 0 0 24pt 0;
      padding-bottom: 12pt;
      border-bottom: 3px solid #4f46e5;
    }
    
    .main-header {
      font-size: 16pt;
      font-weight: 600;
      color: #1e3a5f;
      margin: 24pt 0 12pt 0;
      padding-bottom: 6pt;
      border-bottom: 1px solid #e5e7eb;
    }
    
    .section-header {
      font-size: 13pt;
      font-weight: 600;
      color: #374151;
      margin: 18pt 0 8pt 0;
    }
    
    .sub-section-header {
      font-size: 12pt;
      font-weight: 600;
      color: #4b5563;
      margin: 14pt 0 6pt 0;
    }
    
    .sub-sub-header {
      font-size: 11pt;
      font-weight: 600;
      color: #6b7280;
      margin: 10pt 0 4pt 0;
    }
    
    h4, h5, h6 {
      page-break-after: avoid;
    }
    
    .data-table {
      width: 100%;
      border-collapse: collapse;
      margin: 12pt 0;
      font-size: 10pt;
    }
    
    .data-table th {
      background-color: #4f46e5;
      color: white;
      font-weight: 600;
      padding: 10pt 12pt;
      text-align: left;
      border: 1px solid #4338ca;
    }
    
    .data-table td {
      padding: 8pt 12pt;
      border: 1px solid #e5e7eb;
      vertical-align: top;
    }
    
    .data-table tr:nth-child(even) td {
      background-color: #f9fafb;
    }
    
    .data-table tr:hover td {
      background-color: #eef2ff;
    }
    
    .styled-list {
      margin: 8pt 0;
      padding-left: 24pt;
    }
    
    .styled-list li {
      margin: 4pt 0;
      padding-left: 4pt;
    }
    
    blockquote {
      margin: 12pt 0;
      padding: 12pt 16pt;
      background: linear-gradient(to right, #eef2ff, #f9fafb);
      border-left: 4px solid #4f46e5;
      border-radius: 0 4pt 4pt 0;
      font-style: italic;
      color: #4b5563;
    }
    
    .section-divider {
      border: none;
      height: 2px;
      background: linear-gradient(to right, #4f46e5, #e5e7eb);
      margin: 24pt 0;
    }
    
    .link {
      color: #4f46e5;
      text-decoration: none;
    }
    
    .link:hover {
      text-decoration: underline;
    }
    
    strong {
      font-weight: 600;
      color: #1f2937;
    }
    
    p {
      margin: 6pt 0;
    }
    
    /* Course card styling */
    .course-entry {
      margin: 16pt 0;
      padding: 12pt;
      border: 1px solid #e5e7eb;
      border-radius: 4pt;
      background: #fafafa;
    }
    
    /* Print optimization */
    @media print {
      body {
        padding: 0;
      }
      
      .data-table {
        page-break-inside: avoid;
      }
      
      h1, h2, h3, h4, h5, h6 {
        page-break-after: avoid;
      }
      
      .section-divider {
        background: #4f46e5;
      }
    }
  `;

  const handleDownloadWord = () => {
    const htmlContent = convertMarkdownToHtml(content);
    const timestamp = new Date().toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
    
    const wordDoc = `
      <!DOCTYPE html>
      <html xmlns:o='urn:schemas-microsoft-com:office:office' 
            xmlns:w='urn:schemas-microsoft-com:office:word'
            xmlns='http://www.w3.org/TR/REC-html40'>
        <head>
          <meta charset="utf-8">
          <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
          <title>Competitor Research Report</title>
          <!--[if gte mso 9]>
          <xml>
            <w:WordDocument>
              <w:View>Print</w:View>
              <w:Zoom>100</w:Zoom>
              <w:DoNotOptimizeForBrowser/>
            </w:WordDocument>
          </xml>
          <![endif]-->
          <style>
            ${getDocumentStyles()}
          </style>
        </head>
        <body>
          <div class="document-header" style="text-align: right; font-size: 9pt; color: #6b7280; margin-bottom: 24pt;">
            Generated: ${timestamp}
          </div>
          ${htmlContent}
        </body>
      </html>
    `;
    
    const blob = new Blob(['\ufeff' + wordDoc], { 
      type: 'application/msword;charset=utf-8' 
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Competitor-Research-${messageId.slice(0, 8)}.doc`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDownloadPDF = () => {
    const htmlContent = convertMarkdownToHtml(content);
    const timestamp = new Date().toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
    
    const printWindow = window.open("", "_blank");
    if (printWindow) {
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="utf-8">
            <title>Competitor Research Report</title>
            <style>
              ${getDocumentStyles()}
            </style>
          </head>
          <body>
            <div style="text-align: right; font-size: 9pt; color: #6b7280; margin-bottom: 24pt;">
              Generated: ${timestamp}
            </div>
            ${htmlContent}
            <script>
              setTimeout(() => window.print(), 500);
            </script>
          </body>
        </html>
      `);
      printWindow.document.close();
    }
  };

  return (
    <div className="flex items-center gap-1 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
      {/* Copy Button */}
      <button
        onClick={handleCopy}
        className="p-1.5 rounded-lg hover:bg-background-tertiary transition-colors"
        title="Copy"
      >
        {copied ? (
          <svg
            className="w-4 h-4 text-green-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        ) : (
          <svg
            className="w-4 h-4 text-text-muted"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
        )}
      </button>

      {/* Download Word */}
      <button
        onClick={handleDownloadWord}
        className="p-1.5 rounded-lg hover:bg-background-tertiary transition-colors flex items-center gap-1"
        title="Download as Word Document"
      >
        <svg
          className="w-4 h-4 text-text-muted"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <span className="text-xs text-text-muted">.doc</span>
      </button>

      {/* Download PDF */}
      <button
        onClick={handleDownloadPDF}
        className="p-1.5 rounded-lg hover:bg-background-tertiary transition-colors flex items-center gap-1"
        title="Download as PDF"
      >
        <svg
          className="w-4 h-4 text-text-muted"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <span className="text-xs text-text-muted">.pdf</span>
      </button>
    </div>
  );
}
