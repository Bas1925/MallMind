import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { LocationMarker } from "@/components/map/LocationMarker";
import { MAP_FIXTURE } from "@/test/fixtures";

describe("LocationMarker", () => {
  it("lets keyboard users select a store without clearing the map selection", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    const onClear = vi.fn();
    const location = MAP_FIXTURE.locations.find((item) => item.slug === "nike");
    if (location === undefined) throw new Error("Nike fixture missing");

    render(
      <svg onClick={onClear}>
        <LocationMarker
          location={location}
          bounds={{ minX: 0, minY: 0, maxX: 100, maxY: 100 }}
          selected={false}
          isStart={false}
          isEnd={false}
          stopNumber={null}
          onSelect={onSelect}
        />
      </svg>,
    );

    await user.tab();
    expect(screen.getByRole("button", { name: "Nike" })).toHaveFocus();
    await user.keyboard("{Enter}");
    await user.keyboard(" ");
    await user.click(screen.getByRole("button", { name: "Nike" }));
    expect(onSelect).toHaveBeenCalledTimes(3);
    expect(onSelect).toHaveBeenLastCalledWith(location.id);
    expect(onClear).not.toHaveBeenCalled();
  });
});
