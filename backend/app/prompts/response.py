"""Prompts for the response node - generates comprehensive curriculum research output."""

RESPONSE_SYSTEM_PROMPT = """You are generating a competitor research report. LIST EVERY SINGLE COURSE.

# {INDUSTRY} - Competitor Course Research Report

## Summary
- **Total Courses:** [X]
- **Price Range:** [X to Y]
- **Platforms:** [list]

---

## ALL COURSES (List every single one - do NOT skip any!)

**YOU MUST LIST ALL COURSES BELOW. If you found 30 courses, list all 30. Do NOT summarize.**

### Course 1: [Name]
- **Platform:** [X] | **Price:** [X] | **Duration:** [X]
- **Rating:** [X] | **Students:** [X] | **Cert:** [X]
- **URL:** [X]
- **Modules:** [Module 1], [Module 2], [Module 3], [Module 4], [Module 5]

### Course 2: [Name]
[Same format]

### Course 3: [Name]
[Same format]

... Continue for ALL courses (Course 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, etc.)

---

## Module Inventory

### VITAL (5+ courses)
- **[Module]** - [Description]. Found in: [courses]

### HIGH (3-4 courses)
- **[Module]** - [Description]. Found in: [courses]

### MEDIUM (2 courses)
- **[Module]** - [Description]. Found in: [courses]

### NICHE (1 course)
- **[Module]** - [Description]. Found in: [course]

---

## Key Insights
- **Certifications:** [analysis]
- **Pricing:** [analysis]
- **Gaps:** [analysis]

---

CRITICAL RULES:
1. List EVERY course found - number them sequentially (Course 1, Course 2, ... Course 30)
2. Each course needs: Platform, Price, Duration, Rating, Students, Certification, URL, Modules
3. Do NOT say "and more..." or skip courses
4. The report must include ALL courses
"""

RESPONSE_USER_PROMPT = """## Research Data

**Industry:** {industry}

{research_context}

---

## GENERATE THE FULL REPORT

List EVERY course above as numbered entries (Course 1, Course 2, Course 3, etc.)
Do NOT skip any courses. If there are 30 courses in the data, list all 30.
"""
