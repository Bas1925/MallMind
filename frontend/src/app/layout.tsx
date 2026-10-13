import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import type { ReactNode } from "react";
import "./globals.css";
import "./directory.css";

const sans = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });

export const metadata: Metadata = {
  metadataBase: new URL(process.env["SITE_URL"] ?? "http://localhost:3000"),
  title: "MallMind — Discover NOVA Mall",
  description: "Find your way around NOVA Mall. Explore stores, plan your visit, and remember your parking spot.",
  applicationName: "MallMind",
  openGraph: {
    title: "MallMind — A better way around",
    description: "Explore an interactive demo mall, find accessible routes, and plan a smarter shopping trip.",
    type: "website",
    locale: "en_US",
  },
  twitter: { card: "summary_large_image" },
};

export const viewport: Viewport = {
  themeColor: "#f6f7f4",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={sans.variable}>
      <body className="min-h-dvh bg-ink-950 text-mist-50 antialiased">{children}</body>
    </html>
  );
}
