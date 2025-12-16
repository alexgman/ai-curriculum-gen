"use client";

import dynamic from "next/dynamic";

// Dynamically import MainApp with SSR disabled to prevent hydration errors
// caused by browser extensions injecting HTML before React loads
const MainApp = dynamic(() => import("@/components/MainApp"), {
  ssr: false,
  loading: () => (
    <div className="flex h-screen bg-background-primary">
      <div className="flex-1 flex items-center justify-center">
        <div className="text-text-muted">Loading...</div>
      </div>
    </div>
  ),
});

export default function Home() {
  return <MainApp />;
}
