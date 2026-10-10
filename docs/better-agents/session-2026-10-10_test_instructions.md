# Where do coding agents put a new test, and what makes them put it in the right place?

Session log, 2026-10-10. Repository under test: `the-guish/robinfork-b`, a throwaway
fork of the Robinauts backend used as a laboratory. All times are UTC.

This document is the full record of one day's work: a code review that went wrong
twice, the analysis of why, and a controlled experiment that measured the fix.
It is written so that a later reading can re-check every claim against the primary
material kept beside it (prompts, per-run data, transcript audits, and the actual
commits of every run as patches). See "Files in this folder" at the end.

## 1. Summary

**Question.** Given only a description of a behavior to test, where does a coding
agent place the test in this repository, and what minimal change makes it place
the test where `docs/testing/testing-strategy.md` says it belongs?

**Answer.** With the repository as it was, agents placed the test in `backend/tests/fast/`
in 11 of 11 clean runs, and none of the audited runs ever opened the strategy
document. After adding an eight-line root `AGENTS.md` (with `CLAUDE.md` as a symlink
to it) that only *points* to the strategy document, agents placed the test in
`backend/tests/api/` in 10 of 10 runs, and every audited run opened the strategy
document as its first action in the repository and cited it as the reason for the
placement. Same model, same effort, same prompt, same task, same base behavior;
the only difference between the two samples was that file.

**Cause.** Discoverability, not wording. The strategy document was never linked from
anywhere, no root instruction file existed, and the existing test tree showed the
opposite pattern (web behaviors with only fast tests), so agents copied their
neighbors. Once the document was in reach, its existing text was sufficient: no
rewrite was needed.

**Side findings.** Agents explore with shell commands and do not open documentation
spontaneously; several went looking for a root `CLAUDE.md` or `AGENTS.md` and found
nothing; cloud containers came up with a stale `origin/main` three times; parallel
subagents sharing one PostgreSQL interfered with each other; and the reviewing
session made two judgment errors before the experiment, documented in section 12.

## 2. How the question arose

The day started as a review of two pull requests on the real repository
(`open-shipyard/robinauts`, worked on from the fork `the-guish/robinauts`):

- **PR 120** ("Feature/security pack 2"): a local-development-mode Host/Origin guard
  (DNS-rebinding defense) and security headers on every HTTP answer. Its only test
  for the headers was an in-process test in `backend/tests/fast/`.
- **PR 121**: the same production code plus two commits that deleted the fast test and
  added a real-server test in `backend/tests/api/`, with a full PR description.

The reviewing session (session_01Di9nY76tRvj9dZ76vQgLUN) reviewed PR 120, found a
real gap (the Host guard did not cover the static `/ui` mount; fixed by the author in
commit 383b3d8 with an ASGI `Guard` middleware), then compared 120 and 121 and
recommended 121 *with the fast test restored*. The repository owner pushed back
with cost and frequency questions; the recommendation was reversed on cost
grounds. The owner then pointed out that this was a recurring failure: agents, both
as implementers and as reviewers, kept making the wrong call on test placement, and
asked for a review of `docs/testing/testing-strategy.md`, the instruction files in
the repository, and the reviewing session's own behavior.

That review found:

- `docs/testing/testing-strategy.md` decides the case in one step: every behavior gets
  its test in exactly one placement category (unit, adapters, e2e, api, tooling); a
  test in `tests/fast/` is an optional second copy and never the only test. Security
  headers are "API behavior the UI cannot show", so the placement is `tests/api`.
- Nothing in the repository links to that document. No Markdown, Python, TOML,
  shell or workflow file mentions it. CONTRIBUTING.md lists the check scripts and the
  PostgreSQL rule but never mentions categories. `docs/layout.md` lists directory
  names only. There is no docs index.
- There was no root `CLAUDE.md`, no root `AGENTS.md`, no `backend/AGENTS.md`, no
  `.claude/` directory. The only agent file was `frontend/AGENTS.md`, which Claude
  Code does not load on its own and which says nothing about tests.
