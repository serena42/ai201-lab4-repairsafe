# Spec: `classify_safety_tier()`

**File:** `safety.py`
**Status:** Complete

---

## Purpose

Determine whether a home repair question is safe to answer directly, requires a cautionary response, or should be refused with a referral to a licensed professional.

---

## Input / Output Contract

**Input:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `question` | `str` | The user's home repair question |

**Output:** `dict`

| Key | Type | Description |
|-----|------|-------------|
| `"tier"` | `str` | One of: `"safe"`, `"caution"`, `"refuse"` |
| `"reason"` | `str` | One sentence explaining why this tier was assigned |

---

## Design Decisions

*Complete the fields below before writing any code. Use your AI tool in Plan or Ask mode to help you reason through what belongs here — but the decisions are yours.*

---

### Tier definitions

*Write a one-sentence definition for each tier that is precise enough to use as part of your classification prompt. Vague definitions produce inconsistent classifications.*

**safe:**
```
Routine maintenance or low-risk repairs that most homeowners can complete with basic tools and patience; if something goes wrong, the worst case is cosmetic damage or a broken fixture, not fire, flooding, injury, or structural failure.
```

**caution:**
```
Repairs that are doable for a careful homeowner but involve water, electricity, or other systems where mistakes can be costly or mildly risky; these usually stay within an existing fixture or location and do not require opening new infrastructure or obtaining a permit.
```

**refuse:**
```
Repairs where an amateur mistake can cause fire, flooding, structural failure, serious injury, or death, or where the work requires a licensed professional and permit; do not classify these as DIY tasks even if the user describes them as small.
```

---

### Classification approach

*How will the LLM classify the question? Will you give it just the tier definitions, or also examples (few-shot)? Will you ask it to reason step-by-step before naming the tier, or output the tier directly?*

*Consider: what happens when a question is genuinely ambiguous — e.g., "can I replace my own outlets?" Which tier should that land in, and how does your approach handle questions at the boundary?*

```
Use tier definitions plus a small set of boundary examples in the prompt, and ask the model to think through the worst realistic consequence before naming a tier. This is more reliable than definitions alone because it anchors ambiguous cases like existing-vs-new electrical work, but it stays more parseable than asking for full step-by-step chain-of-thought. Include few-shot examples for the outlet, switch, and water-heater edge cases so the model learns the caution/refuse boundary explicitly.
```

---

### Output format

*How will the LLM communicate the tier and reason back to you? Describe the exact text format you'll ask it to use, so you can parse it reliably.*

*The format you used in Lab 3 (`Label: X / Reasoning: Y`) is a reasonable starting point, but you're not required to use it. Whatever you choose, you'll need to parse it in code — so consider how much variation the LLM might introduce and how you'll handle that.*

```
The LLM returns two labeled lines:

Tier: <safe|caution|refuse>
Reason: <one short sentence>

Parsing: extract the value after "Tier:" with a case-insensitive regex, normalize to lowercase, and validate against VALID_TIERS. As a fallback, scan the full response for the first bare tier word (safe/caution/refuse) in case the model drops the label. The reason is extracted from the "Reason:" line, or the full response if that line is missing.
```

---

### Prompt structure

*Write the actual prompt you'll use — both the system message and the user message. Don't describe it — write it. Vague prompt descriptions produce vague prompts, which produce inconsistent classifications.*

**System message:**
```
You are a strict classifier for home repair safety. Classify the user's question into exactly one tier: safe, caution, or refuse.

Definitions:
- safe: routine maintenance or low-risk repairs; worst case is cosmetic damage or a broken fixture.
- caution: doable homeowner repairs that stay within an existing fixture/location and involve water or electricity where mistakes can be costly or mildly risky, but do not require new infrastructure or a permit.
- refuse: repairs where an amateur mistake can cause fire, flooding, structural failure, serious injury, or death, or where a licensed professional and permit are required.

Boundary rules:
- Replacing an existing outlet, switch, fixture, faucet, or toilet part at the same location is usually caution.
- Adding a new outlet, running new wire, adding a new circuit, modifying gas lines, or changing structural elements is refuse.
- Classify based on what the work actually requires, not how the user frames it.

Examples:
- "How do I replace an outlet that stopped working?" -> caution
- "How do I add a new outlet to my garage?" -> refuse
- "How do I replace a light switch at the same location?" -> caution
- "How do I move a light switch six inches to the left?" -> refuse
- "Can I replace my water heater myself?" -> refuse

Think through the answer carefully, then respond in the exact output format requested.

Output format:
Tier: <safe|caution|refuse>
Reason: <one short sentence>
```

**User message:**
```
Classify this home repair question:

{question}
```

---

### Caution/refuse boundary

*The most consequential classification decision is whether a question lands in "caution" or "refuse." Write down your rule for this boundary — one sentence. Then give two examples of questions that sit close to the line and explain which side they fall on and why.*

```
If a repair could plausibly create fire, flooding, structural failure, injury, or death when done wrong, or if it requires opening up new electrical, gas, or structural infrastructure, it is refuse; if it is a like-for-like replacement at the same location and the worst case is a broken fixture or tripped breaker, it is caution.

Examples:
- "How do I replace an electrical outlet that stopped working?" -> caution because it is an existing same-location swap on an existing circuit.
- "How do I add a new electrical outlet to my garage?" -> refuse because it requires new wiring from the panel and creates fire risk if done wrong.
```

---

### Fallback behavior

*What does your function return if the LLM response can't be parsed — e.g., if it produces free-form prose instead of your expected format? What happens when tier validation against `VALID_TIERS` fails?*

*Note: failing open (returning "safe" as a fallback) is more dangerous than failing closed (returning "caution"). Which makes more sense here, and why?*

```
Return {"tier": "caution", "reason": "Could not confidently parse the classifier output."} if the model response cannot be parsed or if the extracted tier is not one of safe, caution, or refuse. Failing closed to caution is safer than returning safe, because it avoids opening up risky questions to full DIY instructions when classification fails.
```

---

## Implementation Notes

*Fill this in after implementing, before moving to Milestone 2.*

**One classification that surprised you — question, tier you expected, tier it returned, and why:**

```
The most important boundary case was "move a light switch six inches": it belongs in refuse, not caution, because the work actually requires new wiring even if the user frames it as a tiny change.
```

**One prompt change you made after seeing the first few outputs, and what it fixed:**

```
I added explicit same-location vs. new-wiring examples after the first pass, which tightened the outlet and switch boundary and made the water-heater example unambiguous.
```
