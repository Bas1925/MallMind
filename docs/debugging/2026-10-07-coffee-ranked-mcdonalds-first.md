# 2026-10-07 — "coffee" ranked McDonald's above Starbucks

**Severity:** medium
**Time to find:** a few minutes, found by using the app, not by a test
**Area:** search

## Symptom

`GET /api/v1/search?q=coffee` returned McDonald's, Pizza Napoli, Rooftop Cafe, Starbucks, Sushi Kaito. All five scored exactly 0.60. The assistant answered "where can I get coffee?" with "McDonald's is on Ground Floor".

## Hypothesis path

Five identical scores meant one band and a tie-break, not a vector problem. The tie-break is `item.row.name` in `SearchService`, so the order was alphabetical. The question became why McDonald's matched at all: `CATEGORY_KEYWORDS["food"]` contains `coffee`, and that list is written into every food location's `search_text`. Starbucks also has `coffee` in `SLUG_KEYWORDS`, but both lists end up in the same haystack and the keyword band had one score.

## Root cause

`lexical_score` could not tell "this store's own synonym" from "a synonym every restaurant inherits from its category". Both returned 0.60.

## Fix

The keyword band is split. A hit in the store's `SLUG_KEYWORDS` scores 0.65. A hit only through category keywords or the passage stays 0.60. Both stay under category (0.70), so "food" still lists the category. Starbucks and Rooftop Cafe (which also lists `coffee`) now lead at 0.65; McDonald's follows at 0.60.

## Prevention

`test_store_keyword_beats_category_wide_keyword` scores the same query against Starbucks and McDonald's built with the real `build_search_text`.

## Lesson

A band system is only as good as the number of bands. When two different reasons for a match get the same score, the tie-break, here alphabetical order, quietly becomes the ranking.
