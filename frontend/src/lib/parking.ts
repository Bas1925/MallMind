export const PARKING_STORAGE_KEY = "mallmind.parking.v1";

export interface ParkingRecord {
  version: 1;
  mallSlug: string;
  level: string;
  zone: string;
  spot: string;
  note: string;
  entranceLocationId: string | null;
  savedAt: string;
}

export interface ParkingInput {
  mallSlug: string;
  level: string;
  zone: string;
  spot: string;
  note: string;
  entranceLocationId: string | null;
}

type StorageReader = Pick<Storage, "getItem">;
type StorageWriter = Pick<Storage, "setItem" | "removeItem">;

const LIMITS = {
  level: 32,
  zone: 32,
  spot: 32,
  note: 160,
} as const;

export function readParking(storage: StorageReader, mallSlug: string): ParkingRecord | null {
  try {
    const raw = storage.getItem(PARKING_STORAGE_KEY);
    if (raw === null) return null;
    const value: unknown = JSON.parse(raw);
    if (!isParkingRecord(value) || value.mallSlug !== mallSlug) return null;
    return value;
  } catch {
    return null;
  }
}

export function createParkingRecord(input: ParkingInput, now = new Date()): ParkingRecord {
  const level = clean(input.level, LIMITS.level);
  const zone = clean(input.zone, LIMITS.zone);
  const spot = clean(input.spot, LIMITS.spot);
  const note = clean(input.note, LIMITS.note);

  if (level === "") throw new Error("Choose a parking level.");
  if (zone === "" && spot === "") throw new Error("Add a zone or spot number.");

  return {
    version: 1,
    mallSlug: input.mallSlug,
    level,
    zone,
    spot,
    note,
    entranceLocationId: input.entranceLocationId,
    savedAt: now.toISOString(),
  };
}

export function writeParking(storage: StorageWriter, record: ParkingRecord): void {
  storage.setItem(PARKING_STORAGE_KEY, JSON.stringify(record));
}

export function clearParking(storage: StorageWriter): void {
  storage.removeItem(PARKING_STORAGE_KEY);
}

function clean(value: string, maxLength: number): string {
  return value.trim().replace(/\s+/g, " ").slice(0, maxLength);
}

function isParkingRecord(value: unknown): value is ParkingRecord {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    record["version"] === 1 &&
    isBoundedString(record["mallSlug"], 1, 64) &&
    isBoundedString(record["level"], 1, LIMITS.level) &&
    isBoundedString(record["zone"], 0, LIMITS.zone) &&
    isBoundedString(record["spot"], 0, LIMITS.spot) &&
    (record["zone"].length > 0 || record["spot"].length > 0) &&
    isBoundedString(record["note"], 0, LIMITS.note) &&
    (isBoundedString(record["entranceLocationId"], 1, 64) ||
      record["entranceLocationId"] === null) &&
    typeof record["savedAt"] === "string" &&
    !Number.isNaN(Date.parse(record["savedAt"]))
  );
}

function isBoundedString(value: unknown, minLength: number, maxLength: number): value is string {
  return typeof value === "string" && value.length >= minLength && value.length <= maxLength;
}
