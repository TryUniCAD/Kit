# Empty project text fields require null

## Expectation

An empty dependency list can be represented by an empty string when updating a
GitHub Project text field.

## Actual behavior

The bulk-field REST request returned `Invalid field values` with HTTP 400 when the
planning importer included empty strings. Changing those field values to null let
the import advance from 366 to 451 published items. Separate intermittent GitHub
draft-creation errors remain a service boundary, not evidence of successful import.

## Workaround

Send null for a cleared field and a string for nonempty text. Preserve accepted
items and reconcile remote scope markers after uncertain creation responses before
resuming. Never blindly repeat a create mutation.

The [GitHub Projects REST contract](https://docs.github.com/en/rest/projects/items#update-project-item-for-organization)
documents null as the field-clearing value.
