import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LocationSearch } from "./LocationSearch";
import { MAP_FIXTURE } from "@/test/fixtures";

afterEach(() => vi.unstubAllGlobals());

describe("LocationSearch", () => {
  it("supports keyboard selection and dismisses suggestions with Escape", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({ results: [] }))));
    const pick = vi.fn();
    const user = userEvent.setup();
    render(<LocationSearch locations={MAP_FIXTURE.locations} onPick={pick} />);
    const input = screen.getByRole("combobox");
    await user.type(input, "Nike");
    expect(input).toHaveAttribute("aria-expanded", "true");
    await user.keyboard("{Escape}");
    expect(input).toHaveAttribute("aria-expanded", "false");
    await user.keyboard("{ArrowDown}{Enter}");
    expect(pick).toHaveBeenCalledWith("loc-nike");
    expect(input).toHaveValue("");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });

  it("does not restore stale server results after the query is cleared", async () => {
    let finish: ((response: Response) => void) | undefined;
    const fetchMock = vi.fn(() => new Promise<Response>((resolve) => { finish = resolve; }));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<LocationSearch locations={MAP_FIXTURE.locations} onPick={vi.fn()} />);
    const input = screen.getByRole("combobox");
    await user.type(input, "coffee");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    await user.clear(input);
    await act(async () => { finish?.(new Response(JSON.stringify({ results: [{
      location_id: "old", name: "Old result", category: "Food", floor: "Ground", category_slug: "food",
    }] }))); });
    expect(screen.queryByText("Old result")).not.toBeInTheDocument();
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
  });
});
