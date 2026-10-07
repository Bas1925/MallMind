"use client";

interface RouteInstructionsProps {
  instructions: string[];
}

export function RouteInstructions({ instructions }: RouteInstructionsProps) {
  if (instructions.length === 0) return null;
  return (
    <ol data-testid="route-instructions" className="space-y-2 text-sm text-stone-700">
      {instructions.map((step, i) => (
        <li key={`${i}-${step}`} className="flex gap-3">
          <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-stone-900 text-[10px] font-semibold text-white">
            {i + 1}
          </span>
          <span>{step}</span>
        </li>
      ))}
    </ol>
  );
}