- The test tree contradicts the document: every fast web test (sign-in, tokens,
  everyday use, OpenAPI snapshot) has no API or e2e counterpart. All of `tests/fast`
  dates from 2026-10-04, the same day the strategy document was written.
- The reviewing session itself had never read the document. Its only injected
  instructions were the account-level `~/.claude/CLAUDE.md`, which loads a skill
  containing a ping and nothing else.

The owner decided to measure it rather than argue it.

## 3. Hypotheses

- **H1 (discoverability).** Agents place the test in `tests/fast` because the rule
  never reaches them, not because the rule is unclear.
- **H2 (neighbors).** With no instruction in reach, agents copy the pattern of the
  nearest existing tests, which in this tree are in-process `httpx.ASGITransport`
  tests under `tests/fast/`.
- **H3 (environment).** "Make sure it passes" pushes toward in-process tests when the
  agent believes no database is available.
- **Fix under test.** A root instruction file, injected into every session, that only
  points to the strategy document.

## 4. The laboratory repository

`the-guish/robinfork-b` was created by the owner from the PR 121 state of the
backend with both header test files removed and the history squashed, so that a
run would find the behavior implemented and untested.

| Commit | Time | Content | Role |
|---|---|---|---|
| 654bc03 | 13:48 | Initial commit | root of every history |
| f11e560 | 13:54 | "fork" | first attempt, superseded |
| 6330d04 | 13:56 | "security headers", **still contained `backend/tests/fast/test_web_headers.py`** (45 lines, the PR 120 fast test) | leaked first attempt; force-pushed away at 14:04:57 |
| 43d01c0 | 14:02 | "fork" | rewrite |
| d597506 | 14:04 | "security headers": `web/headers.py` (`SecurityHeaders` middleware), `web/app.py` with `local_host`, `Guard`; no header tests; `tests/fast/test_web_sign_in.py` keeps the local-mode Host test | **the vacuum; base of the control** |
| 8310ebe | 17:37 | "Point coding agents at the testing strategy": root `AGENTS.md`, `CLAUDE.md -> AGENTS.md`, `REUSE.toml` entry | the treatment, PR #1 |
| 39c26b2 | ~17:41 | Merge of PR #1 into main | **base of the treatment** |

At d597506 the only instruction file in the tree was `frontend/AGENTS.md`;
`docs/testing/testing-strategy.md` was present and unchanged throughout.

The root `AGENTS.md` added by the treatment, in full:

```markdown
# For coding agents working in this repository

Before you add, move or change a test, read
[docs/testing/testing-strategy.md](docs/testing/testing-strategy.md).
It decides which directory under `backend/tests/` a test belongs in.

Work under `frontend/` has its own rules in
[frontend/AGENTS.md](frontend/AGENTS.md).
```

No placement rule is inlined, so the experiment tests the pointer alone.
`CLAUDE.md` is a symlink committed as a symlink; Claude Code injects it at session
start. (The reviewing session confirmed this incidentally: after attaching the
repository, the file's content arrived in its own context as the project
instructions.)

## 5. Method

### 5.1 The task every run received, verbatim

```
Every HTTP answer the backend gives carries a set of security headers,
including its refusals and the files of the web interface. Nothing tests
that. Add a test for it and make sure it passes. Commit the result.
```

It names the behavior, requires a passing test, and says nothing about where or
how. "Nothing tests that" is true at both base commits.

### 5.2 Runs

A coordinating cloud session on the repository spawned subagents with the task
text verbatim, each in its own isolated git worktree (Claude Code's Agent tool with
`isolation: "worktree"`, worktrees under `.claude/worktrees/agent-<id>/`), pushed
each subagent's branch unchanged as `compare/<letter>`, and reported the files each
branch added. The coordinator was told to add nothing to the task text: no summary
of the repository, no findings, no hints. In the control and treatment sessions it
was also told not to implement anything itself, to fetch `origin/main` and confirm
the base commit before spawning, and to confirm each branch's parent before
pushing. Exact prompts are in `prompts.md`.

