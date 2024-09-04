---
title: "Design Patterns: Singleton"
draft: false
tags:
  - GoF
  - creational-patterns
categories:
  - design-patterns
comments: true
date: 2024-09-04
---
**Singleton** is a creational design pattern that ensures a class has only one instance and provides a global access point to that instance.
## Problem
In software development, it's common to need a single instance of a class to be shared across an application. Having multiple instances can lead to issues such as unexpected behaviors or inefficient resource usage.
## Solution
The **Singleton** pattern addresses this problem by:

- Making the class constructor private to prevent direct instantiation from outside the class.
- Providing a static public method that acts as a constructor. Before creating a new instance, it checks if an instance already exists in a private static field. If the field is `null`, it creates a new instance and assigns it to the field; otherwise, it returns the existing instance.

![SingletonDiagram.svg](SingletonDiagram.svg)
## Java example
```java
public class Singleton {
	private static Singleton instance;

	private Singleton() {
		// initialization code
	}

	public static Singleton getInstance() {
		if(intance == null) {
			instance = new Singleton();
		}
		return instance;
	}
}
```
## Applications
Use the **Singleton** pattern when you need a single instance of a class to be shared across the entire application.
## Tips
* Be careful when using the **Singleton** pattern in multi-threaded scenarios, as it is not inherently thread-safe. Check [this article]({{% ref "2024-09-04-singleton-thread-safety" %}}) for further details
