import { describe, expect, it } from "vitest";
import {
  PARKING_STORAGE_KEY,
  clearParking,
  createParkingRecord,
  readParking,
  writeParking,
} from "@/lib/parking";

describe("parking storage", () => {
  it("normalizes, persists, and restores a parking record", () => {
    const record = createParkingRecord(
      {
        mallSlug: "nova-mall",
        level: "  P2  ",
        zone: " Blue   B ",
        spot: " 218 ",
        note: " Near   elevator ",
        entranceLocationId: "loc-parking",
      },
      new Date("2026-10-09T08:00:00.000Z"),
    );

    writeParking(localStorage, record);

    expect(readParking(localStorage, "nova-mall")).toEqual({
      version: 1,
      mallSlug: "nova-mall",
      level: "P2",
      zone: "Blue B",
      spot: "218",
      note: "Near elevator",
      entranceLocationId: "loc-parking",
      savedAt: "2026-10-09T08:00:00.000Z",
    });
  });

  it("ignores corrupt, unknown-mall, and incomplete records", () => {
    localStorage.setItem(PARKING_STORAGE_KEY, "not json");
    expect(readParking(localStorage, "nova-mall")).toBeNull();

    const record = createParkingRecord({
      mallSlug: "another-mall",
      level: "P1",
      zone: "A",
      spot: "",
      note: "",
      entranceLocationId: null,
    });
    writeParking(localStorage, record);
    expect(readParking(localStorage, "nova-mall")).toBeNull();
  });

  it("requires a level and either a zone or a spot", () => {
    expect(() =>
      createParkingRecord({
        mallSlug: "nova-mall",
        level: "",
        zone: "A",
        spot: "",
        note: "",
        entranceLocationId: null,
      }),
    ).toThrow("Choose a parking level");

    expect(() =>
      createParkingRecord({
        mallSlug: "nova-mall",
        level: "P1",
        zone: "",
        spot: "",
        note: "",
        entranceLocationId: null,
      }),
    ).toThrow("Add a zone or spot number");
  });

  it("removes the saved record", () => {
    localStorage.setItem(PARKING_STORAGE_KEY, "saved");
    clearParking(localStorage);
    expect(localStorage.getItem(PARKING_STORAGE_KEY)).toBeNull();
  });
});