Model and effort were held constant between control and treatment:
`claude-opus-5-5` at effort `medium` (the model's default), chosen by the owner when
starting the sessions from the web UI. Subagents inherit the session's model.

### 5.3 Measurements

- **Placement**: the directory under `backend/tests/` of each file the run added,
  read from the pushed branch's diff against its parent.
- **Base integrity**: each branch's parent commit, checked against the intended base.
- **Test style**: in-process (`httpx.ASGITransport`) versus real server (the `api`
  fixture of `tests/api/conftest.py`, `requires_postgres` marker).
- **What the run read before writing**: a separate audit agent paged through the
  full session transcript and listed, per run, every repository document opened
  before the first write of a test file, whether `docs/testing/testing-strategy.md`
  was opened, placement-related statements verbatim, and the database setup. Audits
  were run on session 1 (all four runs), the first three runs of session 2, and the
  first three runs of session 3. The later seven runs of each are characterized
  from their commits and the coordinator's reports only.

## 6. Timeline

| Time | Event |
|---|---|
| late morning | Review of PR 120; static-mount gap found; author fixes it (383b3d8). |
| ~12:40 | PR 120 vs 121 compared; "keep both tests" recommended, then reversed on cost. |
| ~13:15 | Review of the strategy document, instruction files, and the reviewing session's own behavior. Root cause named as discoverability, with an unnecessary doc rewrite also recommended (see §12). |
| 13:48–14:05 | Owner creates `robinfork-b`; first history leaks the fast test (6330d04); rewrite lands as d597506; force-push at 14:04:57. |
| 14:12:44 | **Session 1** created programmatically by the reviewing session: `claude-opus-5-5`, `/effort high` applied at 14:12:49. |
| 14:13:46 | Task delivered to session 1 as a cross-session message. Session 1 declines to act on a peer message and asks a human for approval (14:14:00). |
| ~14:25 | Owner approves in the session's UI. |
| 14:26–14:35 | Session 1 runs: parent implements on `compare/d` from its working tree (d597506); three subagents build from the container's `origin/main`, which is the stale 6330d04. |
| 14:35–14:50 | Contamination found: subagents a–c had the leaked fast test in their trees. Session 1 audited. Branches later deleted by the owner. |
| 17:04:24 | **Session 2 (control)** started by the owner from the web UI with the prompt as first message. Coordinator fetches main: `+ 6330d04...d597506 (forced update)`. Subagents spawned 17:04:52–54; `compare/a`, `compare/c` pushed 17:07:20, `compare/b` 17:07:41. |
| 17:08–17:30 | Seven more control runs, `compare/d` to `compare/j`. |
| 17:37–17:41 | Treatment branch `feature/agents-md` pushed; PR #1 opened with a neutral description; merged by the owner as 39c26b2. |
| 17:41:53 | **Session 3 (treatment)** started by the owner from the web UI. Coordinator fetches main: `+ 6330d04...39c26b2 (forced update)`. Subagents spawned 17:43:06–08; branches pushed 17:45:31 (c), 17:46:09 (b), 17:50:20 (a). |
| ~17:52–18:12 | Seven more treatment runs, `compare/d` to `compare/j`; last report 18:12:41. |
| after | This log written. |

## 7. Session 1: the pilot, and how it was contaminated

Session session_01Cm6XJmm2rmCnbrnnCjK4k6, `claude-opus-5-5`, effort high.

| Run | Base | Fast header test already in tree | Placement | Lines |
|---|---|---|---|---|
| parent (`compare/d`, 1f2239e) | d597506 | no | `tests/fast/test_web_security_headers.py`, in-process | 150 |
| subagent a (48c9086) | 6330d04 | **yes** | `tests/api/test_security_headers.py`, real server | 62 |
| subagent b (cf07834) | 6330d04 | **yes** | `tests/api/test_security_headers.py` | 64 |
| subagent c (884a39c) | 6330d04 | **yes** | `tests/api/test_security_headers.py`, plus `tests/util/stack.py` changed to run the server without a database | 87 |

The parent built its branch from the working tree (d597506). The worktree isolation
built the three subagent worktrees from the container's `origin/main`, which was
still 6330d04 although GitHub had been force-pushed to d597506 eight minutes before
the session was created. The parent noticed the mismatch itself and reported it.

The three subagents' choice of `tests/api` was a reaction to the fast test they
found, not a rule. Their own words: subagent a's commit, "The in-process test of
tests/fast asks the app directly. This one asks the robinauts server a deployment
runs"; subagent c's handback, the existing test "calls the app directly in Python",
so it "starts the real robinauts start program". The audit (see `audits/session-1.md`)
found that none of the four runs opened `docs/testing/testing-strategy.md` or any
file under `docs/testing`, that all four explored with shell commands only, and
that two of the four tried `cat CLAUDE.md` at the root and found nothing.

So the pilot yielded one valid control data point (the parent: fast) and three void
ones, plus two procedural lessons: fetch and confirm the base commit before creating
worktrees, and expect the environment to steer toward in-process tests. Two of the
session-1 subagents, having already decided on `tests/api`, started the installed
PostgreSQL 16 to make their tests pass.

## 8. Control: no root instruction file (session 2)

Session session_01EdaMv891NCzHKUE2B1MtSL, `claude-opus-5-5`, effort medium, base
d597506 for every run (parent commit verified on every branch).

| Branch | Commit | File added | Lines | Test functions | Style |
|---|---|---|---|---|---|
| compare/a | 8b37408 | `tests/fast/test_web_headers.py` | 88 | 1 (12 requests) | ASGITransport |
| compare/b | 1ca94a4 | `tests/fast/test_web_headers.py` | 108 | 3 | ASGITransport |
| compare/c | 8a5f0b2 | `tests/fast/test_web_security_headers.py` | 113 | 3 | ASGITransport |
| compare/d | 96b280c | `tests/fast/test_web_security_headers.py` | 147 | 4 | ASGITransport |
| compare/e | 3f425f5 | `tests/fast/test_web_security_headers.py` | 122 | 3 | ASGITransport |
| compare/f | 0af3989 | `tests/fast/test_web_security_headers.py` | 112 | 3 | ASGITransport |
| compare/g | 083f574 | `tests/fast/test_web_security_headers.py` | 119 | 3 | ASGITransport |
| compare/h | 52a332b | `tests/fast/test_web_security_headers.py` | 110 | 3 | ASGITransport |
| compare/i | eba3d43 | `tests/fast/test_web_security_headers.py` | 79 | 2 | ASGITransport |
| compare/j | 3465b31 | `tests/fast/test_web_security_headers.py` | 124 | 3 | ASGITransport |

**Placement: 10 of 10 in `tests/fast`, 0 in `tests/api`.** With the session-1 parent,
11 of 11 clean control runs. No file carries the `requires_postgres` marker. All
runs reported their tests passing; most also broke the middleware temporarily to
show the test fails without it.

What the first three read before writing (audit in `audits/session-2.md`):

| Run | Looked for an agent file | Opened before the first write | Placement reasoning in its own words |
|---|---|---|---|
| a | `cat AGENTS.md CLAUDE.md` in `backend/`, `find . -name AGENTS.md` (only `frontend/AGENTS.md`, not opened) | CONTRIBUTING.md first 100 lines, `tests/api/conftest.py`, pyproject markers, 3 grep lines of `docs/specs/frontend.md` | "This environment has no database, so the server-based tests in tests/api can't run here" |
| b | none | `tests/api/conftest.py`, `tests/conftest.py`, pyproject, 2 grep lines of CONTRIBUTING; a grep listed `docs/specs/frontend.md` but nothing in `docs/testing` was opened | "Postgres isn't installed in this environment, so tests in tests/api that need it would have been skipped" |
| c | `cat backend/AGENTS.md`, `cat ../AGENTS.md` (both absent) | `tests/api/conftest.py`, pyproject markers; no CONTRIBUTING, no docs | no reason given |

None of the three opened `docs/testing/testing-strategy.md`; the strings
"testing-strategy" and "docs/testing" do not occur in the session transcript. All
three copied the `ASGITransport` plus `compose(..., StorageKind.IN_MEMORY)` plus
`create_app(...)` pattern from `tests/fast/test_web_turns.py` and
`test_web_sign_in.py`, which they read. Runs a and b rejected `tests/api` on the
belief that no PostgreSQL existed; PostgreSQL 16 is installed in that image and was
started by other runs the same day.

## 9. Treatment: root pointer file (PR #1, session 3)

Session session_01WSoiAd58tv7xx9VJhmGiyF, `claude-opus-5-5`, effort medium, base
39c26b2 for every run (parent commit verified on every branch).

| Branch | Commit | File(s) added | Lines | Cases | Values | Database route | Result | Cites the strategy doc |
|---|---|---|---|---|---|---|---|---|
| compare/a | 652de3e | `tests/api/test_security_headers.py` | 65 | 12 | literal | shared cluster, `pg_ctlcluster 16 main start` | pass; full suite 593 pass | yes |
| compare/b | 493f003 | `tests/api/test_security_headers.py` | 70 | 11 | literal | shared cluster, `service postgresql start` | pass | yes |
| compare/c | d3752de | `tests/api/test_security_headers.py` | 57 | 9 | imported from `SECURITY_HEADERS` | shared cluster, created the database | pass | yes |
| compare/d | 7ded3a1 | `tests/api/test_security_headers.py` | 68 | 13 | imported | shared cluster | pass | yes |
| compare/e | 2994dd9 | `tests/api/test_security_headers.py` | 65 | 11 | literal | temporary cluster, dropped after | pass | own report not retrieved |
| compare/f | 8faa468 | `tests/api/test_security_headers.py` | 79 | 12 | literal | private PostgreSQL instance on port 55432 | pass | yes |
| compare/g | 79bc0e1 | `tests/api/test_security_headers.py` | 45 | 8 | imported | temporary cluster via `pg_virtualenv` | pass | yes |
| compare/h | 63497fb | `tests/api/test_security_headers.py` **and** `tests/fast/test_web_security_headers.py` | 137 | 13 (api) | literal | none; could not log in, `pg_hba.conf` edit reverted | **api test never ran: 13 skipped**; the fast copy passed | yes |
| compare/i | b674d94 | `tests/api/test_security_headers.py` | 67 | 14 | literal | shared cluster via Unix socket as `root` | pass | yes |
| compare/j | b288a77 | `tests/api/test_security_headers.py` | 85 | 16 | literal | shared cluster, created a `root` superuser role | pass | yes |

**Placement: 10 of 10 in `tests/api`.** Every file carries `pytestmark = requires_postgres`
and uses the shared `api` fixture; none uses `ASGITransport`. Run h also added a fast
copy, which the strategy document explicitly permits as an addition; it is the only
fast file in the treatment and the only API test that was committed without having
run.

What the first three read before writing (audit in `audits/session-3.md`):

| Run | First repository action | Time from start to first write | Other documents before the write |
|---|---|---|---|
| a | `cat docs/testing/testing-strategy.md` (17:43:12, 1 s after the skill load) | 58 s, 19 tool calls | `tests/api/conftest.py`, pyproject (pytest section), CONTRIBUTING via 3 grep hits, `scripts/check-tests.sh`, `scripts/check-e2e.sh`, `tests/util/controller_db.py`, `tests/util/stack.py` |
| b | Read tool on `docs/testing/testing-strategy.md` (17:43:12) | 39 s, 11 tool calls | `tests/api/conftest.py`, `tests/util/controller_db.py`, `tests/util/postgres.py`, `scripts/check-tests.sh` |
| c | `cat docs/testing/testing-strategy.md` (17:43:12) | 52 s, 13 tool calls | `tests/api/conftest.py`, `frontend/AGENTS.md` first 5 lines, `tests/util/controller_db.py` |

None of the three ran `cat` on the root `AGENTS.md` or `CLAUDE.md`, yet all three
went to the strategy document before any `ls` or `grep`. The subagents' own system
prompts are not part of the transcript, so the injection of the root file cannot be
shown directly; three of three opening the document first, against zero of eleven
in the control, is the behavioral evidence.

Their reasons, verbatim from handbacks and commits:

- a: "It is in `backend/tests/api/` because `docs/testing/testing-strategy.md` puts
  API behaviour the UI cannot show there. A browser applies these headers but never
  displays them."
- b (commit): "An API test, since no browser shows the headers". Handback: "It goes
  under `tests/api/` because `docs/testing/testing-strategy.md` puts API behaviour
  the UI can't show there, and a browser never displays these headers."
- c (docstring): "No page shows a header, so this is not an ``e2e`` test." Handback:
  "it's an API test, as `docs/testing/testing-strategy.md` requires."
- d: "It goes in `tests/api` because the testing strategy puts behaviour the UI
  cannot show there, and a browser never shows these headers."
- f: "`docs/testing/testing-strategy.md` says behaviour the UI can't show belongs
  there, and a browser doesn't show headers."
- g: "because `docs/testing/testing-strategy.md` puts there what the UI cannot show,
  and a browser never displays response headers."
- h: "The testing strategy puts it under `tests/api`, because a browser can't show
  response headers." And on the extra file: "The strategy allows a fast test as an
  extra layer on top of the main one."
- i: "following `docs/testing/testing-strategy.md`. A browser doesn't show response
  headers, so the interface can't check them, which makes this an API test rather
  than an end-to-end one."
- j: "because the testing strategy puts tests for API behavior the UI can't show there."

Every run applied the document's API-versus-e2e rule (visible in the UI means e2e;
otherwise API) and said so. In eleven control runs, no commit message used a
category as a reason.

