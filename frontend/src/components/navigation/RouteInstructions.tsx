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
    <ol data-testid="route-instructions" className="rise relative space-y-1">
      {instructions.map((step, i) => {
        const last = i === instructions.length - 1;
        const icon = iconFor(step);
        return (
          <li key={`${i}-${step}`} className="relative flex gap-3 pb-3">
            {!last ? (
              <span className="absolute start-[15px] top-8 h-[calc(100%-1.5rem)] w-px bg-white/[0.08]" aria-hidden />
            ) : null}
            <span
              className={`relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border ${
                icon === "flag"
                  ? "border-rose-400/50 bg-rose-400/10 text-rose-400"
                  : icon === "walk"
                    ? "border-white/[0.08] bg-ink-800 text-mist-400"
                    : "border-gold-400/40 bg-gold-400/10 text-gold-300"
              }`}
            >
              <Icon name={icon} size={15} />
            </span>
            <span className="pt-1.5 text-sm text-mist-200">
              <span className="sr-only">{i + 1}. </span>
              {step}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
