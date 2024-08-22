---
title: Goodbye Wordpress, welcome Hugo!
tags:
  - postman
categories:
  - development-tools
comments: true
date: 2024-08-19
---
I've been looking for a quick and possibly "distraction-free" system to get back to writing on my blog for a while.

WordPress had become slow and unmanageable, and with each update, it got worse and worse (probably my fault, but I neither had the time nor the desire to figure out the cause), so I thought: "What if I try [Hugo](https://gohugo.io/)?"

After all, using WordPress, for what I do, is like using a _*insert expensive car brand here*_ to go grocery shopping at a discount store: for instance, I don't need comments on my posts, social media already provides that, and I don't want to spend too much time managing security, drafts, cache, etc.

> EDIT: I added disqus comments, just in case

A static site is perfect for what I need, and that's where [Hugo](https://gohugo.io/) comes in, which I hope will help me gain in:

- Speed and performance
- Control over content
- Security
- Costs

> I will definitely do another post in the future to summarize this choice.

## Speed and Performance

Even if you try to keep things minimal, with WordPress you still have to add plugins to manage certain aspects, like cache and SEO, and each plugin you add tends to slow down the platform a bit.

Additionally, I'm not sure if it's an issue with my hosting, Cloudflare, or who knows what, but lately I noticed that my WordPress blog was taking up to 20 seconds to load a simple page, despite having cache and Cloudflare's CDN.

[Hugo](https://gohugo.io/), on the other hand, generates static content, which means no database, no processes running at page load, and no backend queries. You open the page, and it's served to you as static content.

## Control over Content

Sure, WordPress is powerful and flexible, but after a while, I noticed I was spending more time managing WordPress itself than creating content, and that’s not good.

With [Hugo](https://gohugo.io/), I just have to write markdown files to publish on GitHub Pages—nothing more, nothing less.

By the way, I found a way to integrate [Obsidian](https://obsidian.md/) with templates and daily notes, so I can automatically create a markdown template for the day's post and start from there without having to copy and paste common parts from other files. It couldn’t be more convenient...

## Security and Costs

As mentioned earlier, I no longer need a backend or a database, which automatically improves security and reduces costs.

---

In conclusion, switching from WordPress to [Hugo](https://gohugo.io/) was a decision driven by my need for speed, control, security, and simplicity. WordPress remains an excellent platform for many, but for someone like me who seeks a lighter, more minimalist approach to blogging, [Hugo](https://gohugo.io/) looks like a perfect solution.