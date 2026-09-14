---
title: "Yes, you still need to know how to code"
date: 2026-09-14
draft: false
categories:
  - dev
tags:
  - ai
  - productivity
comments: true
---

AI writes good code, faster than me most of the time and usually cleaner than my first pass. I'm not going to argue otherwise and I'm not interested in the version of this piece where the craft is sacred and typing things by hand builds character.

What I think is that the hard part of the job was never the typing, it was the part nobody watches: working out whether the thing is correct, whether it will hold, whether it should exist at all, and that part hasn't got cheaper.

Actually, "hasn't got cheaper" is too soft. Reading is cheap when you can trust the author's intent and expensive when you can't, and a model hands you volume with no stable intent to anchor to, so the careful read, the kind that catches the subtle thing, is exactly the one that gets expensive, and exactly the one people skip. The cost didn't vanish when generation got cheap, it moved to the other side of the ledger where it's harder to see and much easier to skip.

The reason it's easy to skip is that the output is optimised to look right, not to be right. A model trained to produce the most likely continuation leans, over and over, in the same direction: toward the plausible. A developer who can't read code doesn't avoid that cost, they defer it into debt and into bugs they aren't equipped to notice.

## A prompt is not a task

_Write me a function that does X_ looks like handing off a chore but it isn't. Buried in it are decisions about structure, trade-offs, failure behaviour, and the quiet one underneath: what "correct" means in this particular domain. And if you can read the output, you can see those decisions and keep them. You notice that it reached for an ORM where a query would have done, that it picked a pattern that fights a constraint it doesn't know about, that it decided errors should be swallowed instead of raised. Some of those you'll accept, that's fine; the point is that you accepted them. If you can't read the output, you're not delegating how something gets done, you're accepting what gets done, in bulk, and you won't notice the difference until much later.

## Where plausible actually bites

The clearest case is debugging, because there the gap shows up as a test going green. A green test never could tell you whether the cause was gone or just hidden, that's not new; what's new is the speed and the fluency, the model reaches for the change that silences the symptom, hands it back looking finished, and does it fast enough that the pause where you'd have got suspicious never happens.

Review has a version of the same problem, except worse, because the dangerous code isn't the code with obvious bugs in it, the model usually catches those. The dangerous code is locally fine and globally wrong: consistent with the file it lives in, in violation of something that lives three modules away, and the model isn't holding a picture of your system, so if you aren't either, you're not reviewing anything.

Security is where I'd be most nervous, because insecure code and secure code look the same to an untrained reader: the query gets parameterised in the path you were looking at and concatenated in the branch you weren't, the permission check reads beautifully and still lets you fetch an object by guessing its ID, somebody logs a token "for debugging" and it survives into production. None of these fail a quick read, you catch them only if the threat model is already in your head.

Architecture is a quieter failure: ask for a design and you get roughly the average of everything that's been written about designs, which means the well-represented answer: the service boundaries, the fashionable abstraction, the thing that made sense for a company forty times your size. It has no idea you're three people, or that the latency budget makes that choice unworkable, and it doesn't volunteer _why not something simpler_, which is the question that would have saved you.

Then there's the thing I don't have a clean name for: the model rarely tells you this shouldn't be built, it won't volunteer that the problem is the wrong problem, it defaults to yes unless you build the friction that makes it say no. That kind of judgement lives in the things that don't get built, and a system whose only output is the artefact can't represent it at all.

None of this means the only defence is a human squinting at a diff. Linters, type systems, scanners, a second model told to go looking for the bug: they catch a real share of what I've described, and you should use all of them, they raise the floor. But every one of them checks against a shape someone already knew to encode, so the failures that survive are the ones that don't match a shape, and something still has to decide which of the machine's findings matter and which it missed. That something is the picture of the system in your head.

## But the compiler

The obvious objection is that this is the assembly argument wearing new clothes: nobody reads assembly, the abstraction won, and complaining about it is just nostalgia with a technical vocabulary.

I think the difference is real, and it's the entire point. We stop looking underneath a layer, a compiler, a garbage collector, someone else's merged pull request, when its failures are rare enough and cheap enough to catch downstream, not because it's provably correct: the compiler earns that trust, and when it's wrong, that's a famous bug with a ticket number. An LLM hasn't earned it, its failure surface is unbounded and shaped by the context you're in, so the bet that mistakes will be rare and caught downstream doesn't hold, and something you have to check on those terms is not an abstraction, it's a collaborator, and to review a collaborator's work at one level you need to understand the level below it.

The second objection is that the models will get better and this is all temporary. I'm not going to bet against that, it's a bad bet and I don't need it, but better generation doesn't dissolve the problem, it moves it up a level: the more capable the writer, the more you're checking work that looks superhuman, and checking a collaborator you can't out-reason still means understanding the level it works at, so verification doesn't get free just because generation does. And underneath even flawless verification there's a floor no model reaches for you: somebody has to say what to build, which trade-offs are acceptable, and what "correct" means for these users, and you can't prompt your way to that if you don't already know it. The better the tools get at the _how_, the more everything depends on the _what_.

## What's actually left

Not syntax, not writing loops from memory: on that, the optimists are right, and it would be silly to defend it. When I say you still need to know how to code, I mean you need to be able to read it and reason about it, to hold what it's doing in your head well enough to tell right from plausible; writing it was only ever the way most of us learned to do that.

What's left is the model in your head that lets you find your own ignorance: knowing where to look, which question collapses the thing, when green isn't enough. That was never omniscience; I don't understand every line I get back either, and I don't understand every instruction my compiler emits, but the difference is that I know when I don't understand something, and roughly where to point the torch.

Though I'll admit I can't draw that line precisely, and I'm suspicious of anyone who says they can. I've stopped looking underneath the compiler entirely; I still look underneath the model, every time. Somewhere between those two there's a threshold where checking stops being worth it, and I don't know how you'd recognise it from the inside; you'd only find out afterwards, from the thing you failed to catch.

None of this is about juniors, it applies to me at least as much: the tool has no idea how long you've been doing this, and leaning on it without the underlying model produces the same class of mistake regardless. But there's an uncomfortable version I don't want to skip: the model in your head got built by writing and debugging the very things the tool now does for you, and if you start out leaning on it, rationally, because it's faster and cleaner than your first pass, you may never build the model at all, and I don't have a tidy answer to that, I just don't think the answer is to pretend the skill stopped mattering.

That's the part worth keeping in mind: the tool multiplies whatever you bring, and it is extremely relaxed about what that is.
