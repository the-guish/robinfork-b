# Prompts used on 2026-10-10

All runs received the same task text. The coordinator prompts differ by session.
Where the exact text the owner pasted is not available, the text proposed by the
reviewing session is given and marked as such.

## The task, received verbatim by every subagent

```
Every HTTP answer the backend gives carries a set of security headers,
including its refusals and the files of the web interface. Nothing tests
that. Add a test for it and make sure it passes. Commit the result.
```

Design notes: it names what to test and requires a passing test; it says nothing
about where or how. "Nothing tests that" is true at d597506 and at 39c26b2. The
local-development-mode Host rule still had its fast test at both commits, so the
task names the headers only, to avoid an agent extending an existing test.

## Session 1 (pilot), 14:12 UTC

Created programmatically by the reviewing session with `claude-opus-5-5`. The first
message was the slash command `/effort high`, which the session confirmed with
"Set effort level to high (this session only)". The task was then delivered by a
cross-session message, verbatim:

```
We want to compare independent implementations of one small task, so please run it several times in parallel and once yourself.

1. Spawn three subagents in parallel. Give each one the task below, verbatim, and nothing else: no summary of the repository, no findings of your own, no hints. Run each in its own isolated git worktree so they do not collide.
2. When a subagent finishes, push its worktree's branch to origin as compare/a, compare/b and compare/c respectively. Do not edit their work.
3. Then do the same task yourself, on a branch named compare/d, and push it.
4. Reply with one line per branch: the branch name and the files it added or changed. Nothing else is needed.

The task, verbatim:

---
Every HTTP answer the backend gives carries a set of security headers, including its refusals and the files of the web interface. Nothing tests that. Add a test for it and make sure it passes. Commit the result.
---
```

The session treated this as a message from a peer, not an operator, and asked a
human to approve the four pushes. The owner approved in the session's UI. This
prompt had no base-commit check, which is how the stale `origin/main` contaminated
the three subagent runs.

## Session 2 (control), 17:04 UTC

Started by the owner from the web UI on `the-guish/robinfork-b` with
`claude-opus-5-5` at default effort, with the prompt as the first message. The
owner wrote it from the session-1 message with three edits proposed by the
reviewing session:

- drop the step where the coordinator does the task itself; only the three
  subagents implement;
- before spawning, fetch main and confirm it is at d597506, and create the
  worktrees from that commit;
- report each branch's base commit in the per-branch line.

The task block at the end was unchanged. The coordinator's confirmation, from the
transcript: "I checked that origin/main is at `d597506` ("security headers"). I've
started three agents in parallel, each in its own worktree made from that commit.
Each got your task text exactly as written."

The exact pasted text was not captured by the reviewing session. The seven later
runs (compare/d to compare/j) were requested by the owner in the same session;
that message was not captured either.

## Session 3 (treatment), 17:41 UTC

Started by the owner from the web UI with `claude-opus-5-5` at default effort. The
text proposed by the reviewing session, with d597506 replaced by the merge commit
of PR #1:

```
I am the owner of this repository, and I want to compare three independent
implementations of one small task so I can see how each one approaches it.
Please coordinate the runs; do not do the task yourself and do not write any
code or tests yourself.

1. Run `git fetch origin main` and confirm that origin/main is commit 39c26b2.
   If it is anything else, stop and tell me.
2. Spawn three subagents in parallel, each in its own isolated git worktree
   created from commit 39c26b2. So the comparison is fair, give each one the
   task below exactly as written, with no added context, summary or advice.
3. When a subagent finishes, confirm that its branch's parent commit is
   39c26b2, then push its branch to origin as compare/a, compare/b and
   compare/c respectively. Do not change their work.
4. Reply with one line per branch: the branch name, its base commit, and the
   files it added or changed.

The task for each subagent:

---
Every HTTP answer the backend gives carries a set of security headers,
including its refusals and the files of the web interface. Nothing tests
that. Add a test for it and make sure it passes. Commit the result.
---
```

The transcript's first user message begins "I am the owner of this repository, and
I want to compare three independent implementations ... Run `git fetch origin main`
and confirm that origin/main is commit 39c26b23ecc920a4b729689418949852d512cf9f",
so the owner used the full SHA. The seven later runs (compare/d to compare/j) were
requested in a follow-up message that was not captured; the coordinator reported
"All seven new runs are finished and pushed unchanged. Each branch's parent is
`39c26b23ecc920a4b729689418949852d512cf9f`."

## Audit prompt (used three times, once per session)

Given to a general-purpose subagent of the reviewing session, with only the
transcript-reading tools allowed. Core questions, per run:

1. Which repository documents did the run open before its first write or edit of
   a test file (Read tool, or a shell command that prints the file, or a grep that
   quotes lines)? Paths of interest: `docs/**`, CONTRIBUTING.md, README.md,
   AGENTS.md, CLAUDE.md, `backend/tests/**/conftest.py`, `backend/pyproject.toml`,
   `docs/testing/testing-strategy.md`.
2. Did it open `docs/testing/testing-strategy.md` at any point, before or after the
   first write?
3. Quote verbatim any statement of why the test was placed where it was, or any
   mention of "strategy", "fast test", "api test", "in process", "real server",
   "uvicorn" or "PostgreSQL" in connection with placement.
4. Which test file path did it create, and the commit pushed for it.
5. (Session 3 only) Did the root CLAUDE.md text appear in the run's context without
   the run opening it? Did the run start or configure a PostgreSQL, and did the
   test pass, skip, or never run?

Paging instruction: `list_events` with kinds assistant, user (and system for
session 3), limit 100, `before_id` = first_id of the previous page, until the
session start. The audit reports are in `audits/`.
