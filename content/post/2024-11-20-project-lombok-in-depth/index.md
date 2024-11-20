---
title: "An In-Depth Look at Project Lombok: A Follow-Up 🚀"
draft: false
tags:
  - java
categories:
  - dev
comments: true
date: 2024-11-20
---
Following up on [my earlier post about 𝗣𝗿𝗼𝗷𝗲𝗰𝘁 𝗟𝗼𝗺𝗯𝗼𝗸 on LinkedIn](https://www.linkedin.com/posts/tiziano-basile-264681147_projectlombok-java-cleancode-activity-7262501993489846272-MjPY?utm_source=share&utm_medium=member_desktop), let’s dive deeper into 𝘄𝗵𝘆 𝗟𝗼𝗺𝗯𝗼𝗸 𝗰𝗮𝗻 𝗯𝗲 𝗮 𝗯𝗹𝗲𝘀𝘀𝗶𝗻𝗴 𝗮𝗻𝗱 𝗮 𝗰𝘂𝗿𝘀𝗲 in your codebase.

## ✅ 𝗧𝗵𝗲 𝗚𝗼𝗼𝗱: 𝗪𝗵𝘆 𝗟𝗼𝗺𝗯𝗼𝗸 𝗦𝗵𝗶𝗻𝗲𝘀

### 𝗖𝗹𝗲𝗮𝗻𝗲𝗿, 𝗥𝗲𝗮𝗱𝗮𝗯𝗹𝗲 𝗖𝗼𝗱𝗲:
Lombok eliminates the need for repetitive methods like getters, setters, toString, and constructors.
With annotations like `@Getter`, `@Setter`, `@Builder`, and `@Data`, classes become concise and easier to understand.

### 𝗙𝗮𝘀𝘁𝗲𝗿 𝗗𝗲𝘃𝗲𝗹𝗼𝗽𝗺𝗲𝗻𝘁:
Focus on 𝘄𝗵𝗮𝘁 𝗺𝗮𝘁𝘁𝗲𝗿𝘀—business logic—while Lombok handles the repetitive tasks.

### 𝗜𝗺𝗽𝗿𝗼𝘃𝗲𝗱 𝗠𝗮𝗶𝗻𝘁𝗮𝗶𝗻𝗮𝗯𝗶𝗹𝗶𝘁𝘆
Changes to class fields automatically reflect in generated methods, reducing manual errors.
* @𝗘𝗾𝘂𝗮𝗹𝘀𝗔𝗻𝗱𝗛𝗮𝘀𝗵𝗖𝗼𝗱𝗲: No more tedious 𝘩𝘢𝘴𝘩𝘊𝘰𝘥𝘦 and 𝘦𝘲𝘶𝘢𝘭𝘴 implementations.
* @𝗕𝘂𝗶𝗹𝗱𝗲𝗿: Simplifies complex object creation with immutability.

### 𝗕𝗲𝘁𝘁𝗲𝗿 𝗖𝗼𝗱𝗲 𝗥𝗲𝘃𝗶𝗲𝘄𝘀:
Git diffs become cleaner since boilerplate is hidden. 𝗧𝗲𝗮𝗺𝘀 𝗰𝗮𝗻 𝘀𝗽𝗼𝘁 𝗺𝗲𝗮𝗻𝗶𝗻𝗴𝗳𝘂𝗹 𝗰𝗵𝗮𝗻𝗴𝗲𝘀 𝗳𝗮𝘀𝘁𝗲𝗿.

## ❌ 𝗧𝗵𝗲 𝗥𝗶𝘀𝗸𝘀 𝗮𝗻𝗱 𝗖𝗮𝘃𝗲𝗮𝘁𝘀 𝗼𝗳 𝗟𝗼𝗺𝗯𝗼𝗸

### 𝗧𝗿𝗮𝗻𝘀𝗽𝗮𝗿𝗲𝗻𝗰𝘆 𝗜𝘀𝘀𝘂𝗲𝘀:
Generated code isn’t visible in your editor unless you delve into decompiled classes.
* Can confuse 𝗻𝗲𝘄 𝘁𝗲𝗮𝗺 𝗺𝗲𝗺𝗯𝗲𝗿𝘀 or those unfamiliar with Lombok.
* Debugging becomes harder when stack traces point to 𝗶𝗻𝘃𝗶𝘀𝗶𝗯𝗹𝗲 𝗺𝗲𝘁𝗵𝗼𝗱𝘀.

### 𝗢𝘃𝗲𝗿𝘂𝘀𝗲 𝗼𝗳 𝗔𝗻𝗻𝗼𝘁𝗮𝘁𝗶𝗼𝗻𝘀:
Lombok can lead to 𝗰𝗼𝗱𝗲 𝗯𝗹𝗼𝗮𝘁 if misused:
* **@Data** generates `equals`, `hashCode`, `toString`, getters, setters, and a constructor—some of which might not be needed.
* This can impact 𝗽𝗲𝗿𝗳𝗼𝗿𝗺𝗮𝗻𝗰𝗲 or cause 𝘂𝗻𝗲𝘅𝗽𝗲𝗰𝘁𝗲𝗱 𝗯𝗲𝗵𝗮𝘃𝗶𝗼𝗿 (i.e @𝘛𝘰𝘚𝘵𝘳𝘪𝘯𝘨 in nested entities could easily lead to a 𝗦𝘁𝗮𝗰𝗸𝗢𝘃𝗲𝗿𝗙𝗹𝗼𝘄𝗘𝘅𝗰𝗲𝗽𝘁𝗶𝗼𝗻).

### 𝗧𝗼𝗼𝗹𝗶𝗻𝗴 𝗮𝗻𝗱 𝗖𝗼𝗺𝗽𝗮𝘁𝗶𝗯𝗶𝗹𝗶𝘁𝘆:
* IDEs or static analysis tools sometimes struggle with Lombok-generated code.
* Upgrading to new Java versions may introduce 𝗰𝗼𝗺𝗽𝗮𝘁𝗶𝗯𝗶𝗹𝗶𝘁𝘆 𝗶𝘀𝘀𝘂𝗲𝘀.

### 𝗗𝗲𝗽𝗲𝗻𝗱𝗲𝗻𝗰𝘆 𝗟𝗼𝗰𝗸-𝗜𝗻:
Removing Lombok later can be challenging, requiring significant rewrites.

### 𝗗𝗲𝗯𝘂𝗴𝗴𝗶𝗻𝗴 𝗛𝗲𝗮𝗱𝗮𝗰𝗵𝗲𝘀:
Lombok-generated code may not have clear stack traces, making debugging non-trivial.

## 𝗛𝗼𝘄 𝘁𝗼 𝗨𝘀𝗲 𝗟𝗼𝗺𝗯𝗼𝗸 𝗘𝗳𝗳𝗲𝗰𝘁𝗶𝘃𝗲𝗹𝘆

### 𝗕𝗲 𝗦𝗲𝗹𝗲𝗰𝘁𝗶𝘃𝗲 𝘄𝗶𝘁𝗵 𝗔𝗻𝗻𝗼𝘁𝗮𝘁𝗶𝗼𝗻𝘀:
* Use specific annotations like @𝘎𝘦𝘵𝘵𝘦𝘳 and @𝘚𝘦𝘵𝘵𝘦𝘳 instead of all-in-one annotations like @𝘋𝘢𝘵𝘢.
* Avoid unnecessary methods (e.g., don’t generate 𝘦𝘲𝘶𝘢𝘭𝘴/𝘩𝘢𝘴𝘩𝘊𝘰𝘥𝘦 unless required).

### 𝗨𝗻𝗱𝗲𝗿𝘀𝘁𝗮𝗻𝗱 𝘁𝗵𝗲 𝗚𝗲𝗻𝗲𝗿𝗮𝘁𝗲𝗱 𝗖𝗼𝗱𝗲:
* Use IDE features like decompile or delombok during builds to view generated code.
* Knowing what’s happening under the hood prevents surprises.

### 𝗣𝗹𝗮𝗻 𝗳𝗼𝗿 𝗟𝗼𝗻𝗴-𝗧𝗲𝗿𝗺 𝗠𝗮𝗶𝗻𝘁𝗲𝗻𝗮𝗻𝗰𝗲:
If you outgrow Lombok, a 𝗱𝗲𝗹𝗼𝗺𝗯𝗼𝗸 build step can help with the migration.

### Conclusion
𝗟𝗼𝗺𝗯𝗼𝗸 𝗶𝘀 𝗮 𝗽𝗼𝘄𝗲𝗿𝗳𝘂𝗹 𝘁𝗼𝗼𝗹, 𝗯𝘂𝘁 𝗶𝘁 𝗿𝗲𝗾𝘂𝗶𝗿𝗲𝘀 𝗿𝗲𝘀𝗽𝗼𝗻𝘀𝗶𝗯𝗹𝗲 𝘂𝘀𝗮𝗴𝗲. It’s a must-have for teams looking to streamline development, but only if the team is aligned and mindful of the caveats.
What’s your experience with Lombok? Are you using it effectively in your projects? Let’s discuss! 🧑💻