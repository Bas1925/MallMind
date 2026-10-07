"use client";

import type { MapLocation, RouteProfile } from "@/types/map";

interface RouteFormProps {
  locations: MapLocation[];
  fromId: string;
  toId: string;
  profile: RouteProfile;
  loading: boolean;
  onFrom: (id: string) => void;
  onTo: (id: string) => void;
  onProfile: (profile: RouteProfile) => void;
  onSubmit: () => void;
  onSwap: () => void;
}

export function RouteForm({
  locations,
  fromId,
  toId,
  profile,
  loading,
  onFrom,
  onTo,
  onProfile,
  onSubmit,
  onSwap,
}: RouteFormProps) {
  return (
    <form
      className="flex flex-col gap-3"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <label className="flex flex-col gap-1 text-xs font-medium text-stone-600">
        From
        <select
          data-testid="from-select"
          className="rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm text-stone-900"
          value={fromId}
          onChange={(event) => onFrom(event.target.value)}
        >
          <option value="">Select origin</option>
          {locations.map((loc) => (
            <option key={loc.id} value={loc.id}>
              {loc.name} · {loc.floor_name}
            </option>
          ))}
        </select>
      </label>
      <button
        type="button"
        className="self-start text-xs font-medium text-stone-500 underline-offset-2 hover:underline"
        onClick={onSwap}
      >
        Swap start and destination
      </button>
      <label className="flex flex-col gap-1 text-xs font-medium text-stone-600">
        To
        <select
          data-testid="to-select"
          className="rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm text-stone-900"
          value={toId}
          onChange={(event) => onTo(event.target.value)}
        >
          <option value="">Select destination</option>
          {locations.map((loc) => (
            <option key={loc.id} value={loc.id}>
              {loc.name} · {loc.floor_name}
            </option>
          ))}
        </select>
      </label>
      <fieldset className="flex flex-col gap-2">
        <legend className="text-xs font-medium text-stone-600">Route profile</legend>
        <div className="flex flex-wrap gap-1.5">
          {(
            [
              ["normal", "Standard"],
              ["wheelchair", "Wheelchair"],
              ["avoid_stairs", "Avoid stairs"],
            ] as const
          ).map(([value, label]) => (
            <label
              key={value}
              className={
                profile === value
                  ? "cursor-pointer rounded-full bg-stone-900 px-3 py-1.5 text-xs font-semibold text-white"
                  : "cursor-pointer rounded-full border border-stone-200 px-3 py-1.5 text-xs font-medium text-stone-600"
              }
            >
              <input
                type="radio"
                name="profile"
                value={value}
                checked={profile === value}
                onChange={() => onProfile(value)}
                className="sr-only"
              />
              {label}
            </label>
          ))}
        </div>
      </fieldset>
      <button
        type="submit"
        data-testid="route-submit"
        disabled={loading || fromId === "" || toId === ""}
        className="rounded-lg bg-orange-700 px-3 py-2 text-sm font-semibold text-white disabled:opacity-40"
      >
        {loading ? "Finding route…" : "Show route"}
      </button>
    </form>
  );
}
