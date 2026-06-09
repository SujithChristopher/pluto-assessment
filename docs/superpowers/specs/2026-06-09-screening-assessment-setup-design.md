# Screening / Assessment Session Setup — Design

Date: 2026-06-09
Status: Approved (pending spec review)

## Goal

Collapse subject creation, subject selection, limb selection, and time-point
selection into a single "Session Setup" window. Introduce two modes —
**Screening** and **Assessment** — selected by radio button. Remove the
healthy/stroke (`subjtype`) distinction everywhere; the app now always deals
with stroke subjects.

## Decisions (locked)

| Topic | Decision |
|---|---|
| Subject entry | Unified Subject ID box. Existing id → load + lock fields. New id → editable + create. |
| Screening protocol | AROM only, all four mechanisms (FPS, WFE, WURD, HOC). Own shorter protocol. |
| Screening folder | Single-shot, no timepoint: `screening/{subjid}/{limb}/{session}/`. |
| Screening affected | Screened limb **is** the affected limb (limb = afflimb, single selector). No dominant hand. No healthy/stroke. |
| Subject lists | Separate per directory: `screening_subjects.csv`, `fullassess_subjects.csv`. |
| Task inclusion | Drop `subjtype` check (always stroke). Keep `limb==afflimb` gate for AROM/PROM/APROM. |
| Migration | Fresh start. No conversion of old `fullassessment/{type}/...` data. |
| Screening trials | Reuse `AROM.NO_OF_TRIALS`. |
| Label | "Subject ID" (not "Patient ID"). |

## 1. Session Setup window

Replaces `SubjectCreator`, `SubjectSelector`, and the main-window limb +
timepoint controls. One modal window returning a single setup dict.

```
┌─ Session Setup ──────────────────────────┐
│  Mode:  ( ) Screening   ( ) Assessment   │
│  Subject ID: [__________]  (unified box)  │
│      → exists: loads fields, locks them   │
│      → new:    fields editable, creates   │
│  Affected side:        [Left ▾]           │  ← screening: this IS the screened limb
│  Limb being assessed:  [Left ▾]   ← assessment only
│  Dominant hand:        [Right ▾]  ← assessment only
│  Time point:           [A0 ▾]     ← assessment only
│            [ Start ]   [ Cancel ]         │
└──────────────────────────────────────────┘
```

Behaviour:
- Mode radio drives which fields are visible. Screening shows only Affected side
  (which is the screened limb); it hides the separate Limb selector, Dominant
  hand, and Time point. Assessment shows all.
- Subject ID box: on editing-finished, look the id up in the mode-appropriate
  subjects CSV. If found, populate and lock the subject-level fields
  (afflimb; domlimb for assessment). If not found, fields stay editable and the
  subject is created on Start.
- No healthy/stroke control anywhere.
- Start validates required fields, creates/loads the subject record, and returns
  the setup dict. Folder + protocol creation is performed by the worker thread
  in the main window (not in this window).

Returned dict shape:
```python
{
  "mode": "screening" | "assessment",
  "subjid": str,
  "limb": "left" | "right",            # screening: equals afflimb
  "afflimb": "left" | "right",
  "domlimb": "left" | "right" | "",   # "" for screening
  "timepoint": "A0"|"A1"|"A2"|"",      # "" for screening
}
```

## 2. Data layout

`subjtype` is removed everywhere. The `{type}/` path layer is removed.

```
screening/
  screening_subjects.csv            [subjid, afflimb, createdat]
  {subjid}/{limb}/{session}/        session = {limb[0]}_screen_{YYYYmmdd_HHMMSS}
     {subjid}_{limb}_screening_protocol.csv
     subject_info.json              {subjid, afflimb, limb}
     ...raw + summary csvs

fullassessment/
  fullassess_subjects.csv           [subjid, domlimb, afflimb, createdat]   # subjtype col removed
  {subjid}/{limb}/{timepoint}/{session}/                                    # {type}/ layer removed
     {subjid}_{limb}_{timepoint}_protocol.csv                              # type removed from name
     {subjid}_{limb}_{timepoint}_details.json
     subject_info.json              {subjid, domlimb, afflimb, limb, timepoint}
     ...raw + summary csvs
```

