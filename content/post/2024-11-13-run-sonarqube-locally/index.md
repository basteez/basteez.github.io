---
title: How to Use SonarQube and SonarScanner Locally to Level Up Your Code Quality
draft: false
tags:
  - devops
  - docker
categories:
  - devops
comments: true
date: 2024-11-13
---
Code quality tools can make a huge difference in improving your coding skills by helping you identify code smells, bugs, and potential vulnerabilities. 

In this guide, we’ll explore how to set up **SonarQube** and **SonarScanner** locally. This allows you to analyze your code for potential improvements right on your machine.

### Step 1: Setting Up SonarQube with Docker

First, ensure you have Docker installed. With Docker, getting SonarQube up and running is straightforward:

1. **Pull the SonarQube image**:
    
    bash
    
    Copia codice
    
    `docker pull sonarqube`
    
2. **Run SonarQube**:
    
    bash
    
    Copia codice
    
    `docker run -d --name sonarqube -p 9000:9000 -p 9092:9092 sonarqube`
    
    This command runs SonarQube in the background, mapping port `9000` (for the SonarQube web interface) and `9092` (optional).
    

### Step 2: Accessing SonarQube

With SonarQube running, open your browser and go to [http://localhost:9000](http://localhost:9000). Enter the default credentials:

- **Username**: `admin`
- **Password**: `admin`

Once logged in, you will be prompted to change the default password.

### Step 3: Generate an Authentication Token

To allow SonarScanner to connect to SonarQube, you need to create an authentication token.

1. Click the **A** icon in the top-right corner and select **My Account**.
2. Navigate to the **Security** tab and click **Generate a token**.
3. Name your token (it can be user-specific or global) and save it somewhere secure, as it will only be displayed once.

### Step 4: Configure `sonar-project.properties`

Next, set up a configuration file to define key project properties SonarQube will use to analyze your code. In the root directory of your project, create a file named `sonar-project.properties` and add the following content:


```yaml
sonar.projectKey=my:project # Must be unique 
sonar.projectName=my project name 
sonar.projectVersion=1.0 sonar.sources=src/main/java # Adjust based on your source directory 
sonar.java.binaries=target/classes  # Adjust based on your compiled classes 
sonar.tests=src/test/java # Adjust based on your test directory
```

This configuration file tells SonarQube about the structure and setup of your project.

### Step 5: Run SonarScanner

With everything set up, it’s time to analyze your project. Open a terminal at the root of your project and execute the following command:

```bash
mvn clean install && \
mvn dependency:copy-dependencies && \
docker run \
    --rm \
    --network host \
    -e SONAR_HOST_URL="http://{YOUR LOCAL IP}:9000" \
    -e SONAR_TOKEN="{YOUR SONARQUBE TOKEN}" \
    -v "$(pwd):/usr/src" \
    sonarsource/sonar-scanner-cli

```

This command does the following:

- Cleans and builds your project using Maven (`mvn clean install`).
- Copies dependencies needed for analysis.
- Runs SonarScanner in a Docker container and connects it to your local SonarQube instance.

Replace `{YOUR LOCAL IP}` with your machine’s local IP address and `{YOUR SONARQUBE TOKEN}` with the token you generated in Step 4.

### Step 6: Review the Analysis Results in SonarQube

Once SonarScanner completes its run, return to [http://localhost:9000](http://localhost:9000) and navigate to your project dashboard. Here, you’ll see a detailed report on:

- **Code smells**: Areas of the codebase that could benefit from refactoring.
- **Bugs**: Logical errors or anomalies in the code.
- **Vulnerabilities**: Security-related issues.

### Conclusion

Setting up SonarQube and SonarScanner locally allows you to take your code quality analysis into your own hands. Regularly reviewing these reports can help you develop better habits, improve your understanding of code quality principles, and ultimately level up your coding skills.