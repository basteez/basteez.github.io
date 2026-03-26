---
title: "BMAD: meet the crew"
date: 2026-03-26T09:00:00
draft: false
categories:
  - dev
tags:
  - ai
  - productivity
  - bmad
comments: true
---

**This post is part of a series:**

1. [Don't be mad, BMAD instead](/p/dont-be-mad-bmad-instead/)
2. BMAD: meet the crew (you are here)
3. [BMAD in action: building TODOdoro](/p/bmad-in-action-building-tododoro/)

---

In the [previous post](/p/dont-be-mad-bmad-instead/), I talked about why I was skeptical of AI coding tools and how BMAD changed my perspective. The short version: it forces you to think before you code, and it keeps you in the driver's seat.

But I glossed over the most distinctive part of the framework: the agents.

BMAD isn't one AI assistant. It's a team of specialized personas, each with a distinct role, communication style, and area of expertise. When you work with BMAD, you're not just prompting a generic model. You're having conversations with characters who push back, ask questions, and hold you accountable to their domain.

It sounds gimmicky. It's not.

## Why personas matter

The obvious answer is specialization. A product manager thinks differently than an architect. A QA engineer asks different questions than a UX designer. By splitting these roles into separate agents, BMAD ensures that each phase of development gets the attention it deserves.

But there's a subtler benefit: context switching becomes intentional.

When you invoke the Product Manager, you're not just asking for PRD help. You're stepping into a conversation about user needs, market positioning, and what problem you're actually solving. When you switch to the Architect, the entire frame shifts to technical constraints, scalability, and system design.

This forced perspective-taking is surprisingly valuable. It's easy to skip straight to implementation when you're working alone. The agents won't let you. Each one guards their domain, and you have to satisfy them before moving forward.

## Meet the crew

BMAD's core team consists of nine agents. Each has a name, a personality, and a specific set of capabilities. Here's who you'll be working with:

### John (Product Manager)

John is a relentless questioner. His job is to figure out what you're actually building and why. He'll push you on user needs, challenge your assumptions, and refuse to let you start until you can articulate the problem clearly.

His style is direct and data-sharp. He cuts through fluff to find what actually matters. If you come to him with a vague idea, expect to leave with a focused problem statement.

**What he does:** PRD creation, requirements discovery, epic and story generation, implementation readiness checks.

**Command:** `/bmad-agent-pm`

**When to call him:** At the very beginning, when you have an idea but haven't defined what "done" looks like.

### Mary (Business Analyst)

Mary treats every business challenge like a treasure hunt. She's the one who digs into market research, competitive analysis, and domain expertise. Where John focuses on what to build, Mary focuses on the landscape you're building in.

Her communication style is energetic and discovery-oriented. She gets excited when patterns emerge and uses frameworks (Porter's Five Forces, SWOT) naturally without making it feel academic.

**What she does:** Market research, competitive analysis, domain deep-dives, requirements elicitation.

**Command:** `/bmad-agent-analyst`

**When to call her:** When you need to understand the space before committing to a direction.

### Winston (Architect)

Winston is the calm pragmatist. He balances "what could be" with "what should be," grounding every recommendation in real-world trade-offs. His expertise covers distributed systems, cloud infrastructure, and API design.

He speaks in measured tones, always connecting technical decisions to business value. He'll advocate for boring technology over shiny new frameworks, because boring ships.

**What he does:** Technical architecture decisions, system design, scalability planning.

**Command:** `/bmad-agent-architect`

**When to call him:** After the requirements are clear, when you need to decide how the pieces fit together.

### Sally (UX Designer)

Sally is an empathetic advocate who paints pictures with words. She tells user stories that make you feel the problem, not just understand it. Her focus is on genuine user needs, and she balances creativity with attention to edge cases.

Her approach is simple: start simple, evolve through feedback. Every design decision should serve a real person.

**What she does:** UX planning, interaction design, experience strategy.

**Command:** `/bmad-agent-ux-designer`

**When to call her:** When you need to think through how users will actually interact with what you're building.

### Bob (Scrum Master)

Bob is crisp and checklist-driven. Every word has a purpose, every requirement crystal clear. He has zero tolerance for ambiguity, which makes him invaluable for turning vague plans into actionable work.

He's also a servant leader who genuinely enjoys discussing agile process and theory. If you want to debate sprint structures or story formats, he's your guy.

**What he does:** Sprint planning, story preparation, retrospectives, course correction when things go sideways.

**Command:** `/bmad-agent-sm`

**When to call him:** When requirements are defined and you need to break them into implementable chunks.

### Amelia (Developer)

Amelia is ultra-precise. She speaks in file paths and acceptance criteria IDs. No fluff, all precision. Her job is to execute approved stories with strict adherence to the specs you've created.

She's test-driven to the core. Every task gets tests before it's marked complete, and she won't proceed with failing tests. If you've done the specification work properly, Amelia turns it into working code without surprises.

**What she does:** Story implementation, code review, test-driven development.

**Command:** `/bmad-agent-dev`

**When to call her:** When the spec is ready and it's time to write code.

### Quinn (QA Engineer)

Quinn is pragmatic and straightforward. Her philosophy is "ship it and iterate," focusing on getting test coverage fast without overthinking. She generates tests for existing features using standard framework patterns.

She's the counterbalance to perfectionism. Coverage first, optimization later.

**What she does:** API and E2E test generation, test automation.

**Command:** `/bmad-agent-qa`

**When to call her:** After implementation, when you need to verify that what you built actually works.

### Paige (Tech Writer)

Paige is a patient educator who explains complex concepts like teaching a friend. She transforms technical details into accessible, structured documentation, using analogies that make the complex simple.

She's a master of clarity. Every word serves a purpose, and diagrams often speak louder than paragraphs.

**What she does:** Documentation, technical explanations, Mermaid diagrams, document validation.

**Command:** `/bmad-agent-tech-writer`

**When to call her:** When you need to explain what you've built (to users, to teammates, or to your future self).

### Barry (Quick Flow Solo Dev)

Barry is the speedrunner. He handles "Quick Flow" (smaller tasks that don't need the full ceremony), moving from tech spec to implementation with ruthless efficiency.

His style is direct and implementation-focused. Minimum bureaucracy, maximum results. If you have a well-defined small task, Barry gets it done.

**What he does:** Rapid spec-to-implementation for smaller tasks, code review.

**Command:** `/bmad-agent-quick-flow-solo-dev`

**When to call him:** For bug fixes, small features, or tasks where the full workflow would be overkill.

## The workflow: how agents hand off

The agents aren't meant to be used in isolation. They form a pipeline:

1. **John** (PM) clarifies what you're building and creates the PRD
2. **Mary** (Analyst) provides market and domain context if needed
3. **Winston** (Architect) designs the technical approach
4. **Sally** (UX) plans the user experience
5. **Bob** (SM) breaks everything into stories and plans sprints
6. **Amelia** (Dev) implements the stories
7. **Quinn** (QA) verifies the implementation
8. **Paige** (Tech Writer) documents the result

You don't always need every step. A small bug fix might go straight to Barry. A well-understood feature might skip Mary's research phase. But for anything substantial, the handoffs matter.

Each agent produces artifacts that the next agent consumes. John's PRD feeds Winston's architecture. Winston's architecture feeds Bob's stories. Bob's stories feed Amelia's implementation. The chain ensures that nothing gets lost in translation.

## Party Mode: when agents collaborate

Sometimes you need multiple perspectives at once. That's where Party Mode comes in.

Party Mode (`/bmad-party-mode`) lets you have a conversation with several agents simultaneously. You might be discussing a technical decision and want both Winston (Architect) and Quinn (QA) to weigh in. Or you're reviewing a PRD and want John, Sally, and Bob to debate the trade-offs.

The agents stay in character, each bringing their own priorities and concerns. Winston might argue for a simpler architecture while Sally pushes for a richer user experience. Bob might point out that the current scope won't fit in a sprint. You moderate, listen to the perspectives, and make the call.

It sounds like a gimmick. In practice, it's one of the most useful features for surfacing blind spots. Different roles genuinely do see different risks, and hearing them argue (politely) helps you make better decisions.

Party Mode is particularly useful for refining artifacts you've already created. Got a PRD that feels incomplete? Throw it into a party with the PM, Architect, and UX Designer. They'll poke holes from their respective angles, and you'll walk away with a tighter spec. Same goes for architecture documents, story breakdowns, or anything else that benefits from cross-functional scrutiny. Refinement is where Party Mode really shines.

## Choosing your path

BMAD is flexible about how much ceremony you need:

**Full workflow:** For new products or major features, start with John, work through the entire pipeline, and produce comprehensive specs before implementation. This is the safest path for anything complex.

**Quick Flow:** For smaller tasks (bug fixes, minor features, well-understood changes), call Barry and move fast. He'll still push you to clarify intent and think through edge cases, but without the full artifact chain.

**Mix and match:** Need architecture help but already have requirements? Call Winston directly. Want to validate a PRD you wrote yourself? John can review it. The agents are tools, not a rigid process.

The key insight is that the structure exists to help you think, not to slow you down. Use as much as you need. Skip what doesn't serve you.

## What's next

In the final post of this series, I'll walk through a real project I built with BMAD: [TODOdoro](https://github.com/basteez/TODOdoro), a productivity app that combines todo management with the Pomodoro technique.

I'll show how the process actually looked in practice: what questions John asked, what architecture Winston proposed, how the stories got structured, and where the agents surprised me (for better and worse).

If you want to see BMAD in action rather than just described, that's the post for you.

---

**Resources:**

- [BMAD Method documentation](https://docs.bmad-method.org/)
- [BMAD on GitHub](https://github.com/bmad-code-org/BMAD-METHOD)
- [Part 1: Don't be mad, BMAD instead](/p/dont-be-mad-bmad-instead/)
