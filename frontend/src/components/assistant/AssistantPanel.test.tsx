import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AssistantPanel } from "@/components/assistant/AssistantPanel";

describe("AssistantPanel", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("does not apply a late action after leaving the assistant", async () => {
    const user = userEvent.setup();
    const onAction = vi.fn();
    let finish: ((response: Response) => void) | undefined;
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>((resolve) => { finish = resolve; })));
    const { unmount } = render(
      <AssistantPanel profile="normal" currentLocationId={null} onAction={onAction} />,
    );
    await user.type(screen.getByTestId("assistant-input"), "Take me to Nike");
    await user.click(screen.getByTestId("assistant-submit"));
    unmount();
    await act(async () => { finish?.(new Response(JSON.stringify({
      answer: "Nike", language: "en", actions: [{ type: "highlight_location", location_id: "loc-nike" }],
    }))); });
    expect(onAction).not.toHaveBeenCalled();
  });

  it("applies a show_route action from the assistant response", async () => {
    const user = userEvent.setup();
    const onAction = vi.fn();
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            answer: "Main Entrance → Nike: 102 m, about 2 min.",
            language: "en",
            sources: [],
            actions: [
              {
                type: "show_route",
                from_location_id: "loc-entrance",
                to_location_id: "loc-nike",
                profile: "normal",
                floor_level: 0,
              },
            ],
            llm: "template",
            tools: ["search_locations", "calculate_route"],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    render(
      <AssistantPanel profile="normal" currentLocationId={null} onAction={onAction} />,
    );
    await user.type(screen.getByTestId("assistant-input"), "Take me to Nike");
    await user.click(screen.getByTestId("assistant-submit"));
    expect(await screen.findByTestId("assistant-answer")).toHaveTextContent("102 m");
    expect(onAction).toHaveBeenCalledWith(
      expect.objectContaining({ type: "show_route", to_location_id: "loc-nike" }),
    );
  });
});
