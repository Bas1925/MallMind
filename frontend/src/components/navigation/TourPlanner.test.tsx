import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { TourPlanner } from "@/components/navigation/TourPlanner";
import { MAP_FIXTURE } from "@/test/fixtures";

function renderPlanner() {
  render(
    <TourPlanner
      locations={MAP_FIXTURE.locations}
      profile="normal"
      onProfile={vi.fn()}
      onApply={vi.fn()}
    />,
  );
  return screen.getByTestId("tour-search");
}

describe("TourPlanner stop picker", () => {
  it("adds the highlighted suggestion on Enter and clears the box", async () => {
    const user = userEvent.setup();
    const input = renderPlanner();
    await user.type(input, "Nike{Enter}");
    const stops = screen.getByTestId("tour-stops");
    expect(within(stops).getByText("Nike")).toBeInTheDocument();
    expect(input).toHaveValue("");
  });

  it("moves the highlight with the arrow keys", async () => {
    const user = userEvent.setup();
    const input = renderPlanner();
    await user.type(input, "e");
    const options = within(screen.getByRole("listbox")).getAllByRole("option");
    expect(options.length).toBeGreaterThan(1);
    const second = options[1]?.querySelector(".truncate")?.textContent ?? "";
    expect(options[1]).not.toHaveAttribute("aria-selected", "true");
    await user.keyboard("{ArrowDown}");
    expect(within(screen.getByRole("listbox")).getAllByRole("option")[1]).toHaveAttribute("aria-selected", "true");
    await user.keyboard("{Enter}");
    const stops = screen.getByTestId("tour-stops");
    expect(within(stops).getByText(second)).toBeInTheDocument();
  });
});
