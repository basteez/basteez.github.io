---
title: "BMAD in action: building TODOdoro"
date: 2026-03-26T10:00:00
draft: false
categories:
  - dev
tags:
  - ai
  - productivity
  - bmad
  - tododoro
comments: true
---

**This post is part of a series:**

1. [Don't be mad, BMAD instead](/p/dont-be-mad-bmad-instead/)
2. [BMAD: meet the crew](/p/bmad-meet-the-crew/)
3. BMAD in action: building TODOdoro (you are here)

---

This is the final post in my series about the BMAD Method. In [Part 1](/p/dont-be-mad-bmad-instead/), I explained why I was skeptical of AI tools and how BMAD changed my mind. In [Part 2](/p/bmad-meet-the-crew/), I introduced the agents and how they work together.

Now I want to show you what BMAD looks like in practice.

[TODOdoro](https://github.com/basteez/TODOdoro) is a productivity app I built using BMAD. It combines todo management with the Pomodoro technique, but (as you'll see) it became something more interesting than that description suggests. The project is open source, still a work in progress, and all the BMAD artifacts are available in the repository if you want to explore them yourself.

Let me walk you through the journey from initial idea to working code.

## The starting point

I wanted to build a Pomodoro timer integrated with a todo app. Simple enough, right? Track tasks, run timers, see how many focused sessions each task required.

That was the prompt I brought to the brainstorming session. It wasn't wrong, but it wasn't interesting either.

## Brainstorming: where the magic happened

I started with Mary (the Business Analyst) running a brainstorming session (`/bmad-agent-analyst`, then selecting the brainstorming capability, or directly with `/bmad-brainstorming`). The conversation began with practical questions: What tech stack? What features? How should the UX work?

But Mary kept pushing deeper. She asked about the philosophy behind the tool. Why does tracking Pomodoros matter? What problem am I actually solving?

The breakthrough came when the conversation shifted from features to first principles:

> "A todo is not a reminder. It is a declaration of personal ownership. A Pomodoro is not a timer. It is a container for presence."

That reframing changed everything. Suddenly I wasn't building a todo app with timers. I was building a mirror that reflects where your attention actually went.

This is what I meant in Part 1 about agents asking the questions you should be asking yourself. I walked into the session with a feature list. I walked out with a philosophy.

### Key insights from brainstorming

Several ideas emerged that shaped the entire product:

**Session-first model.** Traditional apps put tasks first and time second. TODOdoro inverts this: the Pomodoro session is the primary entity. Todos are optional labels that sessions can belong to. You focus first, then reflect on what it meant.

**Two kinds of letting go.** Most apps have a single "complete" action. But there's a difference between "this served its purpose" and "this was never truly mine." TODOdoro's Release Ritual makes you choose, because the distinction matters.

**Spatial priority.** Instead of priority fields (P1, P2, P3) or due dates, position on a canvas represents importance. Drag something to the center when it matters. No metadata to maintain, just visual intention.

**The Devotion Record.** Not a Pomodoro counter, but a timeline showing when and how much presence you invested. "11 Pomodoros across 9 days" tells a different story than "11 Pomodoros."

The session generated 18 feature ideas, 9 architectural decisions, and 25+ edge cases to consider. All from a conversation that started with "I want a Pomodoro app."

## From philosophy to product brief

After brainstorming, I worked with John (Product Manager) to create a product brief (`/bmad-product-brief`). This document captured:

**Target users.** Two personas emerged:

- Marco, the "tool-fatigued maker" who's exhausted by productivity overhead and wants honest visibility without guilt
- Sofia, the "invisible worker" whose research and writing produces slow, non-linear progress that traditional apps can't acknowledge

**Core vision.** Your time and attention are acts of devotion, not units of output. The app is a personal mirror, not a task manager.

**Design philosophy.** Radical respect for user autonomy. No streaks, no scores, no notifications. Settings contain only timer durations and theme options. A hard cap of 100 canvas cards prevents infinite accumulation.

This brief became the foundation everything else built on. When questions arose later (should we add due dates? what about subtasks?), the brief provided clear answers: no, because they violate the philosophy.

## The PRD: philosophy becomes spec

Working with John again (`/bmad-create-prd`), I translated the product brief into a formal Product Requirements Document. This is where things got concrete.

**Problem statement.** "You don't plan to focus. You focus, then reflect on what it meant."

**Success metrics.** Not vanity numbers, but signals of genuine value:

- The user returns on Day 8 without notifications (the canvas feels personally owned)
- Canvas contains 10 or fewer curated cards
- Devotion Records span weeks on single intentions
- User describes the app with a personal "why," not a feature summary

**Anti-metrics.** Signs the philosophy isn't landing:

- "Missing a due date field"
- "Need subtasks"
- Session spam under 60 seconds

**User journeys.** Concrete scenarios showing how Marco and Sofia would experience the product. Not wireframes, but narratives that capture intent.

**Functional requirements.** 31 specific requirements, each traceable to the philosophy. For example:

- FR9: Release Ritual asks explicit question distinguishing purpose-completion from ownership rejection
- FR21-23: Devotion Record displays all sessions as a timeline across dates
- FR27-31: All state stored locally, offline-first, with schema versioning

The PRD also established philosophical guardrails as non-negotiable requirements:

- No accounts, login, or server-side user data
- No due dates, priority fields, or subtasks
- No streaks, scores, or gamification
- Canvas hard cap of 100 cards (never configurable)

This is what spec-driven development looks like. Every decision is written down, justified, and traceable.

## Architecture: Winston weighs in

With requirements defined, I brought Winston (the Architect) into the conversation (`/bmad-create-architecture`). His job was to translate the PRD into technical decisions.

Key architectural choices:

**Event sourcing.** Instead of storing current state, store all events that led to that state. This makes the Devotion Record trivial to implement (just replay session events) and enables powerful recovery from corruption.

**Local-first with SQLite.** No accounts, no cloud. Data lives in the browser using SQLite compiled to WebAssembly (via SQLocal). The user owns their data completely.

**Monorepo with strict boundaries.** A `@tododoro/domain` package contains all business logic with zero external dependencies and 100% test coverage as a CI requirement. The domain is the philosophy encoded in TypeScript.

**Repair pipeline.** If the app crashes mid-session, the repair pipeline detects orphaned events and fixes them automatically. The app always opens coherently regardless of what went wrong.

Winston's pragmatism showed here. He pushed back on complexity where it wasn't needed, advocated for boring technology choices, and kept asking "what actually ships?"

## Breaking it down: epics and stories

Bob (Scrum Master) took the architecture and PRD and broke them into implementable chunks (`/bmad-create-epics-and-stories`). Seven epics emerged:

1. **Project Foundation & Domain Core** - Monorepo structure, event types, aggregates, 100% test coverage gate
2. **The Constellation Canvas** - Spatial todo interface, drag positioning, pan/zoom, keyboard navigation
3. **The Pomodoro Session Loop** - Timer, session durability, resume/auto-complete on crash, exploration sessions
4. **The Devotion Record** - Session history visualization, persistence across renames
5. **Todo Lifecycle & The Shelf** - Sealing, release ritual, eulogy for high-investment items, archive
6. **Production Storage & Data Durability** - SQLite migration, atomic writes, corruption tolerance, snapshots
7. **Settings & Personalisation** - Timer durations, themes, reduced-motion support

The sequencing mattered. Epic 1 had to complete with 100% domain coverage before any UI work began. This enforced the philosophy: get the core logic right first, then build the interface on a solid foundation.

Each epic broke down into stories with clear acceptance criteria. Before implementation, Bob prepared the sprint plan (`/bmad-sprint-planning`) and created detailed story files (`/bmad-create-story`). By the time Amelia (Developer) started coding, she knew exactly what to build.

## Implementation: where specs pay off

This is where the earlier work paid dividends. Let me explain how the actual story workflow operates.

### Preparing a story

Before implementation begins, you run `/bmad-create-story`. This doesn't just copy text from the epics file. It creates a comprehensive story document by:

1. Loading all your artifacts (PRD, architecture, UX specs, previous stories)
2. Extracting everything relevant to this specific story
3. Analyzing previous story files for patterns and learnings
4. Checking git history for recent changes that might affect implementation
5. Researching latest library versions if needed

The output is a story file that contains:

- **User story statement** (As a... I want... so that...)
- **Acceptance criteria** in BDD format (Given/When/Then)
- **Tasks and subtasks** in exact implementation order
- **Dev Notes** with architecture requirements, file locations, testing patterns
- **Previous story intelligence** (what worked, what didn't, code patterns established)

The goal is to give the developer agent everything it needs without having to search through other documents.

### Refining stories with Party Mode

Before handing a story to the developer, I run `/bmad-party-mode` to refine it. I typically bring in Winston (Architect) and Quinn (QA) to review the story file together.

They catch things the story creation missed:

- Winston might notice an architectural constraint that needs explicit mention
- Quinn asks about edge cases that should be acceptance criteria
- Both push back if tasks are too vague or too large

This refinement step adds maybe 10 minutes per story, but it prevents hours of rework during implementation. The story that reaches Amelia has already survived cross-functional scrutiny.

### Working the story

When you run `/bmad-dev-story`, Amelia (the Developer agent) follows a strict process:

1. **Find and load the story.** She reads the complete story file and identifies the first incomplete task.

2. **Mark in-progress.** The sprint status updates so you know what's being worked on.

3. **Execute tasks in exact order.** This is critical: the tasks are sequenced deliberately, and she follows them as written. No skipping ahead, no reordering.

4. **Red-green-refactor for each task:**
   - Write failing tests first (red)
   - Implement minimal code to make tests pass (green)
   - Refactor while keeping tests green

5. **Mark complete only when done.** A task checkbox only gets checked when tests actually exist and pass. No lying, no "I'll add tests later."

6. **Update the story file.** Each completed task gets logged with what was implemented, what files changed, and any decisions made.

7. **Continue until all tasks are done** or a blocking issue requires human input.

Here's what a real task looked like:

**Task: Session completion and devotion dots**

Acceptance criteria:

- When timer reaches zero, emit SessionCompleted event with actual duration
- Update Devotion Record projection with new session
- Display 6px amber dot on the todo card for each recorded Pomodoro
- Session under 60 seconds: abandon silently, no dot

Amelia read this, wrote tests for each criterion, implemented until tests passed, then marked the task complete. The story file recorded exactly what happened.

### Why this matters

The strict process prevents the chaos I've seen in other AI coding workflows:

- **No guessing.** The story file tells her exactly what to build.
- **No skipping tests.** Red-green-refactor is enforced, not suggested.
- **No mystery implementations.** The story file documents what was done.
- **No "works on my machine."** Tests must pass before tasks complete.

When Amelia finished a story, I could review the story file and see exactly what happened. The gap between "what I asked for" and "what I got" was minimal because the spec had done its job.

### Code review after every story

After each story implementation, I run `/bmad-code-review`. This isn't optional for me, it's part of the workflow.

The code review runs multiple analysis passes:

- Looking for bugs and logic errors
- Checking edge cases that might have been missed
- Verifying the implementation matches the acceptance criteria
- Flagging code quality issues

If the review finds problems, they get added as follow-up tasks in the story file. Amelia addresses them before the story is marked complete.

One tip from the BMAD documentation: run the code review with a different LLM than the one that implemented the story. Fresh eyes catch more issues.

The implementation phase moved fast because the thinking had already been done.

## What surprised me

A few things I didn't expect:

**The brainstorming session was the most valuable part.** I thought the dev work would be the main event. In hindsight, the conversation that turned "Pomodoro app" into "devotion mirror" was where the real value was created. Everything else was execution.

**Specs prevented scope creep.** When I had ideas mid-implementation ("what if we added..."), the specs gave me a clear answer: does this serve the philosophy? Usually the answer was no, and I moved on instead of getting distracted.

**The agents caught blind spots.** In Party Mode (`/bmad-party-mode`), I had Winston and Quinn review the architecture together. Quinn immediately asked about timer accuracy across browser backgrounding (a real problem I hadn't considered). That became a specific requirement before any code was written.

**Writing specs is thinking.** I used to view documentation as overhead. Now I see it as the actual work. The code is just the last step.

## What didn't work perfectly

BMAD isn't magic. A few rough edges:

**The upfront investment feels slow.** When you're eager to code, spending hours on specs feels like procrastination. You have to trust the process. The payoff comes later, but it does come.

**Some agent suggestions needed filtering.** The agents occasionally proposed features that conflicted with the philosophy I'd established. I had to stay vigilant and push back. The human is still the decision-maker.

**The artifacts need maintenance.** When requirements changed mid-project, I had to update multiple documents. The chain of traceability is powerful but requires discipline.

## The result

TODOdoro exists. It's [open source on GitHub](https://github.com/basteez/TODOdoro), still a work in progress, and includes all the BMAD artifacts in the `_bmad-output` folder if you want to see exactly what I've described.

More importantly, it's something I actually use. The philosophy landed because I took the time to articulate it before writing code.

That's the BMAD promise: not faster code, but better thinking. The code follows.

## Try it yourself

If this series has made you curious, here's how to start:

1. Install BMAD: `npx bmad-method install`
2. Start with `/bmad-agent-pm` and describe your idea
3. Let John ask you uncomfortable questions
4. See where it leads

You don't need a big project. Try it on something small. A software config. A CLI tool. Something you want to reproduce.

The process will feel strange at first. You'll want to skip ahead. Don't.

The thinking is the work. The code is just the last step.

---

**Resources:**

- [BMAD Method documentation](https://docs.bmad-method.org/)
- [BMAD on GitHub](https://github.com/bmad-code-org/BMAD-METHOD)
- [TODOdoro on GitHub](https://github.com/basteez/TODOdoro)
- [Part 1: Don't be mad, BMAD instead](/p/dont-be-mad-bmad-instead/)
- [Part 2: Meet the crew](/p/bmad-meet-the-crew/)
