import { ImageResponse } from "next/og";

export const alt = "MallMind — indoor navigation, accessible routes, and smarter shopping trips";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    <div style={{ display: "flex", width: "100%", height: "100%", background: "#f6f7f4", color: "#203a32", padding: 72, flexDirection: "column", justifyContent: "space-between" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
        <div style={{ display: "flex", width: 66, height: 66, alignItems: "center", justifyContent: "center", background: "#176b52", color: "white", borderRadius: 18, fontSize: 36 }}>M</div>
        <div style={{ fontSize: 34, fontWeight: 700 }}>mallmind.</div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
        <div style={{ fontSize: 76, fontWeight: 700, letterSpacing: -3 }}>A better way around.</div>
        <div style={{ fontSize: 29, color: "#526c5e" }}>Find your next stop. Plan your visit. Remember your parking.</div>
      </div>
      <div style={{ display: "flex", gap: 18, fontSize: 22 }}>
        {["Interactive mall map", "Accessible routes", "Multilingual search"].map((label) => (
          <div key={label} style={{ background: "#e2eee5", borderRadius: 24, padding: "12px 20px" }}>{label}</div>
        ))}
      </div>
    </div>,
    size,
  );
}
