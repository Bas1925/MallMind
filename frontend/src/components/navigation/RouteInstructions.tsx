"use client";

import { Icon, type IconName } from "@/components/ui/Icon";

interface RouteInstructionsProps {
  instructions: string[];
}

function iconFor(step: string): IconName {
  const lower = step.toLowerCase();
  if (lower.startsWith("arrive") || lower.startsWith("already")) return "flag";
  if (lower.includes("elevator")) return "elevator";
  if (lower.includes("escalator")) return "escalator";
  if (lower.includes("stairs")) return "stairs";
  return "walk";
}

export function RouteInstructions({ instructions }: RouteInstructionsProps) {
  if (instructions.length === 0) return null;
  return (
    <ol data-testid="route-instructions" className="rise relative rounded-2xl border border-ink-600 bg-ink-850 p-4">
      {instructions.map((step, i) => {
        const last = i === instructions.length - 1;
        const icon = iconFor(step);
        return (
          <li key={`${i}-${step}`} className="relative flex gap-3 pb-4 last:pb-0">
            {!last ? (
              <span className="absolute start-[15px] top-8 h-[calc(100%-1.5rem)] w-px bg-ink-600" aria-hidden />
            ) : null}
            <span
              className={`relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${
                icon === "flag"
                  ? "border-gold-400/30 bg-gold-400 text-white"
                  : icon === "walk"
                    ? "border-ink-600 bg-ink-900 text-mist-300"
                    : "border-gold-400/25 bg-ink-900 text-gold-400"
              }`}
            >
              <Icon name={icon} size={15} />
            </span>
            <span className={`pt-1 text-[13px] leading-relaxed ${icon === "flag" ? "font-medium text-mist-50" : "text-mist-200"}`}>
              <span className="sr-only">{i + 1}. </span>
              {step}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
