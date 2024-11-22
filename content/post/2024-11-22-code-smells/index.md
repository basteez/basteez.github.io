---
title: "Code Smells: Learn to Sniff Them Out"
draft: true
tags:
  - clean-code
  - java
categories:
  - dev
comments: true
date: 2024-11-22
---
"Code smells" are subtle indicators of underlying problems in your codebase. They don’t crash your app or throw errors but can lead to long-term maintainability issues if left unaddressed. Let’s dive into **what code smells are**, **examples of common smells**, and **how to clean them up.**

---

## What Are Code Smells?

- Coined by Martin Fowler in [_Refactoring: Improving the Design of Existing Code_](https://amzn.eu/d/fxygxXO), code smells are symptoms of poor design or coding practices.
- They signal that **something might need refactoring**, even if it technically works.

🧠 **Think of them as warning signs, not bugs.** A bug means something is broken; a smell means your design could use improvement.

---

## Common Code Smells and How to Fix Them

### Long Methods

- **The Smell**: A single method tries to do too much (e.g., 200+ lines of code).
- **Why It’s Bad**: Hard to read, test, and debug.
- **Fix**: Break the method into smaller, single-purpose methods. Use meaningful names to make their purpose clear.

**Before:**

```java
public void processOrder(Order order) {     
	// Code for validating order     
	// Code for applying discounts     
	// Code for calculating total     
	// Code for sending confirmation email }
```

**After:**

```java
public void processOrder(Order order) {     
	validateOrder(order);     
	applyDiscounts(order);     
	calculateTotal(order);     
	sendConfirmation(order); 
}
```

---

### Large Classes (God Objects)

- **The Smell**: A class tries to handle too many responsibilities.
- **Why It’s Bad**: Violates the Single Responsibility Principle (SRP). Hard to maintain and extend.
- **Fix**: Split the class into smaller, more focused classes. Use patterns like **composition** or **delegation**.

**Before:**

```java
public class UserManager {     
	public void createUser() { ... }     
	public void validateUser() { ... }     
	public void sendEmail() { ... }     
	public void logActivity() { ... } 
}
```

**After:**

```java
public class UserService {
	public void createUser() { ... } 
}
---
public class UserValidator {
	public void validateUser() { ... } 
}

---
public class EmailService {
	public void sendEmail() { ... } 
}
```

---

### Magic Numbers and Strings

- **The Smell**: Unexplained hard-coded values scattered throughout your code.
- **Why It’s Bad**: Makes code confusing and harder to maintain.
- **Fix**: Replace them with constants or enums.

**Before:**

```java
if (status == 3) { ... }
````  

**After:**

```java
private static final int STATUS_APPROVED = 3; 
...
...
if (status == STATUS_APPROVED) { ... }
```

---

### Duplicate Code

- **The Smell**: Identical or nearly identical code blocks in multiple places.
- **Why It’s Bad**: Increases maintenance effort. Changes in one place need to be replicated everywhere.
- **Fix**: Abstract the duplicated logic into a reusable method or class.

**Before:**

```java
public int calculateDiscount(int price) {     
	return price * 10 / 100; 
} 

public int calculateTax(int price) {
	return price * 10 / 100; 
}
```

**After:**

```java
public int applyPercentage(int price, int percentage) {
	return price * percentage / 100; 
}
```

---

### Long Parameter Lists

- **The Smell**: Methods or constructors take too many parameters.
- **Why It’s Bad**: Makes code harder to understand and prone to errors when calling.
- **Fix**: Use an object to encapsulate related parameters.

**Before:**

```java
public void createOrder(String product, int quantity, double price, String customerName, String address) { ... }
```

**After:**

```java
public void createOrder(OrderRequest request) { ... }
```

---

## Tools to Detect Code Smells

1. [**SonarQube**](https://bstz.it/p/how-to-use-sonarqube-and-sonarscanner-locally-to-level-up-your-code-quality/): Analyzes code quality and detects common smells.
2. **IntelliJ IDEA**: Built-in inspections flag potential issues like long methods or God objects.
3. **Refactoring Books**: [_Refactoring: Improving the Design of Existing Code_](https://amzn.eu/d/fxygxXO) by Martin Fowler is a must-read!

---

## Actionable Tips to Avoid Code Smells

1. **Start Small**: Refactor one smell at a time.
2. **Embrace Code Reviews**: Fresh eyes can spot smells you’ve become blind to.
3. **Automate Tests**: Refactoring is less scary when you have a safety net of tests.
4. **Follow SOLID Principles**: Adhering to these can prevent many smells in the first place.

---

💡 **Takeaway**: Code smells are inevitable as your codebase grows, but catching and addressing them early can save you from costly rewrites later.