═══════════════════════════════════════════════════════════
SPEC DRIVEN DEVELOPMENT — PROJECT CONSTITUTION
Project: k2-archive-system
Version: 1.0
═══════════════════════════════════════════════════════════

This project uses Spec Driven Development. All work is
governed by three source-of-truth files:

  requirements.md  — What the system must do
  design.md        — How the system is structured
  tasks.md         — The ordered implementation plan

MANDATORY BEFORE ANY ACTION:
  1. Read requirements.md in full
  2. Read design.md in full
  3. Read tasks.md — identify the next incomplete [ ] task

HARD CONSTRAINTS:
  - Never implement requirements not in requirements.md
  - Never alter the data model without updating design.md first
  - Never create files not listed or implied in design.md
  - Never mark a task [x] without verifying its acceptance criterion
  - Never guess when a requirement is ambiguous — ask instead

DIVERGENCE PROTOCOL:
  If implementation must deviate from design.md:
    1. Stop immediately
    2. Describe the conflict clearly
    3. Wait for explicit user approval
    4. Update design.md BEFORE writing code
═══════════════════════════════════════════════════════════

## Project-specific notes

**Scope:** The Archive/Delete subsystem ONLY. The k2-dashboard nav refactor (Phases 1-4) is parallel and NOT governed by these specs — those live in chat + `~/.claude/.../memory/project_k2_nav_refactor.md`.

**Codebase location:** `/Users/ryansandoval/.openclaw/workspace/k2-dashboard/index.html` (single-file SPA). Renderers + helpers all in this one file.

**Data location:** Private GitHub repo `RyanSandoval/k2-data`, file `data.json`. K2Archive mutations flow through `saveData()`.

**Single-agent project:** Only `claude-cli` touches this codebase. No `.cursorrules` / `copilot-instructions.md` needed (no other agents).

**Phase 0 is non-negotiable.** Do not start TASK-005+ until Ryan has verified every `[INFERRED]` requirement and `[TO VERIFY]` design note.

**Existing partial implementation:** `K2Archive` IIFE + Trash page + sidebar entry + palette entry + Trash page CSS are already in `index.html`. `deleteNote` already routed. Treat existing code as Phase 1 in-progress; audit against final spec before extending (TASK-005).

**Toast policy:** Single in-flight `.k2arch-toast` at a time. New archive replaces previous toast — previous Undo is forfeit. This is by design per `design.md` § 5 failure modes.

**Branch:** Work on `main` directly (small project, no PR review process). Commit after each task with `[TASK-NNN]` prefix.
