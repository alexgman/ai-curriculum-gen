"use client";

import { useState, useEffect } from "react";
import MainApp from "@/components/MainApp";

export default function Home() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Show loading until client-side mount to prevent hydration mismatch
  if (!mounted) {
    return (
      <div className="flex h-screen bg-background-primary">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-text-muted">Loading...</div>
        </div>
      </div>
    );
  }

  return <MainApp />;
}
