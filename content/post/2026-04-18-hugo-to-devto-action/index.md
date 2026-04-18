---
title: "Crossposting without the copy-paste: a GitHub Action from Hugo to dev.to"
date: 2026-04-18
draft: false
categories:
  - dev
tags:
  - hugo
  - devto
  - github-actions
  - automation
comments: true
---

My blog runs on Hugo. I also recently discovered I can cross-post to [dev.to](https://dev.to), because that's where a lot of the conversation actually happens. For a while, my workflow was the obvious one: write the post, publish it here, open dev.to, paste it in, fix the frontmatter, fix the links, hit publish.

It worked. I also stopped doing it after the second post.

Copy-paste friction is the kind of chore that silently kills a publishing habit. So I did what most developers do when a task becomes repetitive: I automated it. And then I kept refining the automation until it was worth giving away.

The result is [`basteez/hugo-to-devto-action`](https://github.com/basteez/hugo-to-devto-action), now [published on the GitHub Marketplace](https://github.com/marketplace/actions/hugo-to-dev-to-crosspost).

## What it does

It's a composite GitHub Action. On every push to your blog repo, it looks at what changed in the push range, finds new Hugo posts under your `content/post` directory, and creates a corresponding **draft** on dev.to for each one that is marked `draft: false` locally.

Key behaviours, chosen deliberately:

- **Drafts, not published posts.** The action never hits publish on dev.to for you. It mirrors content, but you stay in control of when it goes live on the other platform. This is intentional: dev.to has its own audience, its own timing, and its own editorial choices (cover image, tags, canonical URL). I want a starting point there
- **Dedup by title.** Before creating a draft, the action queries your dev.to account and skips anything whose title already exists. That means you can safely re-run on any push without ending up with duplicates, and editing a post on dev.to directly doesn't get overwritten.
- **Push-range aware.** It uses `git diff` across `github.event.before..github.event.after` to find what actually changed, rather than scanning the whole repo every time. New posts get mirrored; edits to old posts don't trigger spurious drafts.
- **Stateless.** There is no database, no cache, no state file in your repo. dev.to is the source of truth for "does this already exist?" If you ever want to start fresh, you can.

## Using it

The minimum viable workflow is about fifteen lines:

```yaml
name: Crosspost to dev.to

on:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  crosspost:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: basteez/hugo-to-devto-action@v1
        with:
          devto-api-key: ${{ secrets.DEVTO_API_KEY }}
          before: ${{ github.event.before }}
          after: ${{ github.event.after }}
```

Two things to watch for:

1. **`fetch-depth: 0` is not optional.** The default shallow checkout doesn't contain the `before` SHA of a real push, so `git diff` has nothing to compare against. If you leave this out, the action will fail quickly and loudly. That failure mode is well understood; don't go hunting for a mysterious bug.
2. **`DEVTO_API_KEY` lives in repo secrets.** Grab a Personal API Key from dev.to (Settings → Extensions → DEV Community API Keys) and add it as `DEVTO_API_KEY` under your repo's secrets. The action forwards it into the child process; it's never logged.

If your posts live somewhere other than `content/post`, pass `post-dir:` with the path. If you want to see what would happen without actually creating drafts, pass `dry-run: 'true'`. That's the whole surface area.

## A word on versioning

I went with the GitHub convention of three pin styles:

- `@v1` — a moving tag that tracks the latest non-breaking release. Bug fixes and additive features land automatically. This is what most people want.
- `@v1.x.y` — a full semver pin if you need an immutable reference.
- `@<commit-sha>` — a 40-character SHA for organisations that mandate commit-level pinning.

The `v1` tag will **never** be force-updated to a breaking release. Breaking changes bump to `@v2`. That way, the convenient default is also the safe default.

## Why bother extracting it

This started life as a script in this blog's own repo. It worked fine there. Extracting it into a standalone action was more work than copy-pasting a script into other Hugo repos would have been.

I did it anyway, for three reasons.

First, **separation of concerns.** The crosspost logic has nothing to do with my blog content. Keeping them in the same repo was mixing "what I publish" with "how I publish it," and every time I touched one, I had to reason about the other.

Second, **reuse.** I'm not the only person running a Hugo blog who'd like to mirror to dev.to. If the tool exists in a shareable form, other people can use it without forking my blog.

Third, and this is the part I didn't expect, **extraction forces clarity.** When code is hiding inside your own repo, you get to take a lot of context for granted. The directory layout, the branching model, the workflow triggers, the assumptions about what's already installed. Turning it into a public action meant writing all of that down as explicit inputs, documented defaults, and failure modes. The code ended up smaller and sharper.

That last point keeps showing up in my work, and I think it's worth naming: the act of making something reusable is often more valuable for the original project than for anyone who'll reuse it.

## What's next

A few directions I'm considering, in rough priority order:

- Optional publish mode, for people who genuinely do want one-click mirroring.
- Better handling of images and relative links, which is currently the biggest rough edge.
- Support for other destinations (Hashnode, Medium), though I'd rather keep this action focused and spin up siblings than turn it into a universal crossposter.

If any of this is useful to you, grab it from the [Marketplace](https://github.com/marketplace/actions/hugo-to-dev-to-crosspost) or reference it directly as `basteez/hugo-to-devto-action@v1`. Bug reports and PRs are welcome on [GitHub](https://github.com/basteez/hugo-to-devto-action).

And if this post shows up on my dev.to profile before I get around to publishing it there, you'll know the action works.
