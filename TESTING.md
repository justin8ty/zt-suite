# CHAPTER 6: TESTING AND EVALUATION (CYBERSECURITY)

## Introduction

**Purpose:** Demonstrate the reliability, functionality, and quality assurance of the system or solution developed.

**Validation:** Validates that the system works as intended and meets user, project, or security requirements.

## 6.1 Unit Testing

**Scope:** Required if software modules were developed. Includes individual units and modules tested to identify bugs and security vulnerabilities.

**Presentation:** Must be displayed in tables.

### 6.1.1 Test Plan

**Table 6.1: Test Plan for Core Modules (Template Example)**

| Module | Test ID | Function | Test Date |
|--------|---------|----------|------------|
| Admin / Auth | 1 | T01 – Manage branches / Access Control | 4.06.2023 |
| Admin / Auth | 2 | T02 – Manage user roles | 4.06.2023 |
| Admin / Auth | 3 | T03 – View Calendars (all branches) | 8.06.2023 |

### 6.1.2 Test Data

**Table 6.5: Test Data Summary (Template Example)**

| Module | Test Case | Function / Description | Relevant Test Data |
|--------|-----------|------------------------|--------------------|
| Admin / Auth | T01 | Manage branches / Access Control | Name, Address, State, Phone Number |
| Admin / Auth | T02 | Manage user roles | Username, Password, Email, Role, Branch |

### 6.1.3 Test Results

**Table 6.6: Test Case Execution (Authentication Example)**

| Field | Details |
|-------|---------|
| Test Case ID | T17 |
| Description | Check user login to validate existing users in accordance to user roles |
| Precondition | A valid user account is available in the system |
| Post Conditions | The user is successfully logged into the application and granted role‑specific features. |
| Test Script / Steps | 1. Launch the application.<br>2. Enter a valid username and password.<br>3. Click on the "Login" button.<br>4. Verify redirection to the correct dashboard and role‑specific feature sets. |
| Expected Result | User should be able to log in to the respective user dashboard |
| Actual Results | Successful login and dashboard restriction based on roles |

**Table 6.2: Logic and Exception Unit Testing (Template Example)**

| # | Test Case | Test to execute | Expected results | Actual results | Evaluation |
|--|-----------|----------------|------------------|----------------|------------|
| 1 | Database Connection | Verify secure DB connection | "Connected" status displayed | Connected successfully | Successful |
| 2 | ID Generation Input | Click button to generate token/ID | Unique cryptographic ID generated | Successfully generated unique ID | Successful |
| 3 | Duplicate Prevention | Attempt duplicate ID generation | Regulate or throw error to prevent duplication | Application crash / loop validation failure | Failed (Needs loop fix) |

## 6.2 Integration Testing

**Definition:** Verifies the interaction between components or systems, specifically emphasizing deployment within secured environments.

**Table 6.4: Integration Testing Matrix**

| # | Test Case | Units integrated | Test to execute test cases | Expected results | Actual results |
|--|-----------|------------------|----------------------------|------------------|----------------|
| 1 | Gateway Connection | Auth Module & Protected APIs | Call secure endpoints with valid token | Authorized access redirected to target page | Interface loaded successfully |

## 6.3 System Testing

**Definition:** Validates the complete, integrated system to ensure overall functionality, performance, and robustness.

**Table 6.7: System Testing vs. Objectives**

| # | System Requirement / Objective | Actual Developed Function |
|--|--------------------------------|---------------------------|
| 1 | Provide secure, end‑to‑end management and reporting. | Centralized interface can be managed with structured access control. Reports are generated via filtered parameters. |

## 6.4 Security Testing

### 6.4.1 Vulnerability Assessment

- **Tools Used:** Documentation of deployment infrastructure scanners (e.g., Nessus, OpenVAS, Nikto).
- **Findings:** Summary of discovered vulnerabilities categorized by severity.

### 6.4.2 Penetration Testing

- **Scope & Attack Vectors:** Scope definitions, specific testing tools utilized (e.g., Metasploit, Burp Suite), and target attack vectors.
- **Outcomes:** Comprehensive log of exploits attempted and their direct outcomes.

### 6.4.3 Risk Assessment

- **Matrix:** Classification of risk levels (High, Medium, Low) paired with associated mitigation strategies.

## 6.5 Compliance or Policy Testing

- **Security Standards:** Documented testing of adherence to specific industry security standards (e.g., OWASP Top 10, ISO 27001, NIST).
- **Control Checks:** Programmatic checks validating password strength policies, role‑based access control (RBAC), data encryption‑at‑rest/in‑transit, and comprehensive audit logging.

## 6.6 Acceptance Testing

**Definition:** Final validation verifying that the system meets functional and explicitly stated security requirements.

**Evaluators:** Evaluated and signed off by the client, supervisor, or intended stakeholder base.

**Table 6.9: Security Sign‑off / Acceptance Test**

| Field | Details |
|-------|---------|
| Tester | Client / Target System Administrator |
| Test date | DD‑MM‑YYYY |
| Test Objective | Validate access restriction policy mechanisms |
| Expected Test Outputs | Redirection or block message when invalid permissions are verified |
| Actual Test Results | System successfully enforced policy blocks according to permissions |
