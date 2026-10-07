"use client";

import { Icon } from "@/components/ui/Icon";
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

export const PROFILE_OPTIONS = [
  ["normal", "Standard"],
  ["wheelchair", "Wheelchair"],
  ["avoid_stairs", "Avoid stairs"],
] as const;

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
      className="flex flex-col gap-4"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <div className="card relative flex gap-3 p-3">
        {/* From → To rail */}
        <div className="flex flex-col items-center pt-[1.15rem]" aria-hidden>
          <span className="h-2.5 w-2.5 rounded-full border-2 border-jade-400" />
          <span className="my-1 w-px flex-1 border-s border-dashed border-white/20" />
          <span className="h-2.5 w-2.5 rounded-full bg-rose-400" />
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <LocationSelect
            label="From"
            testId="from-select"
            placeholder="Choose a starting point"
            value={fromId}
            locations={locations}
            onChange={onFrom}
          />
          <LocationSelect
            label="To"
            testId="to-select"
            placeholder="Choose a destination"
            value={toId}
            locations={locations}
            onChange={onTo}
          />
        </div>
        <button
          type="button"
          aria-label="Swap start and destination"
          title="Swap"
          className="icon-btn self-center border border-white/[0.08] bg-ink-900"
          onClick={onSwap}
        >
          <Icon name="swap" size={15} />
        </button>
      </div>

      <fieldset className="flex flex-col gap-2">
        <legend className="eyebrow mb-2">Route profile</legend>
        <div className="flex flex-wrap gap-1.5">
          {PROFILE_OPTIONS.map(([value, label]) => (
            <label key={value} className={`chip ${profile === value ? "chip-active" : ""}`}>
              <input
                type="radio"
                name="profile"
                value={value}
                checked={profile === value}
                onChange={() => onProfile(value)}
                className="sr-only"
              />
              {value === "wheelchair" ? <Icon name="wheelchair" size={13} /> : null}
              {label}
            </label>
          ))}
        </div>
      </fieldset>

      <button
        type="submit"
        data-testid="route-submit"
        disabled={loading || fromId === "" || toId === ""}
        className="btn-primary"
      >
        <Icon name="route" size={16} />
        {loading ? "Finding route…" : "Show route"}
      </button>
    </form>
  );
}

function LocationSelect({
  label,
  testId,
  placeholder,
  value,
  locations,
  onChange,
}: {
  label: string;
  testId: string;
  placeholder: string;
  value: string;
  locations: MapLocation[];
  onChange: (id: string) => void;
}) {
  return (
    <label className="flex flex-col gap-0.5">
      <span className="eyebrow">{label}</span>
      <select
        data-testid={testId}
        className="w-full cursor-pointer truncate bg-transparent py-0.5 text-sm font-medium text-mist-50 outline-none"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">{placeholder}</option>
        {locations.map((loc) => (
          <option key={loc.id} value={loc.id}>
            {loc.name} · {loc.floor_name}
          </option>
        ))}
      </select>
    </label>
  );
}
