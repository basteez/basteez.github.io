---
title: Singleton pattern thread-safety in java
draft: false
tags:
  - java
  - creational-patterns
categories:
  - design-patterns
comments: true
date: 2024-09-04
---
As stated in [this article]({{% ref "2024-09-04-design-pattern-singleton" %}}), **singleton** is not thread-safe by default. Let's see how to make it thread-safe.

## Basic singleton class
First, let's recap how to create a basic singleton:

```java
public class Singleton {
	private static Singleton instance;

	private Singleton() {
		// initialization code
	}

	public static Singleton getInstance() {
		if(instance == null) {
			instance = new Singleton();
		}
		return instance;
	}
}
```

This implementation does not guarantee correct behavior in a multithreaded environment.

## How to make a singleton thread-safe

We can achieve **singleton thread-safety** in several ways:
1. Eager initialization
2. Lazy initialization with method synchronization
3. Double-checked initialization with synchronized block and volatile variable

### Eager initialization
In this approach, the instance is created when the class itself gets loaded in the application context to ensure thread-safety without relying on any synchronization mechanism.
However, it could lead to a waste of resources if the instance is never used, and it doesn’t allow passing parameters during instantiation.

```java
public class EagerSingleton {

    // Instance created at the time of class loading
    private static final EagerSingleton instance = new EagerSingleton();

    private EagerSingleton() {}

    public static EagerSingleton getInstance() {
        return instance;
    }
}

```

### Lazy initialization with method synchronization
This approach ensures thread safety by synchronizing the `getInstance()` method. However, this method can suffer from performance issues due to synchronization overhead on every call to `getInstance()`.
```java
public class SynchronizedSingleton {

    private static SynchronizedSingleton instance;

    private SynchronizedSingleton() {}

    // Synchronized method to control simultaneous access
    public static synchronized SynchronizedSingleton getInstance() {
        if (instance == null) {
            instance = new SynchronizedSingleton();
        }
        return instance;
    }
}
```
### Double-checked initialization with synchronized block and volatile variable
In this approach, similar the previous one, the synchronization overhead is reduced by synchronizing only the first time the instance is accessed.
The instance variable is marked as `volatile` to prevent the occurrence of partially constructed instances.

```java
public class DoubleCheckedSingleton {

    // volatile keyword ensures that multiple threads handle the instance variable correctly
    private static volatile DoubleCheckedSingleton instance;

    private DoubleCheckedSingleton() {}

    // Method to return the singleton instance with double-checked locking
    public static DoubleCheckedSingleton getInstance() {
        if (instance == null) { // First check without synchronization
            synchronized (DoubleCheckedSingleton.class) {
                if (instance == null) { // Second check with synchronization
                    instance = new DoubleCheckedSingleton();
                }
            }
        }
        return instance;
    }
}
```