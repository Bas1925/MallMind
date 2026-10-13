import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ParkingPanel } from "@/components/parking/ParkingPanel";
import { MAP_FIXTURE } from "@/test/fixtures";

describe("ParkingPanel", () => {
  it("saves the parking details and can route to the selected entrance", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    const baseLocation = MAP_FIXTURE.locations[0];
    if (baseLocation === undefined) throw new Error("Map fixture needs one location");
    const locations = [
      ...MAP_FIXTURE.locations,
      {
        ...baseLocation,
        id: "loc-parking",
        slug: "parking-entrance",
        name: "Parking Entrance B",
      },
    ];

    render(
      <ParkingPanel
        mallSlug="nova-mall"
        locations={locations}
        hasRouteOrigin
        onNavigate={onNavigate}
      />,
    );

    await user.type(screen.getByLabelText("Level *"), "P2");
    await user.type(screen.getByLabelText("Zone"), "Blue B");
    await user.type(screen.getByLabelText("Spot number"), "218");
    await user.click(screen.getByTestId("parking-save"));

    expect(screen.getByTestId("saved-parking")).toHaveTextContent("LevelP2");
    expect(screen.getByTestId("saved-parking")).toHaveTextContent("ZoneBlue B");
    expect(screen.getByTestId("saved-parking")).toHaveTextContent("Spot218");
    expect(screen.getByTestId("saved-parking")).toHaveTextContent("Directions end at the parking entrance");
    await user.click(screen.getByRole("button", { name: "Route to entrance" }));
    expect(onNavigate).toHaveBeenCalledWith("loc-parking");
  });

  it("shows validation instead of saving incomplete details", async () => {
    const user = userEvent.setup();
    render(
      <ParkingPanel
        mallSlug="nova-mall"
        locations={MAP_FIXTURE.locations}
        hasRouteOrigin={false}
        onNavigate={vi.fn()}
      />,
    );

    await user.click(screen.getByTestId("parking-save"));
    expect(screen.getByRole("status")).toHaveTextContent("Choose a parking level");
    expect(screen.queryByTestId("saved-parking")).not.toBeInTheDocument();
  });

  it("keeps the panel usable when the browser blocks local storage access", () => {
    const storage = vi.spyOn(window, "localStorage", "get").mockImplementation(() => {
      throw new DOMException("Access denied", "SecurityError");
    });

    try {
      render(
        <ParkingPanel
          mallSlug="nova-mall"
          locations={MAP_FIXTURE.locations}
          hasRouteOrigin={false}
          onNavigate={vi.fn()}
        />,
      );

      expect(screen.getByRole("status")).toHaveTextContent("This browser has blocked saved parking");
      expect(screen.getByLabelText("Level *")).toBeEnabled();
      expect(screen.queryByTestId("saved-parking")).not.toBeInTheDocument();
    } finally {
      storage.mockRestore();
    }
  });
});
