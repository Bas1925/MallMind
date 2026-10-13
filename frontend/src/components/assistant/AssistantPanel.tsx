"use client";

import { useEffect, useRef, useState } from "react";
import { Icon } from "@/components/ui/Icon";
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
  const request = useRef<AbortController | null>(null);
  useEffect(() => () => request.current?.abort(), []);

  async function submit(text: string): Promise<void> {
    const trimmed = text.trim();
    if (trimmed === "" || pending) return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setPending(true);
    setReply(null);
    setError(null);
    try {
      const result = await askAssistant({
        message: trimmed,
        currentLocationId,
        profile,
      }, controller.signal);
      if (controller.signal.aborted) return;
      setReply(result);
      for (const action of result.actions) onAction(action);
    } catch (err) {
      if (controller.signal.aborted) return;
      setReply(null);
      setError(err instanceof Error ? err.message : "Assistant unavailable");
    } finally {
      if (!controller.signal.aborted) setPending(false);
    }
  }

  const direction = reply?.language === "ar" || reply?.language === "he" ? "rtl" : "ltr";

  return (
    <section className="space-y-4" data-testid="assistant-panel">
      <div className="card flex items-start gap-3 p-3.5">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-gold-300 to-gold-500 text-ink-950">
          <Icon name="sparkle" size={16} />
        </span>
        <div>
          <p className="text-sm font-semibold text-mist-50">Mall concierge</p>
          <p className="mt-0.5 text-xs leading-relaxed text-mist-400">
            Looking for something? Ask about stores, amenities, or directions in English, עברית or العربية.
          </p>
        </div>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {PROMPTS.map((prompt) => (
          <button
            key={prompt}
            type="button"
            disabled={pending}
            className="chip disabled:cursor-wait disabled:opacity-60"
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
        className="relative"
        onSubmit={(event) => {
          event.preventDefault();
          void submit(message);
        }}
      >
        <input
          data-testid="assistant-input"
          aria-label="Ask the mall concierge"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Ask anything — “Where is Nike?”"
          dir="auto"
          className="field pr-12"
        />
        <button
          type="submit"
          data-testid="assistant-submit"
          aria-label="Ask"
          disabled={pending || message.trim() === ""}
          className="absolute right-1.5 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-lg bg-gold-400 text-white transition hover:bg-gold-300 disabled:bg-ink-700 disabled:text-mist-500"
        >
          {pending ? (
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent motion-reduce:animate-none" />
          ) : (
            <Icon name="send" size={15} />
          )}
        </button>
      </form>
      {error !== null ? (
        <p
          data-testid="assistant-error"
          role="alert"
          className="rounded-xl border border-rose-400/30 bg-rose-400/10 px-3 py-2 text-sm text-rose-400"
        >
          {error}
        </p>
      ) : null}
      {reply !== null ? (
        <p
          data-testid="assistant-answer"
          dir={direction}
          lang={reply.language}
          role="status"
          className="rise rounded-2xl rounded-ss-md border border-ink-600 bg-ink-850 px-4 py-3 text-sm leading-relaxed text-mist-50"
        >
          {reply.answer}
        </p>
      ) : null}
    </section>
  );
}
