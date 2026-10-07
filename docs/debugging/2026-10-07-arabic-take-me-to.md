# 2026-10-07 — "خذني إلى Nike" answered where Nike is, not how to get there

**Severity:** medium
**Time to find:** minutes, found while demoing the Ask tab
**Area:** assistant

## Symptom

"Take me to Nike" drew a route. The Arabic "خذني إلى Nike" (same meaning) returned `Nike في Ground Floor` and a `highlight_location` action. No route.

## Hypothesis path

Search was fine, it found Nike. So the intent was wrong, not retrieval. `parse_intent` decides route vs search from a phrase list, `_ROUTE`. It had "take me" in English and "קח אותי" in Hebrew, but no Arabic "take me" (خذني, وديني, دلني). Writing tests for all three languages showed a second problem: the Hebrew phrase was in the list, but `_strip_route_words` only removed English phrases, so the destination query was the whole sentence `קח אותי ל-Zara`. It worked live only because search happened to find the Latin token "Zara" inside the sentence.

## Root cause

Two lists that had to agree did not. Route detection was multilingual. Destination extraction was English only.

## Fix

`_strip_route_words` now removes every `_ROUTE` phrase, longest first, then one leading "to": `to`, `إلى`, `الى`, `على`, or Hebrew `ל-` / `ל `. A Hebrew ל glued to a Hebrew word (`לשירותים`) is left alone, because there it is part of the word. Added Arabic خذني / خدني / وديني / دلني and Hebrew תיקח אותי / איך להגיע.

## Prevention

`test_take_me_to_is_a_route_in_three_languages`: seven phrasings in English, Arabic and Hebrew must parse as `route` with the bare store name as the destination.

## Lesson

A case that "works" can be passing by accident. The Hebrew route looked fine in the demo and was only correct because search is forgiving.

## Side finding

The backend runs from a OneDrive folder, and `uvicorn --reload` never saw the edit, so the first live check ran old code. Polling (`WATCHFILES_FORCE_POLLING=true`) fixes the watcher.
