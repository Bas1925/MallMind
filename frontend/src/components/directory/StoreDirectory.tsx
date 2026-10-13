"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { MallAtrium } from "./MallAtrium";
import { StoreBrand } from "./StoreBrand";
import { Icon } from "@/components/ui/Icon";
import type { MapFloor, MapLocation } from "@/types/map";

interface Props {
  active: boolean;
  locations: MapLocation[];
  floors: MapFloor[];
  visitIds: string[];
  onToggleVisit: (id: string) => void;
  onOpenLocation: (id: string, navigate: boolean) => void;
  onPlan: () => void;
  onMap: () => void;
}
const CATEGORY_LABELS: Record<string, string> = { fashion: "Fashion", food: "Food & drink", electronics: "Technology", services: "Lifestyle & more" };
const categoryLabel = (slug: string, fallback: string) => CATEGORY_LABELS[slug] ?? fallback;
const normalize = (text: string) => text.normalize("NFKD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();

export function StoreDirectory({ active, locations, floors, visitIds, onToggleVisit, onOpenLocation, onPlan, onMap }: Props) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [floor, setFloor] = useState("all");
  const [sort, setSort] = useState("az");
  const [selected, setSelected] = useState<MapLocation | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const stores = useMemo(() => locations.filter((loc) => loc.node_type === "store_anchor"), [locations]);
  const categories = useMemo(() => Array.from(new Map(stores.map((loc) =>
    [loc.category_slug, categoryLabel(loc.category_slug, loc.category_name)])).entries()).sort((a, b) => a[1].localeCompare(b[1])), [stores]);
  const filtered = useMemo(() => stores.filter((loc) =>
    (category === "all" || loc.category_slug === category) &&
    (floor === "all" || String(loc.floor_level) === floor) &&
    normalize(`${loc.name} ${loc.category_name} ${categoryLabel(loc.category_slug, loc.category_name)} ${loc.description ?? ""}`).includes(normalize(query.trim()))
  ).sort((a, b) => sort === "floor"
    ? a.floor_level - b.floor_level || a.name.localeCompare(b.name)
    : sort === "za" ? b.name.localeCompare(a.name) : a.name.localeCompare(b.name)), [stores, category, floor, query, sort]);

  useEffect(() => {
    if (selected !== null) dialog.current?.showModal();
    else if (dialog.current?.open) dialog.current.close();
  }, [selected]);
  useEffect(() => {
    if (!active) setSelected(null);
  }, [active]);
  const reset = () => { setQuery(""); setCategory("all"); setFloor("all"); };
  const hasFilters = query !== "" || category !== "all" || floor !== "all";
  const explore = (navigate: boolean) => {
    if (selected === null) return;
    const id = selected.id;
    dialog.current?.close();
    setSelected(null);
    onOpenLocation(id, navigate);
  };

  return (
    <main id="store-directory" tabIndex={-1} className="store-home">
      <section className="discovery-hero" aria-labelledby="discovery-title">
        <div className="hero-copy">
          <p className="discovery-kicker"><span /> THE NOVA MALL COLLECTION</p>
          <h1 id="discovery-title">A good day.<br />All in <em>one place.</em></h1>
          <p className="hero-description">Your favourite finds. Your next coffee.<br />A little less searching, a little more exploring.</p>
          <div className="hero-actions">
            <a href="#directory-list" className="discovery-primary">Find your next stop <Icon name="send" size={17} /></a>
            <button type="button" className="discovery-text-button" onClick={onMap}>Explore the map <Icon name="layers" size={16} /></button>
          </div>
          <div className="hero-facts"><span><strong>{stores.length}</strong> stores & dining</span><i /><span><strong>{floors.length}</strong> floors to explore</span><i /><span>One easy visit</span></div>
        </div>
        <div className="hero-illustration">
          <MallAtrium />
          <div className="hero-art-label"><Icon name="pin" size={14} /> NOVA Mall <span>Illustrated demo</span></div>
        </div>
      </section>

      <div className="discovery-ribbon">
        <span><Icon name="route" size={19} /><strong>Find it. Map it. Make a day of it.</strong></span>
        <p>Add a few stops. We’ll help you find the way.</p>
        <button type="button" onClick={onPlan}>Build my visit <Icon name="send" size={16} /></button>
      </div>

      <section id="directory-list" className="directory-section" aria-labelledby="directory-heading">
        <div className="directory-heading">
          <div><p className="discovery-kicker">A LITTLE SOMETHING FOR EVERYONE</p><h2 id="directory-heading">Where will you wander?</h2></div>
          <p>Discover a favourite. Find something new.</p>
        </div>
        <div className="directory-controls">
          <label className="directory-search"><Icon name="search" size={20} /><input type="search" aria-label="Search stores" placeholder="A store, a coffee, something new…" value={query} onChange={(event) => setQuery(event.target.value)} /></label>
          <label className="directory-select"><span>Floor</span><select aria-label="Filter by floor" value={floor} onChange={(event) => setFloor(event.target.value)}><option value="all">All floors</option>{floors.map((item) => <option key={item.id} value={item.level}>{item.name}</option>)}</select></label>
          <label className="directory-select"><span>Sort by</span><select aria-label="Sort stores" value={sort} onChange={(event) => setSort(event.target.value)}><option value="az">Name: A–Z</option><option value="za">Name: Z–A</option><option value="floor">Floor</option></select></label>
        </div>
        <div className="directory-categories" role="group" aria-label="Store categories">
          <button type="button" aria-pressed={category === "all"} onClick={() => setCategory("all")}>All places <span>{stores.length}</span></button>
          {categories.map(([slug, label]) => <button type="button" key={slug} aria-pressed={category === slug} onClick={() => setCategory(slug)}>{label} <span>{stores.filter((loc) => loc.category_slug === slug).length}</span></button>)}
        </div>
        <div className="directory-results-meta"><p role="status">{filtered.length} {filtered.length === 1 ? "place" : "places"} to discover{hasFilters ? " · Filtered results" : ""}</p>{hasFilters ? <button type="button" onClick={reset}>Clear filters <Icon name="close" size={13} /></button> : <span>Curated demo directory</span>}</div>
        {filtered.length === 0 ? (
          <div className="directory-empty"><Icon name="search" size={32} /><h3>No places found</h3><p>Try another name, category, or floor.</p><button type="button" className="discovery-primary" onClick={reset}>Reset filters</button></div>
        ) : (
          <div className="store-grid">
            {filtered.map((loc) => {
              const added = visitIds.includes(loc.id);
              return <article className="store-card" key={loc.id} data-testid="store-card" aria-labelledby={`store-name-${loc.id}`}>
                <div className={`store-card-art category-${loc.category_slug}`}>
                  <span className="store-floor-tag"><Icon name="layers" size={12} />{loc.floor_name}</span>
                  <button type="button" className="store-add" aria-label={`${added ? "Remove" : "Add"} ${loc.name} ${added ? "from" : "to"} my visit`} aria-pressed={added} onClick={() => onToggleVisit(loc.id)}><span aria-hidden>{added ? "✓" : "+"}</span></button>
                  <button type="button" className="store-wordmark" onClick={() => setSelected(loc)} aria-label={`View ${loc.name} details`} tabIndex={-1}><StoreBrand slug={loc.slug} name={loc.name} /><small>{categoryLabel(loc.category_slug, loc.category_name)}</small></button>
                </div>
                <div className="store-card-content"><p className="store-category">{categoryLabel(loc.category_slug, loc.category_name)}</p><h3 id={`store-name-${loc.id}`}><button type="button" onClick={() => setSelected(loc)}>{loc.name}<Icon name="send" size={18} /></button></h3><p className="store-description">{loc.description ?? `Discover ${loc.name} at NOVA Mall.`}</p>
                  <div className="store-card-actions"><button type="button" onClick={() => onOpenLocation(loc.id, false)}><Icon name="pin" size={14} /> On the map</button><span>{added ? "In your visit" : loc.wheelchair_accessible ? "Step-free access" : "Check access"}</span></div>
                </div>
              </article>;
            })}
          </div>
        )}
      </section>
      <section className="discovery-visit-banner"><div><p className="discovery-kicker">LESS BACKTRACKING. MORE DISCOVERING.</p><h2>Your stops. A smarter stroll.</h2><p>Save the places you love, then turn your list into one connected route.</p></div><button type="button" className="discovery-primary" onClick={onPlan}>Plan my visit <Icon name="route" size={17} /></button></section>
      <footer className="discovery-footer"><span><strong>mallmind.</strong> A better way around.</span><p>NOVA is a fictional demo mall. Brand names and logos belong to their owners; no affiliation, live opening hours, or indoor positioning.</p><button type="button" onClick={onMap}>Map & visitor tools <Icon name="send" size={14} /></button></footer>
      {visitIds.length > 0 ? <aside className="visit-tray" aria-label="Your selected stops"><span className="visit-tray-icon"><Icon name="list" size={21} /></span><div><strong>{visitIds.length} {visitIds.length === 1 ? "stop" : "stops"} in your visit</strong><p>{visitIds.map((id) => locations.find((loc) => loc.id === id)?.name).filter(Boolean).join(" · ")}</p></div><button type="button" onClick={onPlan}>Plan my route <Icon name="send" size={16} /></button></aside> : null}
      <dialog ref={dialog} className="store-dialog" aria-labelledby="store-detail-title" onClose={() => setSelected(null)}>
        {selected !== null ? <>
          <div className={`store-detail-art category-${selected.category_slug}`}><button type="button" className="store-dialog-close" aria-label="Close store details" onClick={() => setSelected(null)}><Icon name="close" size={20} /></button><StoreBrand slug={selected.slug} name={selected.name} /></div>
          <div className="store-detail-body"><p className="discovery-kicker">{categoryLabel(selected.category_slug, selected.category_name)}</p><h2 id="store-detail-title">{selected.name}</h2><p>{selected.description ?? `Discover ${selected.name} at NOVA Mall.`}</p>
            <dl><div><dt><Icon name="layers" size={16} /> Find us</dt><dd>{selected.floor_name}</dd></div><div><dt><Icon name="wheelchair" size={16} /> Access</dt><dd>{selected.wheelchair_accessible ? "Step-free access available" : "Check route accessibility"}</dd></div></dl>
            <p className="store-hours-note">Demo listing · Opening hours are not published.</p>
            <button type="button" className="discovery-primary" onClick={() => explore(true)}>Take me here <Icon name="route" size={17} /></button>
            <div className="store-detail-secondary"><button type="button" className="btn-ghost" onClick={() => explore(false)}>View on map</button><button type="button" className="btn-ghost" aria-pressed={visitIds.includes(selected.id)} onClick={() => onToggleVisit(selected.id)}>{visitIds.includes(selected.id) ? "Remove from my visit" : "Add to my visit"}</button></div>
            <small>Directions use your chosen start, or Main Entrance if none is set. They do not use live location.</small>
          </div>
        </> : null}
      </dialog>
    </main>
  );
}