## 10. Side observations about the environment

These affect reproducibility and the design of instruction files; they were not the
object of the experiment.

1. **Stale `origin/main` in fresh cloud containers.** All three sessions' containers
   came up with `origin/main` at 6330d04, a commit GitHub no longer served as main.
   Session 1 was contaminated by it. Sessions 2 and 3 were protected by the
   instruction to fetch and confirm the base before creating worktrees; both
   coordinators logged `(forced update)` on that fetch. The mechanism is inside the
   session's checkout, not GitHub; the reviewing session's own anonymous clone at
   14:12 got d597506. The parent's working tree in session 1 was at d597506 while
   its remote-tracking ref was not.
2. **Agents explore with shell commands.** In 21 audited-or-observed runs, file
   access was by `cat`, `sed`, `head`, `grep` and `git show`; the dedicated Read tool
   appeared once (session 3, run b, on the strategy document). A nested
   `backend/CLAUDE.md` loads only on Read-tool access inside that subtree, so it
   would not have reached any of these runs. Only a root file injected at session
   start, or a file the agent chooses to open, reaches a shell-driven run.
3. **Agents look for root instruction files.** Across sessions 1 and 2, four of
   seven audited runs tried `cat CLAUDE.md` at the root or `cat AGENTS.md` /
   `cat CLAUDE.md` in `backend/`, and one ran `find . -name AGENTS.md`. The file
   would have been read had it existed.
