Challenge Statement 1:
AI Grandma Knows Best: Intelligent Self-Triage and Care Navigation

Introduction
Patients often struggle to decide whether symptoms can be managed at home, require a GP visit, or need urgent medical attention. This is especially challenging for older adults, people with chronic conditions, caregivers, and other vulnerable groups. AI can help patients understand symptoms, recognise warning signs, monitor changes, and navigate healthcare services more appropriately.

Problem Statement
How might we build an AI-powered self-triage assistant that helps patients understand what to do when they feel unwell, supports safe self-management, and identifies when professional or urgent care is needed?


Challenge
Build a patient-facing prototype that assesses symptoms and relevant context, recommends an appropriate level of care, provides self-care guidance where suitable, and monitors for changes that warrant escalation. Teams are encouraged to focus on a specific population or clinical scenario.

Below are some example scenarios:


Scenario 1: Pediatric Fever in an Infant (6–36 months)
A caregiver opens the app within 24 hours of detecting fever in a 6–36 month-old and enters temperature (with route), age, weight, associated symptoms (vomiting, rash, wet diapers, activity), and recent immunizations. The system tiers to four levels: ≥40°C or non-blanching rash, seizure, severe lethargy → ED now; ≥39°C or fever >72h → urgent care within 4h; mild symptoms → home care with weight-based acetaminophen/ibuprofen dosing and fluids, with re-checks every 8 hours and automated detection of any new red-flag symptom.

Scenario 2: Adult COVID-19 Symptom Screening and Triage
Adults ≥18 open the app within 48 hours of symptom onset or after a known close contact, reporting fever, cough, sore throat, anosmia/dysgeusia, dyspnea, and other symptoms along with self-measured temperature, SpO₂, respiratory rate, home rapid antigen result, vaccination status, and exposure history. The system tiers by oxygen thresholds: SpO₂ <90% at rest, RR
≥30, new chest pain, or confusion → 911 now; SpO₂ 90–93% or worsening dyspnea in high-risk comorbidities → same-day respiratory clinic; positive test or classic symptoms in high-risk patients (age ≥65, BMI ≥30, diabetes, CKD, immunosuppression, unvaccinated) → telehealth within 24 hours with a Paxlovid 5-day-window eligibility check; mild symptoms with SpO₂ ≥94%
→ home isolation, antipyretics, hydration, prone positioning, and daily SpO₂/symptom logs for 10 days, escalating to same-day care if SpO₂ drops ≥3 points from baseline or new dyspnea, chest pain, or biphasic fever appears


What the Solution Should Solve
The solution should address a meaningful challenge within the health or care journey and help users make better-informed decisions or take appropriate next steps, and should have following features:
•	Conversational assessment — gather symptoms, history and context naturally, handling
vague or incomplete input.
•	Care navigation — distinguish self-care, primary/community care, and urgent/emergency care with calibrated confidence.
•	Warning-sign detection — identify symptoms or combinations warranting prompt
professional attention.
•	Calibrated abstention — recognise and declare the limits of what it can assess.
•	Self-management support — practical guidance on monitoring and next steps.
•	Dynamic reassessment — update recommendations as symptoms or measurements change.
•	Personalisation — adapt to the chosen population, with fairness tested across subgroups. Strategic Guardrails for Participants - Dataset: necessary healthcare data can be found from open datasets, e.g., MIMIC-III or Kaggle.

The Solution Should Be
•	Safe: Clearly recognise situations requiring professional care and avoid inappropriate reassurance.
•	Patient-friendly: Communicate in clear, accessible language suitable for the target population.
•	Personalised: Consider relevant health history and individual circumstances.
•	Explainable: Tell users why a particular action is recommended.
•	Actionable: Help patients decide what to do next rather than simply provide information. The Solution Should Include
•	Demo Walkthrough – A live demonstration.
•	Architecture Diagram – architecture, trust-boundary diagram, key design trade-offs.
•	Source Code – Complete source code submitted through a GitHub repository.
Note: The features listed above are provided as guidance only. Participants are strongly encouraged to explore alternative approaches that meaningfully address the problem statement


Challenge Statement 2:
AI Healthier Every Day: Intelligent Support for Long-Term Self-Care

Introduction
Good health is shaped by what patients do every day between healthcare visits. People managing chronic conditions may need to understand multiple medications, monitor health indicators, follow treatment plans, attend screenings, and make sustainable lifestyle changes. The information is often fragmented and difficult to manage. AI offers an opportunity to turn these tasks into personalised, continuous self-care support.


Problem Statement
How might we build an AI-powered health companion that helps people understand and manage their medications, stay on track with their care, and take greater ownership of their long-term health?

Challenge Statement 2:
AI Healthier Every Day: Intelligent Support for Long-Term Self-Care

Introduction
Good health is shaped by what patients do every day between healthcare visits. People managing chronic conditions may need to understand multiple medications, monitor health indicators, follow treatment plans, attend screenings, and make sustainable lifestyle changes. The information is often fragmented and difficult to manage. AI offers an opportunity to turn these tasks into personalised, continuous self-care support.


Problem Statement
How might we build an AI-powered health companion that helps people understand and manage their medications, stay on track with their care, and take greater ownership of their long-term health?

