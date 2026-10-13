import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StoreBrand, STORE_BRANDS } from "./StoreBrand";

describe("StoreBrand", () => {
  it.each(Object.entries(STORE_BRANDS))("uses a local asset for %s", (slug, source) => {
    render(<StoreBrand slug={slug} name="Store" />);
    const image = screen.getByRole("img", { name: "Store logo" });
    const url = new URL(image.getAttribute("src") ?? "", window.location.href);
    expect(url.origin).toBe(window.location.origin);
    expect(url.pathname).toBe(source);
    expect(source).toMatch(/^\/brands\/[a-z-]+\.(svg|png)$/);
  });

  it("keeps fictional and unknown brands as text", () => {
    render(<StoreBrand slug="nova-cinema" name="NOVA Cinema" />);
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByText("NOVA Cinema")).toBeInTheDocument();
  });

  it("falls back to the store name if an image fails", () => {
    render(<StoreBrand slug="nike" name="Nike" />);
    fireEvent.error(screen.getByRole("img", { name: "Nike logo" }));
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(screen.getByText("Nike")).toBeInTheDocument();
  });

  it("does not let an old image error hide another brand", () => {
    const { rerender } = render(<StoreBrand slug="nike" name="Nike" />);
    fireEvent.error(screen.getByRole("img"));
    rerender(<StoreBrand slug="apple" name="Apple" />);
    expect(screen.getByRole("img", { name: "Apple logo" })).toBeInTheDocument();
  });
});
