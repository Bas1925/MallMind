"use client";

import { useEffect, useMemo, useState } from "react";
import { Icon } from "@/components/ui/Icon";
import {
  clearParking,
  createParkingRecord,
  readParking,
  writeParking,
  type ParkingRecord,
} from "@/lib/parking";
import type { MapLocation } from "@/types/map";

interface ParkingPanelProps {
  mallSlug: string;
  locations: MapLocation[];
  hasRouteOrigin: boolean;
  onNavigate: (entranceLocationId: string) => void;
}

export function ParkingPanel({
  mallSlug,
  locations,
  hasRouteOrigin,
  onNavigate,
}: ParkingPanelProps) {
  const entrances = useMemo(
    () =>
      locations.filter(
        (location) =>
          location.slug.includes("parking") &&
          (location.category_slug === "entrance" || location.node_type === "entrance"),
      ),
    [locations],
  );
  const [saved, setSaved] = useState<ParkingRecord | null>(null);
  const [level, setLevel] = useState("");
  const [zone, setZone] = useState("");
  const [spot, setSpot] = useState("");
  const [note, setNote] = useState("");
  const [entranceId, setEntranceId] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const savedEntranceAvailable =
    saved?.entranceLocationId !== null &&
    entrances.some((entrance) => entrance.id === saved?.entranceLocationId);

  useEffect(() => {
    try {
      const record = readParking(window.localStorage, mallSlug);
      setSaved(record);
      setLevel(record?.level ?? "");
      setZone(record?.zone ?? "");
      setSpot(record?.spot ?? "");
      setNote(record?.note ?? "");
      setEntranceId(record?.entranceLocationId ?? "");
    } catch {
      setMessage("This browser has blocked saved parking. Allow local storage to remember your spot.");
    }
  }, [mallSlug]);

  useEffect(() => {
    if (entranceId === "" && entrances[0] !== undefined) setEntranceId(entrances[0].id);
  }, [entranceId, entrances]);

  const save = (): void => {
    try {
      const record = createParkingRecord({
        mallSlug,
        level,
        zone,
        spot,
        note,
        entranceLocationId: entranceId === "" ? null : entranceId,
      });
      writeParking(window.localStorage, record);
      setSaved(record);
      setLevel(record.level);
      setZone(record.zone);
      setSpot(record.spot);
      setNote(record.note);
      setMessage("Parking spot saved on this device.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Parking spot could not be saved.");
    }
  };

  const remove = (): void => {
    try {
      clearParking(window.localStorage);
      setSaved(null);
      setLevel("");
      setZone("");
      setSpot("");
      setNote("");
      setMessage("Saved parking spot cleared.");
    } catch {
      setMessage("Parking spot could not be cleared.");
    }
  };

  return (
    <section className="space-y-6" aria-labelledby="parking-title">
      <div className="parking-hero relative flex items-center gap-2 overflow-hidden rounded-2xl border border-gold-400/15 bg-gradient-to-br from-gold-400/[0.08] to-ink-900 px-4 py-5">
        <div className="relative z-10 min-w-0 flex-1">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-gold-400">Your way back</p>
          <h2 id="parking-title" className="text-[21px] font-semibold leading-tight tracking-[-0.6px] text-mist-50">
            Remember your parking
          </h2>
          <p className="mt-2 text-xs leading-relaxed text-mist-300">
            Save the details now. Find your way back after your visit.
          </p>
        </div>
        <ParkingTicketIllustration />
      </div>

      {saved !== null ? (
        <div className="parking-ticket card rise overflow-hidden !border-gold-400/25 !bg-gold-400/[0.04] !p-0" data-testid="saved-parking">
          <div className="flex items-center justify-between border-b border-dashed border-gold-400/25 px-4 py-3">
            <p className="text-xs font-semibold text-gold-400">Your saved spot</p>
            <span className="rounded border border-gold-400/30 px-1.5 py-0.5 text-[10px] font-bold text-gold-400" aria-hidden>P</span>
          </div>
          <div className="space-y-4 p-4">
            <dl className="grid grid-cols-3 gap-3">
              {[["Level", saved.level], ["Zone", saved.zone], ["Spot", saved.spot]].map(([label, value]) => (
                <div key={label} className="min-w-0">
                  <dt className="text-[11px] text-mist-400">{label}</dt>
                  <dd className="mt-1 break-words text-lg font-semibold tracking-tight text-mist-50">{value || "—"}</dd>
                </div>
              ))}
            </dl>
            {saved.note !== "" ? <p className="text-[13px] leading-relaxed text-mist-300">{saved.note}</p> : null}
            <p className="flex items-center gap-1.5 text-[11px] text-mist-500">
              <Icon name="clock" size={12} />
              Saved {new Date(saved.savedAt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                className="btn-primary min-w-0 flex-1"
                disabled={!savedEntranceAvailable}
                onClick={() => {
                  if (saved.entranceLocationId !== null) onNavigate(saved.entranceLocationId);
                }}
              >
                <Icon name="route" size={15} />
                {hasRouteOrigin ? "Route to entrance" : "Set destination"}
              </button>
              <button type="button" className="btn-ghost shrink-0" onClick={remove}>
                Clear
              </button>
            </div>
            <p className="text-xs leading-relaxed text-mist-400">
              Directions end at the parking entrance. Use your saved details to find your car inside the garage.
            </p>
            {!hasRouteOrigin ? (
              <p className="text-xs leading-relaxed text-mist-400">
                Choose your current location in Route to calculate directions back.
              </p>
            ) : null}
            {!savedEntranceAvailable ? (
              <p className="text-xs leading-relaxed text-amber-700">
                This parking entrance is no longer available on the current map. Update the saved spot.
              </p>
            ) : null}
          </div>
        </div>
      ) : null}

      <form
        className="space-y-4"
        onSubmit={(event) => {
          event.preventDefault();
          save();
        }}
      >
        <div>
          <h3 className="text-sm font-semibold text-mist-200">{saved === null ? "Parking details" : "Update your details"}</h3>
          <p className="mt-1 text-xs leading-relaxed text-mist-400">Add your level and either a zone or spot number.</p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <label className="flex flex-col gap-1.5 text-xs font-medium text-mist-300">
            <span>Level *</span>
            <input
              className="field min-h-11"
              aria-required="true"
              value={level}
              maxLength={32}
              placeholder="e.g. P2"
              autoComplete="off"
              onChange={(event) => setLevel(event.target.value)}
            />
          </label>
          <label className="flex flex-col gap-1.5 text-xs font-medium text-mist-300">
            <span>Zone</span>
            <input
              className="field min-h-11"
              value={zone}
              maxLength={32}
              placeholder="e.g. Blue B"
              autoComplete="off"
              onChange={(event) => setZone(event.target.value)}
            />
          </label>
          <label className="col-span-2 flex flex-col gap-1.5 text-xs font-medium text-mist-300">
            <span>Spot number</span>
            <input
              className="field min-h-11"
              value={spot}
              maxLength={32}
              placeholder="e.g. 218"
              autoComplete="off"
              onChange={(event) => setSpot(event.target.value)}
            />
          </label>
          <label className="col-span-2 flex flex-col gap-1.5 text-xs font-medium text-mist-300">
            <span>Entrance</span>
            <select
              className="field min-h-11"
              value={entranceId}
              onChange={(event) => setEntranceId(event.target.value)}
              disabled={entrances.length === 0}
            >
              {entrances.length === 0 ? <option value="">No mapped entrance</option> : null}
              {entrances.map((entrance) => (
                <option key={entrance.id} value={entrance.id}>
                  {entrance.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="flex flex-col gap-1.5 text-xs font-medium text-mist-300">
          <span>Note</span>
          <input
            className="field min-h-11"
            value={note}
            maxLength={160}
            placeholder="Near the elevator"
            autoComplete="off"
            onChange={(event) => setNote(event.target.value)}
          />
        </label>
        <button type="submit" className="btn-primary min-h-12" data-testid="parking-save">
          <Icon name="pin" size={15} />
          {saved === null ? "Save parking spot" : "Update parking spot"}
        </button>
        {message !== null ? (
          <p className="rounded-xl bg-ink-850 px-3.5 py-3 text-xs leading-relaxed text-mist-300" role="status">
            {message}
          </p>
        ) : null}
      </form>
      <p className="border-t border-ink-600 pt-4 text-xs leading-relaxed text-mist-500">
        Private to this device. Your parking details stay in this browser and are never uploaded.
      </p>
    </section>
  );
}

function ParkingTicketIllustration() {
  return (
    <svg
      viewBox="0 0 112 132"
      className="h-[128px] w-[86px] shrink-0 overflow-visible"
      fill="none"
      aria-hidden="true"
      focusable="false"
    >
      <ellipse cx="58" cy="119" rx="37" ry="6" fill="#174F49" fillOpacity="0.08" />
      <g className="parking-ticket-float">
        <g transform="translate(15 7) rotate(9 42 51)">
          <path d="M9 7H76L81 12V101L75 108H9L4 103V13L9 7Z" fill="#A2D7C7" />
          <rect x="1" y="2" width="74" height="101" rx="10" fill="white" stroke="#C5E4DB" />
          <path d="M11 2H65C70.523 2 75 6.477 75 12V49H1V12C1 6.477 5.477 2 11 2Z" fill="#197568" />
          <path d="M31 38V14H41C46 14 49 17 49 22C49 27 46 30 41 30H36V38H31ZM36 25H40C42.5 25 44 24 44 22C44 20 42.5 19 40 19H36V25Z" fill="white" />
          <path d="M11 60H64" stroke="#C5DCD5" strokeDasharray="3 4" />
          <rect x="14" y="71" width="31" height="4" rx="2" fill="#5C7F77" />
          <rect x="14" y="80" width="23" height="3" rx="1.5" fill="#D3E5DF" />
          <path d="M14 91H16M19 91H20M24 91H26M30 91H31M35 91H38M41 91H42" stroke="#71968B" strokeWidth="2" />
          <circle cx="59" cy="83" r="9" fill="#F6D8BB" />
          <path d="M55 83L58 86L63 80" stroke="#9A663B" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="1" cy="59" r="4" fill="#EFF8F4" />
          <circle cx="75" cy="59" r="4" fill="#EFF8F4" />
        </g>
      </g>
    </svg>
  );
}
