import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { FloorSelector } from "@/components/map/FloorSelector";
import { MAP_FIXTURE } from "@/test/fixtures";

describe("FloorSelector", () => {
  it("changes the displayed floor", async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <FloorSelector
        floors={MAP_FIXTURE.floors}
        activeLevel={0}
        routeLevels={[0, 1]}
        onChange={onChange}
      />,
    );
    await user.click(screen.getByRole("tab", { name: "Level 1" }));
    expect(onChange).toHaveBeenCalledWith(1);
  });
});