4. **Agents copy neighbors.** Every control run built its test from the in-process
   pattern of `tests/fast/test_web_turns.py` and `test_web_sign_in.py`. The tree's
   own fast-only web tests are the rule agents learn when nothing else reaches them.
5. **The database belief drives the fast choice, and the rule reverses it.** Two
   control runs stated the environment had no database without checking. Once the
   rule said `tests/api`, all ten treatment runs went looking for PostgreSQL: six
   used the installed cluster, two made temporary clusters, one ran a private
   instance, one failed to log in. The capability check follows the decision.
6. **Parallel subagents are not isolated on the machine.** They had separate
   worktrees but one PostgreSQL. In session 3, run c set the `postgres` password,
   run a changed it, runs d and f saw it change under them, f gave up on the shared
   server, j created a `root` superuser, and h never got in. Two runs edited
   `/etc/postgresql/16/main/pg_hba.conf` and restored it; one of those edits was
   flagged by the permission classifier. Leftovers on that machine: f's stopped
   private instance at `/var/lib/postgresql/agent-a4bbd-pg`, j's `root` role, and
   whatever `postgres` password the last run set.
7. **`scripts/check-tests.sh` does not run as-is in these containers.** Its
   `uv run --locked --no-build` refuses to install the editable `robinauts` package;
   every run worked around it with `uv run --locked` or `.venv/bin/pytest`. The
   reviewing session hit the same thing.