What the Solution Should Solve
The solution should address a meaningful challenge people experience when managing their health over time. It should help users better understand and organise relevant health information, take appropriate actions, recognise when something may require further attention, and sustain healthy behaviours and routines. And it should have following features:
•	Medication understanding  —  Explain what medications are for and how they should be
taken in patient-friendly language.
•	Medication management  —  Help patients remember and sustain treatment routines while identifying barriers to adherence.
•	Adherence support  —  Help patients remember and sustain treatment routines while identifying barriers to adherence.
•	Health tracking  —  Interpret relevant measurements, symptoms or lifestyle information over time.
•	Preventive health  —  Surface relevant screening, vaccination, lifestyle or follow-up needs.
•	Healthcare Preparation  —  Help users identify concerns and questions to discuss with their doctor or pharmacist.
•	Strategic Guardrails for Participants - Dataset: necessary healthcare data can be found from open datasets, e.g., MIMIC-III or Kaggle.


7. Suggested Tools
Tencent Cloud WorkBuddy Ecosystem
The following tools are all accessible through WorkBuddy’s built-in ecosystem  —  no complex development environment setup required. Operate everything via natural language.

Area	Recommended Tools	Description


Agent Development	

Workbuddy	•	An AI-native workspace that enables users to build, deploy, and manage intelligent agents and automations through a natural-language interface, integrating large language models, MCP connectors, skills, and scheduling to automate real-world tasks
across business workflows.


Agent Development	

Codebuddy	•	Tencent Cloud's AI coding assistant that provides intelligent code completion, code review, debugging, and multi-file editing capabilities within the developer's IDE, accelerating software
development with context-aware suggestions.

Tencent Cloud Services Recommended for Hackathon Challenges


Area	Recommended Tools	Description



Agent Development	

Tencent Cloud Agent Development platform(ADP)	•	Tencent Cloud's foundational infrastructure for building AI agents at scale, offering model orchestration, sandboxed runtime environments, tool-calling frameworks, and extensible plugin ecosystems that allow developers to compose multi-agent systems with guardrails, RAG, and human-in-the-loop controls.


Agent runtime sandbox	

Tencent Cloud Agent Runtime	•	Agent Runtime uses a secure sandbox as its core execution environment, supporting millisecond-level startup and concurrency of tens of thousands of instances. It provides a secure, isolated, and high-performance execution foundation for AI Agents.

Speech & Voice	ASR from Tencent Cloud TRTC	•	Real-time and batch speech-to-text recognition with multi-accent support, used to transcribe spoken transaction commands into text for intent parsing.

Speech & Voice	TTS from Tencent Cloud TRTC	•	Natural text-to-speech synthesis for voice-based clarification prompts and confirmation overlays in the conversational banking experience.
Big Data / Database / Storage / Compute / Container / Network	
Tencent Cloud	
•	Tencent Cloud provides the full underlay infrastructure.


8. Project Submission Requirements

Project Basic Requirements
The project must be original and built on at least one of the products CodeBuddy or WorkBuddy.
Proof of product usage is mandatory: chat screenshots, API call logs, or a
written development-process description. Without proof, the project will not proceed to scoring.

Submission Requirements

Submission Items	Req.	Description
Project title	Required	•	The name of your AI Agent project
Short blurb	Required	•	A summary of what your project does or the value it delivers. Hard limit: under 10 words





Project Description	




Required	•	Project Overview: Target Scenarios, Users, and Value Proposition
•	Real-World Scenario Insights: Source of Pain Points, Target Audience, and Core Problems Solved
•	Comprehensive Solution Design: business and technical
architecture, and how prompts drive the AI generation.
•	Business Value: quantifiable metrics or clearly defined impact.
CodeBuddy / WorkBuddy Conversation History	
Required	•	The CodeBuddy / Workbuddy chat history used during the project development process
Cover Image	Required	•	A 16:9 cover image for your project, used for the online showcase. Recommended size: 380×216px.


Demo video	

Optional	•	A 5–8 minute video covering:
•	Project overview
•	Core Agent features and how it's used
•	A short reflection on your build approach and any development-tool tips

Chat history	
Required	•	Minimum of 3 screenshots of your chat logs from CodeBuddy or WorkBuddy during the development
process
Project link	Optional	•	A live URL or demo link for your project. Optional, but earns bonus points.
Other Requirements as per the Challenge
Statement	
Optional	•	Please check the respective challenge statement for specific requirements.


11. Judging Process
•	Preliminary Technical Judging: Each project will be evaluated by the respective industry organization that contributed the challenge statement and Tencent Cloud experts. As each track has different objectives and requirements, the detailed judging criteria will be shared with participants after registration.
•	Demo Day Grand Final: Representative teams from participating schools present their projects live at the offline roadshow. Judges score each project based on theme alignment, use of AI tools, and game quality, and select regional award winners and teams advancing to the grand final, please refer to the following:


Evaluation Dimension	
Score	
Key Review Focus

Impact & Relevance	
10 Points	Evaluate whether the project addresses a real-world problem and creates meaningful value.

Human-Centered Design	
10 Points	
Assess how well the solution is designed for real users.

AI Interaction	
10 Points	
Evaluate the quality and depth of AI usage in the project.

Technical Execution	
10 Points	
Assess the technical quality and completeness of the project.

Feasibility	
10 Points	Evaluate whether the project is realistic and scalable beyond the hackathon.

Demo & Storytelling	
10 Points	
Assess how effectively the project is presented and communicated.

Innovation & Creativity	
10 Points	
Evaluate the originality and uniqueness of the project.
User Experience (UX) & Accessibility	
10 Points	
Assess the overall usability and accessibility of the solution.
Responsible AI & Ethics	
10 Points	Evaluate whether the project demonstrates responsible and trustworthy AI practices.
Overall Quality & Judge's Impression	
10 Points	
Provide an overall assessment of the project.



