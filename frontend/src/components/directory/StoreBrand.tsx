"use client";

import Image from "next/image";
import { useState } from "react";

// Explicit slugs prevent a similarly named demo store from receiving a real brand's logo.
// Source and modification records are in docs/brand-assets.md.
export const STORE_BRANDS: Readonly<Record<string, string>> = {
  adidas: "/brands/adidas.svg",
  apple: "/brands/apple.svg",
  hm: "/brands/handm.svg",
  muji: "/brands/muji.png",
  mcdonalds: "/brands/mcdonalds.svg",
  nike: "/brands/nike.svg",
  samsung: "/brands/samsung.svg",
  starbucks: "/brands/starbucks.svg",
  "super-pharm": "/brands/super-pharm.png",
  zara: "/brands/zara.svg",
};

export function StoreBrand({ slug, name }: { slug: string; name: string }) {
  const [failedSlug, setFailedSlug] = useState<string | null>(null);
  const source = STORE_BRANDS[slug];
  if (source === undefined || failedSlug === slug) {
    return <span className="store-brand-fallback">{name}</span>;
  }
  return (
    <Image
      className={`store-brand-logo brand-${slug}`}
      data-brand-logo={slug}
      src={source}
      alt={`${name} logo`}
      width={180}
      height={88}
      unoptimized
      onError={() => setFailedSlug(slug)}
    />
  );
}
