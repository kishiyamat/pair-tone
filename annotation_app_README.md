# Pair Annotation App

A standalone annotation application for validating and revising Japanese mishearing stimulus pairs.

This app is intended to be developed in a separate repository from the corpus construction codebase. Its role is to support human annotation over pre-exported pair manifests, with fast audio preview via Amazon Polly and structured result storage in S3.

## Goal

Given a `pair_id`, the annotator should be able to:

1. Check whether the 8 sentences belonging to the pair form a valid stimulus set.
2. Reject invalid pairs early when the target words are not used with the same sense.
3. Inspect and revise prosody for valid items.
4. Preview the result with Amazon Polly.
5. Save the final annotation as a pair-level record.

The app is optimized for throughput, not for corpus generation. Data preparation stays in the existing corpus repository; annotation and submission happen in this separate app.

## Scope

### In scope

- Pair-level validity screening
- Sentence-level prosody editing for 8 items in a pair
- Amazon Polly preview
- Revisioned saves to S3
- Worker/time logging for crowdsourcing
- Retrieval of latest revision per pair

### Out of scope

- Corpus generation
- Pair mining
- LLM prompting
- Audio dataset versioning inside this app repo
- Crowd worker management beyond recording worker IDs and submission logs

## Core assumptions

- One pair contains 8 items.
- Annotators are assigned batches externally, for example via CrowdWorks.
- The app only needs a `worker_id` or equivalent task code.
- Pair validity is decided before detailed prosody correction.
- Prosody editing should be easier than direct AquesTalk/OpenJTalk editing.

## Annotation model

### Pair-level decision

The first decision is whether the pair is usable at all.

A pair is invalid when the two target words are not used with the same sense across the 8 sentences.

Example:

- `めじろ台` is used as a place name
- `目白` is interpreted as the bird

In that case, the pair should be rejected before prosody work begins.

### Sentence-level prosody fields

For valid pairs, each item is edited with two layers:

- `prosody_kana`: reading, phrase boundaries, pauses, devoicing marks
- `prosody_pattern`: `L/H` sequence aligned with mora count and phrase boundaries

Example:

```json
{
  "prosody_kana": "メジロダイニ/デカケタ",
  "prosody_pattern": "LHHLLL/LHHH"
}
```

Design principle:

- Upper layer: reading and phrasing
  - `kana`
  - `/`
  - `、`
  - `_`
- Lower layer: pitch only
  - `L`
  - `H`
  - same boundary layout as upper layer

The app converts these into preview-ready Polly SSML and, if needed later, into AquesTalk-like kana.

## Why this format

Directly editing accent nuclei such as `メジロ'ダイニ/デカケタ'` is precise but hard for non-specialists.

Using `prosody_kana + prosody_pattern` reduces cognitive load:

- phrasing edits are separate from pitch edits
- annotators can think in `L/H` rather than accent-nucleus terminology
- the system can validate mora-pattern consistency automatically

## Input data

The app reads pair manifests exported from the corpus repository.

Recommended input unit: one pair per record.

Example:

```json
{
  "pair_id": "めじろ台__目白",
  "word_a": "めじろ台",
  "word_b": "目白",
  "items": [
    {
      "item_id": 17,
      "condition_id": "a",
      "target_word": "めじろ台",
      "sentence": "週末にめじろ台に出かけた。",
      "openjtalk_kana": "シュウマツニ'/メジロ'ダイニ/デカケタ'"
    }
  ]
}
```

## Output data

The app writes revisioned pair annotations to S3.

Recommended output unit: one annotation record per saved pair revision.

Example:

