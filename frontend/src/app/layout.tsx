import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "MallMind — NOVA Mall map",
  description: "Indoor mall navigation with a real A* route on an SVG floor map.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-dvh bg-stone-100 text-stone-900 antialiased">{children}</body>
    </html>
  );
}
