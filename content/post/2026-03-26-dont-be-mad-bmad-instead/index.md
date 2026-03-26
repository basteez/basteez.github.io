---
title: "Don't be mad, BMAD instead"
date: 2026-03-26T08:00:00
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

1. Don't be mad, BMAD instead (you are here)
2. [BMAD: meet the crew](/p/bmad-meet-the-crew/)
3. [BMAD in action: building TODOdoro](/p/bmad-in-action-building-tododoro/)

---

A few weeks ago I wrote about the tension I felt using AI coding tools, the fear that by outsourcing the friction, I was also outsourcing my competence. That piece ended with a question: are you extending yourself, or outsourcing yourself?

I didn't have a clean answer then. I still don't have a universal one. But I found something that changed how I think about the problem.

## The grave I thought I was digging

When a colleague first mentioned BMAD, my reaction was skepticism dressed as caution. Another AI framework. Another promise that the machine will handle it. My concern wasn't that it wouldn't work, it was that it would work too well, and I'd wake up one day having forgotten how to build things myself.

That fear isn't irrational. I've seen what happens when you reach for autocomplete before you've finished the thought. You produce, but you don't learn. The output looks fine, but the map never forms. You become dependent on a system you can't fully reason about, and every time you hit a similar problem, you prompt again instead of drawing from understanding.

So when someone told me "try this method where AI agents play different roles," I heard: more ways to stop thinking. More automation. More distance between me and the craft I'd spent years developing.

I was wrong. But it took some hands-on experimentation to see why.

## The problem with vibe coding

Before I explain what BMAD does differently, let me describe what it's pushing against.

There's a pattern that's become disturbingly common, often celebrated even, that I'll call "vibe coding." It goes like this: you have a rough idea of what you want to build. You open your editor, write a prompt, and let the AI generate something. If it looks mostly right, you keep it. If it doesn't work, you prompt again with a correction. You iterate like this, adjusting and regenerating, until the output seems functional.

I've always hated this approach. It treats software development like a slot machine: pull the lever, see what comes out, try again if you don't like it.

But here's what's actually happening: you're making decisions without articulating them. You're accepting code without fully understanding it. You're building something that works (maybe) without building a mental model of why it works. The AI is filling in gaps you never consciously identified, which means you can't evaluate whether it filled them correctly.

Vibe coding optimizes for output. It feels efficient in the moment. But it produces fragile results, because no one (not you, not the AI) ever defined what "correct" actually means. When something breaks later, you're debugging a system you never fully understood in the first place.

This isn't a problem with AI. It's a problem with how we use it. And it's the problem that spec-driven development solves.

## What spec-driven development actually means

If you haven't encountered the term before, spec-driven development is exactly what it sounds like: you write the specification before you write the code.

That might seem obvious. "Of course you should know what you're building before you build it." But there's a difference between having a vague idea in your head and having a written document that defines requirements, constraints, acceptance criteria, and architectural decisions.

The spec isn't just documentation. It's a thinking tool. The act of writing it forces you to confront questions you might otherwise skip: What exactly is this feature supposed to do? What happens at the edges? How does this component interact with that one? What does "done" look like?

When you answer these questions upfront, implementation becomes a translation exercise. You're not discovering the requirements as you code. You're executing a plan you've already validated. The code follows from decisions you consciously made, not from guesses the AI filled in for you.

This is the opposite of vibe coding. Instead of iterating toward something that seems to work, you define what "working" means first, then build to that definition.

The challenge, of course, is that writing good specs is hard. It requires discipline, experience, and (honestly) a fair amount of tedium. Which is exactly where BMAD comes in.

## What BMAD actually is

BMAD stands for "Build More Architect Dreams." It's an open-source framework that uses AI agents to guide you through a structured development process, from initial idea through implementation.

But here's the crucial part: BMAD doesn't generate code and call it done. It forces you through the specification process first.

The framework includes multiple specialized agents, each with a distinct role:

- A **Product Manager** who helps you clarify what you're building and why
- A **Business Analyst** who digs into requirements and edge cases
- An **Architect** who designs how components will fit together
- A **Developer** who implements based on the specs you've created
- A **QA Engineer** who defines how you'll verify the implementation works