```json
{
  "pair_id": "めじろ台__目白",
  "worker_id": "cw_001",
  "revision": 3,
  "status": "completed",
  "pair_is_valid": true,
  "pair_invalid_reason": null,
  "started_at": "2026-05-08T10:00:00Z",
  "updated_at": "2026-05-08T10:14:12Z",
  "submitted_at": "2026-05-08T10:14:12Z",
  "elapsed_sec": 852,
  "items": [
    {
      "item_id": 17,
      "condition_id": "a",
      "target_word": "めじろ台",
      "sentence": "週末にめじろ台に出かけた。",
      "is_natural_sentence": true,
      "prosody_kana": "シュウマツニ/メジロダイニ/デカケタ",
      "prosody_pattern": "LHHHHH/LHHLLL/LHHH",
      "preview_used": true,
      "notes": ""
    }
  ]
}
```

## Validation rules

### Pair-level rules

- All 8 sentences must use the target words in the intended senses.
- If the pair fails this requirement, set `pair_is_valid=false` and stop sentence-level prosody work.

### Sentence-level rules

- `prosody_kana` and `prosody_pattern` must have the same boundary layout.
- `/` and `、` must appear in the same places in both strings.
- Each phrase must have the same number of morae and `L/H` symbols.
- `_` is allowed in `prosody_kana` and should not count as an extra mora.
- Small kana such as `ャ`, `ュ`, `ョ` belong to the previous mora.
- Sokuon `ッ` and moraic nasal `ン` each count as one mora.

### Derived output rules

- Generate pitch-drop markers automatically from `prosody_pattern`.
- Preserve phrase boundaries.
- Preserve `、` separately from `/` because pause strength differs.

## Amazon Polly usage

Amazon Polly is used for preview audio, not as the source of truth.

The app should:

1. Convert `prosody_kana + prosody_pattern` into Polly-compatible SSML.
2. Use Japanese pronunciation support such as `x-amazon-pron-kana` where possible.
3. Insert pauses corresponding to `、`.
4. Synthesize short previews on demand.

Preview is optional support, not the only inspection method. Annotators may often decide directly from `L/H` patterns.

## Storage design

### S3 layout

Suggested layout:

```text
s3://BUCKET/
  manifests/
    pair_manifest.jsonl
  annotations/
    worker_id=cw_001/
      pair_id=めじろ台__目白/
        rev=0001.json
        rev=0002.json
  latest/
    pair_id=めじろ台__目白.json
```

### Storage strategy

- Keep immutable revision records under `annotations/`
- Optionally write denormalized latest snapshots under `latest/`
- Never overwrite history without retaining revision metadata

## UI requirements

### 0. Pair selection

- Select a `pair_id`
- Show pair metadata and annotation status
- Resume latest revision if one exists

### 1. Pair validity check

- Show all 8 sentences at once
- Ask whether the pair is valid as a stimulus set
- Require a reason when invalid

### 2. Prosody editing

For valid pairs only:

- Display all 8 items
- Show sentence, target word, and `openjtalk_kana`
- Provide editable `prosody_kana`
- Provide editable `prosody_pattern`
- Show validation warnings inline

### 3. Preview

- Generate Polly preview per item on demand
- Optionally allow pair-level batch preview
- Mark whether preview was used

### 4. Save and submit

- Save draft
- Submit completed pair
- Record timestamps and elapsed time
- Keep latest revision retrievable

## Suggested MVP

### Phase 1

- Streamlit app
- Local JSON manifest input
- S3 save
- Pair validity check
- Prosody editing fields
- Basic mora/boundary validation
- Polly preview per sentence

### Phase 2

- Latest revision loading
- Better error messages for mora mismatch
- Worker dashboard
- Search/filter by status
- Batch export for QA

### Phase 3

- Admin review mode
- Inter-annotator agreement support
- Assignment import from external platform output

## Recommended repo structure

```text
annotation-app/
  README.md
  app.py
  requirements.txt
  annotation_app/
    __init__.py
    ui/
    polly/
    validation/
    storage/
    schemas/
  tests/
  docs/
```

## Suggested Python dependencies

- `streamlit`
- `boto3`
- `pydantic`
- `pandas`
- `python-dotenv`
- `pytest`

Optional:

