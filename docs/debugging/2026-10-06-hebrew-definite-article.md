# 2026-10-06 — "איפה הכספומט?" did not find an ATM

**Severity:** medium
**Time to find:** the eval printed it (assistant grounding 8/9)
**Area:** assistant

## Symptom

`python -m app.evaluation` marked `איפה הכספומט?` as not grounded. The search case `איפה יש כספומט` passed, because `כספומט` is its own token and it is in the ATM synonym list.

## Hypothesis path

Language detection was fine (`he`). The facility detector sees the substring `כספומט` inside `הכספומט` and returns the English facility word `"atm"`. The next line required `"atm" in folded`, which is false for a Hebrew sentence, so the assistant searched the raw sentence. The keyword matcher then looked for the token `הכספומט`, and the stored synonym is `כספומט` without the definite ה.

## Root cause

Two checks assumed the query token and the stored synonym were the same string. Hebrew attaches "the" to the noun.

## Fix

A detected facility is searched as `atm` or `bathroom`, which the lexical index already knows. Keyword matching also strips one leading ה or Arabic ال. `test_hebrew_atm_searches_the_facility_word` asserts the tool query is `"atm"`.

## Prevention

The eval case stays. After the fix it is 9/9 on the template assistant.

## Lesson

Substring detection and token lookup are different. A prefix that is a clitic will pass one and fail the other.