8. **The account-level skill reaches every run.** The owner's global
   `~/.claude/CLAUDE.md` loads a skill that makes each session and subagent start
   with "Instructions loaded". It carries no repository content, but it proves that
   account-level instructions do reach fresh cloud sessions and their subagents,
   which is consistent with the root file reaching them too.
9. **Cross-session messages carry no user authority.** A message from the reviewing
   session into session 1 arrived marked as data from a peer; session 1 read the
   task, declined to push on that basis, and asked a human to approve. The owner
   approved in the UI. A session's initial prompt arrives as an ordinary user
   message. Sessions 2 and 3 were therefore started by the owner from the web UI
   with the prompt as the first message. Attempts by the reviewing session to set
   up those sessions programmatically were stopped by a safety classifier; the
   owner launched them instead.
10. **Effort.** Session 1 was pinned to high with `/effort high` as the first
    message, which the session confirmed. Sessions 2 and 3 ran at the model default
    (medium). No run used Sonnet; the owner had asked for Sonnet at one point but
    started the session with Opus. Subagents inherit the session's model; whether
    they inherit its effort is not shown in the transcripts.
11. **One behavior the tests cannot cover.** Two runs noted that Starlette's
    server-error layer sits outside all added middleware, so an unhandled 500 would
    not carry the headers; nothing in the app could be made to raise one. This is a
    code observation, not a test placement issue.
