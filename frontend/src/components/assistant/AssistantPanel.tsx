"use client";

import { useState } from "react";
import { askAssistant } from "@/lib/api";
import type { AssistantAction, AssistantResponse } from "@/types/assistant";
import type { RouteProfile } from "@/types/map";

interface AssistantPanelProps {
  profile: RouteProfile;
  currentLocationId: string | null;
  onAction: (action: AssistantAction) => void;
}

const PROMPTS = [
  "Where is Nike?",
  "Nearest bathroom",
  "Wheelchair route to Nike",
  "Where is an ATM?",
  "Where did I start?",
  "Take me to Nike",
] as const;

export function AssistantPanel({ profile, currentLocationId, onAction }: AssistantPanelProps) {
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reply, setReply] = useState<AssistantResponse | null>(null);

  async function submit(text: string): Promise<void> {
    const trimmed = text.trim();
    if (trimmed === "") return;
    setPending(true);
    setError(null);
    try {
      const result = await askAssistant({
        message: trimmed,
        currentLocationId,
        profile,
      });
      setReply(result);
      for (const action of result.actions) onAction(action);
    } catch (err) {
      setReply(null);
      setError(err instanceof Error ? err.message : "Assistant unavailable");
    } finally {
      setPending(false);
    }
  }

  const direction = reply?.language === "ar" || reply?.language === "he" ? "rtl" : "ltr";

  return (
    <section className="space-y-3" data-testid="assistant-panel">
      <p className="text-xs text-stone-500">
        Answers use mall search and the routing engine. If the model is offline, you still get the
        facts.
      </p>
      <div className="flex flex-wrap gap-1.5">
        {PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            className="rounded-full border border-stone-200 px-2.5 py-1 text-xs text-stone-700 hover:bg-stone-50"
            onClick={() => {
              setMessage(prompt);
              void submit(prompt);
            }}
          >
            {prompt}
          </button>
        ))}
      </div>
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void submit(message);
        }}
      >
        <input
          data-testid="assistant-input"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Where is Nike?"
          className="min-w-0 flex-1 rounded-lg border border-stone-200 px-3 py-2 text-sm"
        />
        <button
          type="submit"
          data-testid="assistant-submit"
          disabled={pending || message.trim() === ""}
          className="rounded-lg bg-stone-900 px-3 py-2 text-sm font-semibold text-white disabled:opacity-40"
        >
          {pending ? "…" : "Ask"}
        </button>
      </form>
      {error !== null ? (
        <p data-testid="assistant-error" className="text-sm text-red-800">
          {error}
        </p>
      ) : null}
      {reply !== null ? (
        <p
          data-testid="assistant-answer"
          dir={direction}
          lang={reply.language}
          className="rounded-lg bg-stone-50 px-3 py-2 text-sm text-stone-800"
        >
          {reply.answer}
        </p>
      ) : null}
    </section>
  );
}