Each agent asks questions. Each one pushes you to articulate something specific before you move forward. You can't skip to the code, because the developer agent won't have what it needs until the earlier stages are complete.

This structure is the key insight. The AI isn't doing the thinking for you. It's holding you accountable to a process that requires thinking. The agents are collaborators, not replacements. They augment your capability to do the specification work, but the decisions remain yours.

## Why this feels different

Most AI coding tools are optimized for a simple interaction: you prompt, you get code. The faster and more accurate that loop, the better the tool seems.

BMAD optimizes for something else: the quality of your thinking before code exists.

When I started experimenting with it, I chose deliberately small tasks. An Emacs configuration I'd been putting off. A bug I wanted to reproduce in isolation before fixing. Low stakes, easy to abandon if it felt like hype.

What surprised me wasn't the speed. It was the structure.

Working with the Product Manager agent, I had to articulate what I actually wanted (not just "fix this bug," but what specific behavior should change, and why, and how I'd know it was fixed). Working with the Architect, I had to think about how my change would interact with existing code. Working with the QA persona, I had to define acceptance criteria before implementation.

By the time I reached the Developer agent, I wasn't prompting and hoping. I was handing over a spec that I understood, because I'd helped build it. The implementation felt like execution, not experimentation.

And here's what I didn't expect: that constraint is liberating. The process felt slower at first (more steps, more questions, more writing). But I wasn't backtracking. I wasn't debugging code I didn't understand. I wasn't prompting the same thing five different ways hoping for a better result.

The spec had done its job. The thinking was front-loaded, where it belongs.

## Orchestrator, not passenger

The shift I described in my earlier post, from active thinker to passive prompter, doesn't happen with BMAD. It can't. The method requires you to validate, decide, and course-correct at every stage.

The AI handles the grunt work: generating document templates, suggesting architectural patterns, writing implementation code that follows the spec. But you're still the one reviewing, adjusting, and approving. You're still the one who understands why the system is designed the way it is.

That's the answer I was looking for. Not "don't use AI," but "use it in a way that keeps you in the driver's seat."

I delegate the dirty work. I orchestrate. I stay in the loop.

The mental model I keep coming back to is this: BMAD turns AI into a team of junior collaborators who are fast and capable, but who need direction. You're the senior engineer. You set the vision, define the constraints, and make the judgment calls. They execute, and they execute well, but only because you've told them what "well" means.

That's extending yourself. That's the version of AI assistance I was hoping existed.

## The dopamine is real (and so is the fun)

I should mention something else: this process is genuinely enjoyable.

There's a particular satisfaction in watching a well-defined spec turn into working code without surprises. The gap between "what I wanted" and "what I got" shrinks dramatically when you've done the specification work upfront.

And (I didn't expect this) role-playing with the different personas is fun. Switching from the PM mindset to the Architect mindset to the Developer mindset keeps the work varied. You're not just grinding through one mode of thinking. You're shifting perspectives, which keeps you engaged.

BMAD even has something called "Party Mode" where multiple agents can participate in a single conversation, debating approaches and surfacing trade-offs. It sounds gimmicky until you try it. Having the Architect and QA agents push back on each other while you moderate is surprisingly useful for finding blind spots.

## What's next

This is the first in a series of three posts.

In the next one, I'll go deeper on the agents themselves: who they are, what each one does, how they hand off work to each other, and how you can customize the process for your own workflow.

In the third post, I'll walk through a real project I built using BMAD: a productivity app called [TODOdoro](https://github.com/basteez/TODOdoro). It combines todo management with the Pomodoro technique, and I'll show how the method helped me go from a philosophical idea ("a mirror, not a manager") to a working application with a clear architecture.

If you've felt the same tension I did, excited by AI's potential but worried about what you might lose, this might be worth following. BMAD isn't the only answer, but it's an answer. And for me, it's been the difference between feeling like AI is happening to me and feeling like I'm using it deliberately.

The tools are getting more powerful every month. The question isn't whether to use them. It's whether you'll use them in a way that makes you better, or in a way that quietly makes you less than you were.

I know which one I'm choosing.

---

**Resources:**

- [BMAD Method documentation](https://docs.bmad-method.org/)
- [BMAD on GitHub](https://github.com/bmad-code-org/BMAD-METHOD)
