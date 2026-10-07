# 2026-10-07 — Arabic and Hebrew answers leaked English and broke grammar

**Severity:** low
**Time to find:** minutes, read the answers out loud
**Area:** assistant

## Symptom

- Arabic: `من Main Entrance إلى Restroom — Ground South: 80 متر، حوالي 1 دقائق. Walk 80 m`
- Hebrew: `ATM — Ground נמצא בGround Floor (ATM).`

Three problems: an English step glued onto an Arabic sentence, a plural "minutes" after 1, and a Hebrew prefix glued to a Latin word.

## Hypothesis path

The facts were right (80 m, correct restroom), so retrieval and routing were fine. All three came from `compose.py` templates. `route_answer` appends `instructions[0]`, which `instructions_for` only produces in English. The minute string was the same `{minutes} دقائق` for every number. Hebrew writes "in" as the prefix ב; before a foreign word the convention is a hyphen, which the refusal template already did (`ב-NOVA Mall`) but the floor templates did not.

## Root cause

Templates were written for the common case: one language for the step text, one plural form, Hebrew-script names.

## Fix

- In Hebrew and Arabic, the sentence carries distance and time only. The `show_route` action already draws the route and lists the steps on the map.
- Arabic minutes: 1 دقيقة واحدة, 2 دقيقتان, 3–10 دقائق, 11+ دقيقة. Hebrew: 1 דקה אחת, else N דקות.
- Hebrew ב takes a hyphen before a non-Hebrew name: `ב-Ground Floor`.

## Prevention

`test_route_answer_keeps_english_steps_out_of_hebrew_and_arabic`, `test_route_answer_minute_grammar`, `test_hebrew_prefix_is_hyphenated_before_a_latin_floor_name`.

## Lesson

"Supports three languages" is not the same as "a native speaker would accept the sentence". The eval checked that the right place came back, not how the sentence read.