- `orjson`
- `tenacity`
- `mypy`
- `ruff`

## Operational notes

- Worker management is delegated externally, for example to CrowdWorks.
- The app should only store the worker identifier needed for payment and traceability.
- Audio synthesis is helpful but should not be mandatory for every judgment.
- The most important guardrail is strong validation between kana units and pitch patterns.

## Open questions

- Exact JSON schema for pair manifests
- Exact transformation from `prosody_pattern` to Polly pronunciation kana
- Whether to persist derived SSML or regenerate it on every preview
- Whether latest snapshots should live in S3 only or also in a lightweight DB
- Whether admins need a separate review UI

## Initial build order

1. Define manifest and annotation schemas.
2. Implement mora counting and boundary validation.
3. Implement `prosody_kana + prosody_pattern -> Polly SSML` conversion.
4. Build the Streamlit pair annotation screen.
5. Implement S3 draft/save/submit flow.
6. Add revision browsing and QA support.

---

## Implementation notes (as of 2026-05)

### accent_kana format (replaces prosody_kana + prosody_pattern)

The implemented annotation model uses a single `accent_kana` field instead of the two-layer `prosody_kana + prosody_pattern` design described above.

`accent_kana` encodes reading, accent nucleus, phrase boundaries, devoicing, and pauses in one string:

| Symbol | Meaning |
|--------|---------|
| `'` | Accent nucleus (high-to-low transition follows this mora) |
| `/` | Accent phrase boundary (no pause) |
| `_` | Devoiced mora |
| `、` | Pause boundary (maps to 150 ms `<break>` in SSML) |

Example:

```
サ'ッキマデ/ミナ'デ、ア'_クションニ/ツ'イテ/ハナ'_シテ/イタ'
```

Each phrase delimited by `/` or `、` must contain exactly one `'`.

### Polly SSML conversion

`accent_kana_to_ssml()` converts `accent_kana` to Polly SSML as follows:

- `、` splits the string into separate `<phoneme>` tags separated by `<break time="150ms"/>`.
- Within each `、`-clause, all `/`-phrases are merged into a single `<phoneme>` tag.
- The `ph` attribute receives `'` markers but **not** `_` or `/`; Polly's `x-amazon-pron-kana` silently ignores any `<phoneme>` element whose `ph` contains `/`.
- The text node inside `<phoneme>` is plain kana with `'`, `_`, and `/` all removed.

Example output:

```xml
<speak><lang xml:lang="ja-JP">
  <phoneme alphabet="x-amazon-pron-kana" ph="サ'ッキマデミナ'デ">サッキマデミナデ</phoneme>
  <break time="150ms"/>
  <phoneme alphabet="x-amazon-pron-kana" ph="ア'クションニツ'イテハナ'シテイタ'">アクションニツイテハナシテイタ</phoneme>
</lang></speak>
```

### Tab layout

The app uses four tabs (no step-by-step navigation):

| Tab | Content |
|-----|---------|
| 0. ペア選択 | Worker ID + Pair ID form; annotation history per worker |
| 1. 有効性チェック | Pair validity judgment |
| 2. アクセント編集 | `accent_kana` editing with inline Polly preview |
| 3. 保存・提出 | Draft save and final submission |

### Worker annotation history

Tab 0 shows a table of all annotations submitted by the entered Worker ID.
This list is loaded from `annotations/worker_id={id}/` in S3 and shows pair ID, status, validity judgment, and last updated time.
Clicking a row populates the Pair ID field for easy resumption.

### S3 paths (actual)

```text
s3://BUCKET/{PREFIX}/
  manifests/
    pair_manifest.jsonl          # base batch
    retry01/pair_manifest.jsonl  # additional batches (merged by pair_id)
  annotations/
    worker_id={safe_id}/
      pair_id={safe_id}/
        rev=0001.json
  latest/
    pair_id={safe_id}.json       # latest revision snapshot per pair
```

`safe_id` replaces `/` and `\` with `_`.