`session` name: assessment `{limb[0]}_{timepoint}_{datetime}`; screening
`{limb[0]}_screen_{datetime}`.

Breaking change: existing data under `fullassessment/{type}/...` is not read by
the new code. Accepted (fresh start).

## 3. Protocol / task inclusion

- New `SCREENING_MECH_TASKS = {m: [["AROM"]] for m in MECHANISMS}` in
  `plutofullassessdef.py`. AROM only, all four mechanisms.
- Dedicated screening protocol builder adds AROM rows for all four mechanisms.
  The screened limb is always the affected limb (limb = afflimb), so the
  affected-side gate is satisfied by construction. Reuses `AROM.NO_OF_TRIALS`.
- Assessment `is_task_included(taskname, limb, afflimb)` — `subjtype` parameter
  removed. Keeps `in_unaffected or limb == afflimb` gate.
- `TASK_DEPENDENCIES`: remove the `in_subjtypes` key from every entry.

## 4. State machine + main window

- State machine: collapse `SUBJ_SELECT → LIMB_SELECT → TIMEPOINT_SELECT` into a
  single setup step. The setup window returns everything at once; the worker
  builds the folder + protocol; the machine then goes straight to `MECH_SELECT`.
  Remove `LIMB_SET` / `TIMEPOINT_SET` two-step events (one `SETUP_DONE` event).
- `PlutoAssessmentData`: add `mode` (screening|assessment); drop `type`.
  Replace `set_subject` / `set_limb` / `set_timepoint` with one
  `setup_session(setupdict)` that stores fields and (via worker) creates the
  session folder. Folder/file naming uses `mode` to pick the tree and naming
  scheme.
- `async_workers.LimbSetupWorker`: handle both modes (screening = no timepoint,
  screening protocol builder).
- Main window: delete `cbLimb`, `pbSetLimb`, `cbTimePoint`, `pbSetTimePoint`,
  and the two subject buttons. Add one "Setup Session" button opening the new
  window. Mechanism-selection UI stays; for screening only AROM is enabled.
- Fix the DEBUG init block (drop `TYPE_LIMB_SET`, `type`) and window-title
  strings (drop type).

## 5. Files touched

| File | Change |
|---|---|
| `subjectcreator.py` | Rewrite as the combined Session Setup window. Two `SubjectsListFile` variants (screening/assessment headers). |
| `subjectselector.py` | Removed/folded into the combined window. |
| `ui/sessionsetup.ui` + `uipy/ui_sessionsetup.py` | New UI for the combined window. |
| `ui/plutofullassessment.ui` + `uipy/ui_plutofullassessment.py` | Remove limb/timepoint/subject widgets; add Setup Session button. |
| `plutofullassessdef.py` | Drop `{type}` from `DATA_DIR` paths; add screening dir + `screening_subjects.csv`; `SCREENING_MECH_TASKS`; `is_task_included` signature; `TASK_DEPENDENCIES` cleanup. |
| `plutofullassesssdata.py` | `PlutoAssessmentData` mode/no-type; `setup_session`; screening protocol builder; filename/folder schemes; JSON contents. |
| `plutofullassessstatemachine.py` | Collapse setup states; `SETUP_DONE` event. |
| `plutofullassessment.py` | New setup callback; remove old callbacks/UI wiring; DEBUG + title fixes. |
| `async_workers.py` | Worker handles both modes. |

## Out of scope

- Migrating or reading legacy `{type}/`-layered data.
- Changes to individual task windows beyond what AROM-only screening requires.
- The legacy proprioception app (`plutopropass.py`).
