interface StoreMarkProps {
  slug: string;
  name: string;
  size?: number;
}

interface Mark {
  paper: string;
  ink: string;
  letters: string;
}

const MARKS: Record<string, Mark> = {
  nike: { paper: "#1f3d34", ink: "#e7f6ef", letters: "NK" },
  zara: { paper: "#2c2c2c", ink: "#f4f1ea", letters: "ZA" },
  hm: { paper: "#8f2d2d", ink: "#fff4f1", letters: "H&M" },
  adidas: { paper: "#1d3550", ink: "#e7f0f8", letters: "AD" },
  muji: { paper: "#8a5a3b", ink: "#f8f1e8", letters: "MJ" },
  apple: { paper: "#243044", ink: "#eef3f8", letters: "AP" },
  samsung: { paper: "#163a63", ink: "#e7f1fb", letters: "SG" },
  starbucks: { paper: "#1e4d3a", ink: "#e7f6ee", letters: "SB" },
  mcdonalds: { paper: "#8a4b16", ink: "#fff3e4", letters: "MC" },
  "pizza-napoli": { paper: "#7a3030", ink: "#fdeeee", letters: "PN" },
  "sushi-kaito": { paper: "#1f4a52", ink: "#e7f4f6", letters: "SK" },
  "rooftop-cafe": { paper: "#5c4632", ink: "#f8f1e6", letters: "RC" },
  "super-pharm": { paper: "#1f5c4a", ink: "#e7f7f1", letters: "SP" },
  "guest-services": { paper: "#3d4a63", ink: "#eef2f8", letters: "GS" },
  "nova-cinema": { paper: "#3a3158", ink: "#f1eef8", letters: "NC" },
  "pages-bookstore": { paper: "#4a3b2a", ink: "#f7f1e8", letters: "PB" },
};

export function StoreMark({ slug, name, size = 72 }: StoreMarkProps) {
  const mark = MARKS[slug] ?? fallbackMark(name);
  return (
    <svg className="store-mark" width={size} height={size} viewBox="0 0 64 64" aria-hidden>
      <rect width="64" height="64" rx="14" fill={mark.paper} />
      <rect x="6" y="6" width="52" height="52" rx="10" fill="none" stroke={mark.ink} strokeOpacity="0.35" />
      <text
        x="32"
        y="38"
        textAnchor="middle"
        fill={mark.ink}
        style={{ fontSize: mark.letters.length > 2 ? 16 : 20, fontWeight: 700, letterSpacing: -0.4 }}
      >
        {mark.letters}
      </text>
    </svg>
  );
}

function fallbackMark(name: string): Mark {
  const letters = name
    .split(/\s+/)
    .map((word) => word[0] ?? "")
    .join("")
    .slice(0, 2)
    .toUpperCase();
  return { paper: "#31493c", ink: "#f3f7f4", letters: letters === "" ? "•" : letters };
}
