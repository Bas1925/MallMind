import type { SVGProps } from "react";

// Stroke icons on a 24-unit grid. Inline so the bundle needs no icon library.
const PATHS = {
  search: "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm10 2-4.35-4.35",
  swap: "M7 4v16M7 4 3 8m4-4 4 4m6 12V4m0 16-4-4m4 4 4-4",
  walk: "M13 4.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM9 21l2.5-6.5L14 17v4m-6.5-9.5L10 8l4 1 2 4m-6-5 1.5 6.5",
  elevator: "M5 3h14v18H5zM9.5 9 12 6.5 14.5 9M9.5 15l2.5 2.5 2.5-2.5",
  stairs: "M3 20h5v-5h5v-5h5V5h3",
  escalator: "M3 19h4l9-12h5M8 8.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z",
  flag: "M5 21V4m0 0h11l-2 4 2 4H5",
  pin: "M12 21s7-6.1 7-11.5A7 7 0 0 0 5 9.5C5 14.9 12 21 12 21Zm0-9a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z",
  route: "M6 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4Zm12-10a2 2 0 1 0 0-4 2 2 0 0 0 0 4ZM8 17h7.5a3.5 3.5 0 0 0 0-7h-7a3.5 3.5 0 0 1 0-7H16",
  list: "M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01",
  sparkle: "M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Zm7 13 .7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7L19 16Z",
  up: "m6 15 6-6 6 6",
  down: "m6 9 6 6 6-6",
  close: "M6 6l12 12M18 6 6 18",
  layers: "m12 3 9 5-9 5-9-5 9-5Zm-9 9 9 5 9-5M3 16l9 5 9-5",
  send: "M5 12h14m-6-6 6 6-6 6",
  wheelchair: "M11 4.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3ZM10 7v6h6l2 6m-8-9a5 5 0 1 0 5.5 7.5",
  clock: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Zm0-13v4l3 2",
  ruler: "M3 17 17 3l4 4L7 21l-4-4Zm4-4 2 2m2-6 2 2m2-6 2 2",
  car: "M5 17h14M6 17v2m12-2v2M4 13l2-5h12l2 5v4H4v-4Zm3.5 1h.01m9 0h.01M7 8l1-3h8l1 3",
} as const;

export type IconName = keyof typeof PATHS;

interface IconProps extends Omit<SVGProps<SVGSVGElement>, "name"> {
  name: IconName;
  size?: number;
}

export function Icon({ name, size = 16, ...rest }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      {...rest}
    >
      <path d={PATHS[name]} />
    </svg>
  );
}
