# Remaining Issues - July 2026

This document tracks issues found during code review and the resolution plan for each issue.

## How We Will Use This

- You report an issue.
- I add it as a new entry in this file.
- I include a concrete resolution plan with scope, implementation steps, validation, and risk notes.
- I update status as we implement and verify fixes.

## Status Legend

- `OPEN`: Reported, not yet implemented.
- `IN_PROGRESS`: Being implemented.
- `BLOCKED`: Waiting on dependency/decision.
- `DONE`: Implemented and verified.

## Issue Template

Copy/paste this section when adding a new issue.

```markdown
### ISSUE-YYYYMMDD-XX: <Short Title>
- Status: OPEN
- Reported by: <name>
- Date reported: <YYYY-MM-DD>
- Area: <module/notebook/tests/docs>
- Severity: <high|medium|low>

#### Observed Behavior
<What is happening now>

#### Expected Behavior
<What should happen>

#### Repro Steps
1. <step>
2. <step>
3. <step>

#### Suspected Root Cause
<Optional hypothesis>

#### Resolution Plan
1. Scope and constraints
2. Code changes
3. Tests to add/update
4. Validation steps
5. Rollback/mitigation

#### Implementation Notes
<Links to files, commits, PR notes>

#### Verification Evidence
<Command outputs, notebook results, screenshots, etc.>

#### Final Outcome
<What changed and why it resolves the issue>
```

## Issues

### ISSUE-20260723-01: Summary Outputs Show Technical Keys Instead of Human-Friendly Names
- Status: OPEN
- Reported by: Eric Truett
- Date reported: 2026-07-23
- Area: yahoo_fantasy queries, notebook presentation
- Severity: medium

#### Observed Behavior
League, team, and player summaries often display identifiers such as league_key, team_key, and player_key, which are difficult for end users to interpret quickly.

#### Expected Behavior
Summary outputs should prioritize human-friendly fields such as league_name, team_name, owner_name, full_name, and display_position. Keys should be hidden by default or moved to optional technical/debug views.

#### Repro Steps
1. Open examples/query_tables_fixed.ipynb.
2. Run the summary/query cells (for example league/team summary and standings summary).
3. Observe that key columns are prominent in displayed outputs.

#### Suspected Root Cause
Query helpers and notebook display selections currently preserve technical identifiers as primary columns, with no presentation-specific profile for end-user views.

#### Resolution Plan
1. Scope and constraints
	- Keep raw data fidelity in storage and internal joins.
	- Change only presentation-facing summary outputs and helper defaults.
2. Code changes
	- Add presentation-focused query helpers or optional arguments (for example include_keys=False by default for summary functions).
	- Update standings, league/team, my-team, and roster summary outputs to surface human-friendly columns first.
	- Keep keys available in optional columns for troubleshooting.
3. Tests to add/update
	- Add tests asserting default summary schemas prefer name fields.
	- Add tests for optional key inclusion mode.
4. Validation steps
	- Re-run query notebook summary cells and confirm tables are readable without key columns.
	- Confirm joins and downstream calculations are unaffected.
5. Rollback/mitigation
	- If compatibility concerns arise, keep old behavior behind include_keys=True and document migration.

#### Implementation Notes
- Target files likely include src/nfl/yahoo_fantasy/queries.py and examples/query_tables_fixed.ipynb.

#### Verification Evidence
Pending implementation.

#### Final Outcome
Pending implementation.
