import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "AI Curriculum Builder",
  description: "AI-powered research and curriculum development tool",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        {/* Suppress browser extension errors and hydration warnings */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Suppress browser extension errors (MetaMask, etc.)
              window.addEventListener('error', function(e) {
                if (e.message && (
                  e.message.includes('MetaMask') ||
                  e.message.includes('ethereum') ||
                  e.message.includes('chrome-extension') ||
                  e.message.includes('extension') ||
                  e.message.includes('pronounceRootElement')
                )) {
                  e.preventDefault();
                  e.stopPropagation();
                  return true;
                }
              }, true);
              
              window.addEventListener('unhandledrejection', function(e) {
                if (e.reason && e.reason.message && (
                  e.reason.message.includes('MetaMask') ||
                  e.reason.message.includes('ethereum') ||
                  e.reason.message.includes('chrome-extension') ||
                  e.reason.message.includes('extension') ||
                  e.reason.message.includes('pronounceRootElement')
                )) {
                  e.preventDefault();
                  e.stopPropagation();
                  return true;
                }
              }, true);
              
              // Suppress hydration warnings from browser extensions
              const originalError = console.error;
              console.error = function(...args) {
                if (args[0] && typeof args[0] === 'string' && (
                  args[0].includes('Hydration') ||
                  args[0].includes('pronounceRootElement') ||
                  args[0].includes('suppressHydrationWarning')
                )) {
                  return;
                }
                originalError.apply(console, args);
              };
            `,
          }}
        />
      </head>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased bg-background-primary text-text-primary`}
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}