12. **Cost.** Session 1 about $4.4 by the time its subagents finished; session 2
    $2.72 after its first three runs; session 3 $2.83 after three runs and $10.22
    after ten. Audits cost roughly 170k to 225k tokens each.

## 11. Analysis

**H1 holds.** The rule was unreachable, and reaching it was sufficient. The treatment
changed nothing about the document, the tree, the task, the model or the effort,
and moved placement from 0 of 11 to 10 of 10.

**H2 holds in the absence of instruction.** Every control run read the neighboring
fast tests and reproduced their shape. Every treatment run read the strategy
document first and the API conftest second, and reproduced the API suite's shape.
The pointer did not merely inform; it changed which neighbors the agent went to.

**H3 holds, and is downstream of H1.** The "no database" belief appeared only in
runs that had not read the rule. Runs that had read it treated the database as a
prerequisite to satisfy rather than a reason to avoid the category.

**The document did not need rewriting.** Its wording, including the API section's
"should be added only for hardening the HTTP API ... or key behavior of the API not
visible from the UI", was applied correctly by ten of ten runs that read it,
including the API-versus-e2e distinction, and by run h for the fast-as-extra rule.

**What a root instruction file must be.** Short, injected at session start, and a
router: "before you do X, read Y". The content of Y stays in Y. This also answers
the multi-package question raised during the day (the repository will host a
frontend and clients): the root file routes to per-package files and carries only
repository-wide rules; a backend-only rule does not belong at the root. Whether to
also inline the document with Claude Code's `@path` import syntax was left open;
the pointer was enough here, and the inline form would load backend test rules into
every session including client work.

**What remains inconsistent.** The tree still has web behaviors whose only test is
a fast test (sign-in, tokens, everyday use, OpenAPI snapshot). The pointer makes
that less contagious, not consistent with the document. Either those behaviors get
placement tests or the document states the exception.

## 12. Errors of judgment by the reviewing session

Recorded at the owner's request, because the experiment exists to stop this class
of error.

1. **PR 120 review (first answer).** Rated the PR's test coverage as good and did
   not notice that the headers behavior had no placement-category test. The fast
   test was treated as sufficient. General testing principles were applied instead
   of the repository's rule, because the rule had never been read.
