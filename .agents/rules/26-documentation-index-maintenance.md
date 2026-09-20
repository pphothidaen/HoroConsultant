# Rule 26 — Documentation Index (docs/INDEX.md) Maintenance

## Status: NORMATIVE

## Scope

This rule governs the maintenance of `docs/INDEX.md`, the back-matter documentation index
for the HoroConsultant project. The INDEX.md file serves as a searchable alphabetical
reference for all documentation terms, concepts, and cross-references.

## Mandate

**MANDATORY RULE:** Whenever a new document is added to `docs/`, an existing document
is removed, or a document is renamed/moved, the following MUST be updated:

1. **`docs/INDEX.md`** — Add/remove/rename the document in the alphabetical index
   and cross-reference map.
2. **`docs/SUMMARY.md`** — Update the GitBook sidebar navigation entry.

## Trigger Conditions

You MUST update INDEX.md when:

- A new `.md` file is created anywhere inside `docs/`
- An existing `.md` file is deleted from `docs/`
- An existing `.md` file is renamed or moved within `docs/`
- A significant new term, concept, or component is documented that agents or
  developers might need to search for

## Update Procedure

### For New Documents

1. Add a new row to the alphabetical index section (A-Z) for each significant term
   introduced by the document, with the document path as reference.
2. Add the document to the appropriate cross-reference map (by workflow or component).
3. If the document covers a new system component, add it to the "By System Component" table.

### For Removed Documents

1. Delete all alphabetical index rows referencing the removed document.
2. Remove all cross-references to the deleted file.

### For Renamed/Moved Documents

1. Update all references throughout INDEX.md to point to the new path.
2. Verify all cross-references remain valid.

## Automated Support

The GitHub Action `.github/workflows/update-index.yml` runs on every push that modifies
`docs/**/*.md` and auto-regenerates the document registry section of INDEX.md. However,
the alphabetical index (A-Z) and cross-reference map sections must be maintained manually
as they require semantic understanding of the content.

## Verification

Run the following to verify all docs are indexed:

```bash
python3 scripts/verify_doc_index.py
```

## Failure Mode

If INDEX.md is found to be out of date (missing references to existing docs), the PR
check workflow will fail with a list of unindexed documents.
