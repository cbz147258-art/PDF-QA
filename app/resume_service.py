"""
Resume optimization service - LangChain ChatOpenAI powered
==========================================================
Professional resume parsing, analysis, and optimization with multiple strategies.
"""
from langchain_core.messages import SystemMessage, HumanMessage
from app.deepseek_client import llm


class ResumeParser:
    """Resume parser: auto-detect sections in a resume"""

    SECTION_PATTERNS = {
        "personal": ["Personal Info", "Contact", "Profile"],
        "education": ["Education", "School", "University"],
        "experience": ["Experience", "Work", "Employment", "Projects"],
        "skills": ["Skills", "Tech Stack", "Core Skills", "Expertise"],
        "projects": ["Projects", "Portfolio"],
        "certificates": ["Certificates", "Certifications"],
        "languages": ["Languages"],
        "self_eval": ["Summary", "Objective", "About Me"],
    }

    @classmethod
    def parse(cls, text: str) -> dict:
        lines = text.split("\n")
        sections = {}
        current_section = "header"

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            matched = False
            for section_name, keywords in cls.SECTION_PATTERNS.items():
                if any(kw.lower() in line_stripped.lower() for kw in keywords):
                    current_section = section_name
                    matched = True
                    break

            if current_section not in sections:
                sections[current_section] = []
            if not matched:
                sections[current_section].append(line_stripped)

        if "experience" in sections:
            sections.setdefault("projects", [])
            sections["projects"] = sections.get("projects", []) + sections["experience"]

        return sections


class ResumeAnalyzer:
    """Resume analyzer using LangChain ChatOpenAI"""

    @staticmethod
    async def analyze(text: str) -> str:
        prompt = f"""You are a senior HR and technical interviewer. Please provide a comprehensive professional analysis of the following resume.

Analysis dimensions (follow this format strictly):

## 1. Overall Score
Give a score from 1-10 with brief reasoning.

## 2. Structure & Layout
- Is the layout clear?
- Is information hierarchy logical?
- Is length appropriate?

## 3. Content Quality
### 3.1 Project Experience
- Does it use STAR method?
- Are there quantified metrics?
- Are descriptions specific?

### 3.2 Skills Description
- Is the skills list clear?
- Are proficiency levels distinguished?

### 3.3 Work Experience
- Are responsibilities clearly described?
- Are achievements reflected?

## 4. Highlights
List 3-5 most outstanding highlights.

## 5. Key Weaknesses
List 3-5 key areas for improvement.

## 6. Specific Improvement Suggestions
Actionable suggestions for each weakness.

## 7. Suitable Job Directions
Recommend suitable job types based on the resume.

---

Resume content:
{text}

Ensure the analysis is professional, specific, and constructive."""

        response = await llm.ainvoke([
            SystemMessage(content="You are a senior HR and technical interviewer, skilled in resume evaluation and career planning."),
            HumanMessage(content=prompt),
        ])
        return response.content


class ResumeOptimizer:
    """Resume optimizer with multiple strategies using LangChain ChatOpenAI"""

    STRATEGIES = {
        "general": {
            "name": "General Optimization",
            "desc": "Smoother language, clearer logic, better formatting",
            "focus": "Language expression and logical structure",
        },
        "professional": {
            "name": "Professional Style",
            "desc": "Precise wording, formal tone, highlight results and data",
            "focus": "Business professional expression and result quantification",
        },
        "technical": {
            "name": "Technical Emphasis",
            "desc": "Emphasize tech stack depth, project architecture, quantified performance metrics",
            "focus": "Technical depth and engineering capability",
        },
        "position": {
            "name": "Position-Specific",
            "desc": "Customized optimization for target job requirements",
            "focus": "Job matching",
        },
    }

    @staticmethod
    def _build_system_prompt(original: str, target: str, position: str = "") -> str:
        strategy = ResumeOptimizer.STRATEGIES.get(target, ResumeOptimizer.STRATEGIES["general"])

        prompt = f"""You are a top resume optimization expert. Please professionally optimize the user's resume.

## Optimization Direction: {strategy["name"]}
{strategy["desc"]}

## Core Requirements
1. **Factual Integrity**: Do not modify any factual information (name, company, dates, tech names, etc.)
2. **STAR Method**: Rewrite project experience using Situation-Task-Action-Result structure
3. **Data Quantification**: Add quantifiable achievement metrics where possible
4. **Keyword Optimization**: Use industry-standard professional terminology
5. **ATS Friendly**: Ensure the resume can be correctly parsed by automated screening systems
6. **Formatting**: Maintain clear section hierarchy, separate sections with ---

## Output Format
Please output the optimized resume strictly following this structure:

[Personal Info]
(optimized content)

[Education]
(optimized content)

[Work/Project Experience]
(optimized content, use STAR method for each project)

[Skills]
(optimized content, categorized by proficiency level)

[Summary]
(optimized content)

---
[Optimization Notes]
- Key changes:
- Optimization highlights:
- Targeted suggestions:"""

        if target == "position" and position:
            prompt += f"""

## Target Position
{position}

Please optimize for this position, ensuring high keyword match with the JD."""

        prompt += f"""

## Original Resume
{original}"""

        return prompt

    @staticmethod
    async def optimize(text: str, target: str = "general", position: str = "") -> dict:
        strategy = ResumeOptimizer.STRATEGIES.get(target, ResumeOptimizer.STRATEGIES["general"])

        system_prompt = ResumeOptimizer._build_system_prompt(text, target, position)

        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Please optimize my resume in the '{strategy['name']}' direction, focusing on '{strategy['focus']}'"),
        ])
        optimized = response.content

        return {
            "original": text,
            "optimized": optimized,
            "strategy": target,
            "strategy_name": strategy["name"],
        }

    @staticmethod
    async def optimize_section(text: str, section: str, target: str = "general") -> str:
        """Optimize a specific section of the resume"""
        section_names = {
            "project": "Project Experience",
            "skill": "Skills",
            "summary": "Self Summary",
            "education": "Education",
        }
        section_name = section_names.get(section, section)

        prompt = f"""You are a resume optimization expert. Please specifically optimize the '{section_name}' section of the following resume.

Optimization direction: Make it more professional and attractive
Requirements:
1. Do not change factual information
2. Use more professional expressions
3. Use STAR method for project experience
4. Add quantified data where the original has relevant data

Original text to optimize:
{text}

Output ONLY the optimized '{section_name}' section content. Do not add any other explanations."""

        response = await llm.ainvoke([
            SystemMessage(content="You are a resume optimization expert."),
            HumanMessage(content=prompt),
        ])
        return response.content


class ResumeService:
    """Resume optimization service - unified entry point"""

    def __init__(self):
        self.parser = ResumeParser()
        self.analyzer = ResumeAnalyzer()
        self.optimizer = ResumeOptimizer()

    async def analyze(self, text: str) -> dict:
        sections = self.parser.parse(text)
        analysis = await self.analyzer.analyze(text)
        return {
            "sections": sections,
            "analysis": analysis,
        }

    async def optimize(self, text: str, target: str = "general", position: str = "") -> dict:
        return await self.optimizer.optimize(text, target, position)

    async def optimize_section(self, text: str, section: str, target: str = "general") -> str:
        return await self.optimizer.optimize_section(text, section, target)