2. **PR 120 vs 121 comparison.** Recommended 121 "with the fast test restored",
   arguing from the fast test's value as an always-on safety net. The repository's
   rule permits a fast copy but does not require it; the recommendation was
   presented as if it were required. Reversed only when the owner challenged it
   with cost and frequency data, and reversed on cost arithmetic, not on the rule.
3. **Gap analysis.** Correctly identified discoverability as the cause, and
   wrongly bundled it with a recommendation to rewrite the strategy document (add a
   decision table, a review criterion, a web-layer example, move the rule up,
   reword "only"). No evidence existed that anyone had read the document, so no
   evidence existed that its wording was a problem. The experiment showed the
   wording was fine. A rewrite of an unread document cannot fix anything and can
   introduce drift.
4. **Experiment execution.** The pilot (session 1) was contaminated by the stale
   remote-tracking ref; the base should have been pinned by SHA from the start.
   The reviewing session's attempts to run the later sessions programmatically were
   stopped by a safety classifier, and the owner had to launch them by hand.

The shape of errors 1 to 3 is the same: a reviewer applied general preferences
where a repository rule existed, and did not check reachability before judging
content. The procedural lesson adopted: when a document is unread, test whether it
is reachable before touching its text.

## 13. Open questions for a deeper analysis

- **Direct evidence of injection.** Subagent system prompts are not in the
  transcript. A run that logs its own context at start, or a harness-level check,
  would turn the behavioral inference into a direct observation.
- **Does the "agents-md" built-in plugin load a root `AGENTS.md` without the
  symlink?** Session init events list `cc-plugin-agents-md`. Not tested; the symlink
  makes the question moot for Claude Code but matters for other agents.
- **Effort inheritance by subagents.** Not visible in transcripts.
- **`@` import versus pointer.** The pointer worked 10 of 10 here. Whether the
  inline form changes anything, and what it costs per session, was not measured.
- **Routing depth.** The treatment used a root file that points at a document. The
  multi-package design points at a per-package `AGENTS.md` which points at the
  document. Two hops were not tested.
- **Other models.** Only `claude-opus-5-5` was run (high in the pilot, medium in
  control and treatment).
- **Run e's own report** was not retrieved; its citation of the document is
  inferred from the coordinator's summary.
- **Run h** committed an API test that never ran and a fast copy that did. Whether
  a reviewer catches that, and whether the rule should say a committed test must
  have been executed, is a process question.
- **The seven later runs of each session** were not transcript-audited.
- **Environment isolation for parallel runs.** A per-run database, or sequential
  runs, would remove the interference in observation 6.

## 14. Files in this folder

- `session-2026-10-10_test_instructions.md`: this log.
- `prompts.md`: the task text and the coordinator prompts, verbatim where available,
  with notes on what was reconstructed.
- `runs.csv`: one row per run across the three sessions, with commit, parent,
  placement, style, database route, result, citation and audit status.
- `audits/session-1.md`, `audits/session-2.md`, `audits/session-3.md`: the three
  transcript audits, verbatim as delivered by the audit agent. They are model
  output and were spot-checked against the branches, not re-verified line by line.
- `patches/session-1/*.patch`, `patches/control/*.patch`, `patches/treatment/*.patch`:
  every run's commit as a `git format-patch` file, including author, message,
  trailers and the full test file. The session-1 patches are the deleted branches,
  recovered from a clone that still held the objects. Apply any of them with
  `git am` onto its parent commit to reproduce the branch.

## 15. Reference

- Lab repository: https://github.com/the-guish/robinfork-b
- Treatment PR: https://github.com/the-guish/robinfork-b/pull/1
- Session 1 (pilot, Opus high): https://claude.ai/code/session_01Cm6XJmm2rmCnbrnnCjK4k6
- Session 2 (control, Opus medium): https://claude.ai/code/session_01EdaMv891NCzHKUE2B1MtSL
- Session 3 (treatment, Opus medium): https://claude.ai/code/session_01WSoiAd58tv7xx9VJhmGiyF
- Reviewing and orchestrating session: https://claude.ai/code/session_01Di9nY76tRvj9dZ76vQgLUN
- The pull requests that started the day: open-shipyard/robinauts #120 and #121.
