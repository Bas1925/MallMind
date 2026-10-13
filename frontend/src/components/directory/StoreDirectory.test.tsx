import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { StoreDirectory } from "./StoreDirectory";
import { MAP_FIXTURE } from "@/test/fixtures";

function setup(visitIds: string[] = []) {
  const onToggleVisit = vi.fn();
  const onOpenLocation = vi.fn();
  const onPlan = vi.fn();
  render(<StoreDirectory active locations={MAP_FIXTURE.locations} floors={MAP_FIXTURE.floors} visitIds={visitIds} onToggleVisit={onToggleVisit} onOpenLocation={onOpenLocation} onPlan={onPlan} onMap={vi.fn()} />);
  return { user: userEvent.setup(), onToggleVisit, onOpenLocation, onPlan };
}

describe("Store directory", () => {
  it("lists stores, not routing infrastructure", () => {
    setup();
    expect(screen.getAllByTestId("store-card")).toHaveLength(2);
    expect(screen.queryByRole("heading", { name: "Main Entrance" })).not.toBeInTheDocument();
  });
  it("combines category and floor filters and resets empty results", async () => {
    const { user } = setup();
    await user.click(within(screen.getByRole("group", { name: "Store categories" })).getByRole("button", { name: /Fashion/ }));
    await user.selectOptions(screen.getByLabelText("Filter by floor"), "1");
    expect(screen.getByRole("heading", { name: "No places found" })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Reset filters" }));
    expect(screen.getAllByTestId("store-card")).toHaveLength(2);
  });
  it("trims a case-insensitive query and can sort by floor", async () => {
    const { user } = setup();
    await user.type(screen.getByRole("searchbox", { name: "Search stores" }), "  nIkE  ");
    expect(screen.getAllByTestId("store-card")).toHaveLength(1);
    expect(screen.getByRole("heading", { name: "Nike" })).toBeInTheDocument();
    await user.clear(screen.getByRole("searchbox", { name: "Search stores" }));
    await user.selectOptions(screen.getByLabelText("Sort stores"), "floor");
    const first = screen.getAllByTestId("store-card")[0];
    if (first === undefined) throw new Error("Expected a store card");
    expect(within(first).getByRole("heading")).toHaveTextContent("Nike");
  });
  it("hands a store to the map using its actual ID", async () => {
    const { user, onOpenLocation } = setup();
    const nike = screen.getAllByTestId("store-card").find((card) => card.textContent?.includes("Nike"));
    if (nike === undefined) throw new Error("Expected Nike in the directory");
    await user.click(within(nike).getByRole("button", { name: "On the map" }));
    expect(onOpenLocation).toHaveBeenCalledWith("loc-nike", false);
  });
  it("exposes selected stops and sends the visit to the planner", async () => {
    const { user, onToggleVisit, onPlan } = setup(["loc-nike"]);
    expect(screen.getByRole("button", { name: "Remove Nike from my visit" })).toHaveAttribute("aria-pressed", "true");
    await user.click(screen.getByRole("button", { name: "Add Apple to my visit" }));
    expect(onToggleVisit).toHaveBeenCalledWith("loc-apple");
    await user.click(screen.getByRole("button", { name: "Plan my route" }));
    expect(onPlan).toHaveBeenCalledOnce();
  });
});
