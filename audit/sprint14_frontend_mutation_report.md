# Sprint 14-A Frontend Mutation Report

## Goal
Prove that the new static-UI pytest coverage detects realistic frontend regressions.

## Mutations and expected failures

| Mutation | Expected failing test |
|---|---|
| Remove `briefForm` from the detail page | `test_detail_contains_brief_form` |
| Remove `artifactList` from the detail page | `test_detail_contains_artifact_list` |
| Remove `progressFill` from the detail page | `test_detail_contains_progress_fill` |
| Remove `localStorage` from the projects page | `test_projects_uses_localstorage` |
| Remove `client-package.zip` from the detail page | `test_detail_contains_client_package_zip` |

## Coverage notes

- The new suite checks file existence, visible UI markers, artifact references, and explicit mock-generation labeling.
- It also verifies that the smoke report documents the same frontend proof points.
- The checks are static and deterministic, so they catch source regressions without needing a browser runtime.

## Manual verification summary

- Mutation A: breaks the brief form selector and fails the brief-form test.
- Mutation B: breaks the artifact list selector and fails the artifact-list test.
- Mutation C: breaks the progress bar fill selector and fails the progress-fill test.
- Mutation D: removes persistence proof and fails the localStorage test.
- Mutation E: removes the ZIP artifact reference and fails the ZIP artifact proof test.
