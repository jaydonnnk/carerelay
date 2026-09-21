# Mount Sinai's “Check Symptoms & Get Care” AI triage program

## Scope and source

This is a comprehensive, non-verbatim digest of the full signed-in article page, including its narrative sections, nine figures, two tables, author information, limitations, disclosures, and references. It excludes site navigation, advertisements, and unrelated recommended articles. Patient comments shown in Figure 8 are summarized rather than copied word for word.

- Source: [“Check Symptoms & Get Care”: Mount Sinai’s AI Triage Solution](https://catalyst.nejm.org/doi/full/10.1056/CAT.25.0394)
- Article type: Case Study
- Journal: *NEJM Catalyst Innovations in Care Delivery*
- Citation: 2026;7(8)
- DOI: 10.1056/CAT.25.0394
- Published online and in issue: July 15, 2026
- Page accessed: September 16, 2026
- Topics: artificial intelligence in health care; patient engagement; patient experience
- Copyright notice: © 2026 Massachusetts Medical Society; the page says the material is for personal use and commercial reuse requires permission.

## Authors and affiliations

1. **Bilal A. Naved, Ph.D.** — Eric and Wendy Schmidt AI in Human Health Fellow, Windreich Department of Artificial Intelligence and Human Health, Icahn School of Medicine at Mount Sinai; Chief Product Officer and cofounder, Clearstep Health; postdoctoral fellow, Department of Preventive Medicine and Bioinformatics, Northwestern University Feinberg School of Medicine.
2. **Minh Tran, M.Sc.** — Product Owner, Digital and Technology Partners, Mount Sinai Health System (MSHS).
3. **Quintan M. Slott, B.S.** — Senior Product Success Manager, Clearstep Health.
4. **Paul Francaviglia, B.S.** — Senior Director, Digital Experience, Department of Artificial Intelligence and Human Health, Icahn School of Medicine at Mount Sinai.
5. **Michael Amygdalidis, B.S.** — Chief Technology Officer, Clearstep Health.
6. **Phyllis Crandall, B.S.** — Director, Web Production, MSHS.
7. **Girish Nadkarni, M.D., M.P.H., C.P.H.** — Chair and Professor, Department of Artificial Intelligence and Human Health, Icahn School of Medicine at Mount Sinai; Chief AI Officer, MSHS.
8. **Robert Freeman, D.N.P., R.N.** — Chief Digital Transformation Officer, MSHS; ORCID 0000-0003-4946-6533.
9. **Yuan Luo, Ph.D.** — Professor, Department of Preventive Medicine and Bioinformatics, Northwestern University Feinberg School of Medicine.
10. **Nicholas Gavin, M.D., M.B.A., M.S.** — Chief Clinical Innovation Officer, MSHS.

The article lists Bilal Naved as the contact author at `bilalnaved@gmail.com` and `bilal.naved@northwestern.edu`.

## Abstract distilled

MSHS wanted to reduce confusion among patients with new symptoms, delayed care, unnecessary clinic or emergency-department use, and inefficient use of staff and facilities. Following a market review and request for proposals beginning in 2021, it selected Clearstep, whose product combines:

- a probabilistic natural-language-processing layer for mapping free-text symptoms to a structured chief complaint; and
- a deterministic, rules-based clinical expert system based on an enhanced version of the Schmitt–Thompson telephone-triage protocols.

The branded service, **Check Symptoms & Get Care (CSGC)**, was placed on the public Mount Sinai website and inside the Epic-powered MyMountSinai mobile application. The page describes a late-2022 launch at scale and an early-2023 deployment/integration period.

Headline results reported by the authors include more than 60,000 visits, about 22,000 completed digital-triage sessions, a stated 37% initiation rate, roughly 80% completion among initiators, a System Usability Scale (SUS) score of 85.5, substantial use outside business hours, no reported CSGC-related safety incidents, and clinician-triage concordance ranging from 88% to 96% depending on evaluation method and acuity level.

## Key takeaways

1. **Patient experience:** A digital symptom checker can provide 24/7 guidance without requiring a phone call and can route users directly to an appropriate care option.
2. **Clinical evidence and safety:** The authors argue that triage should rest on trusted clinical content. CSGC uses Schmitt–Thompson-derived rules, clinician review, and post-launch safety monitoring.
3. **Workflow integration:** Adoption depends on integration with the patient portal, mobile application, scheduling, telehealth, and clinician workflows. A standalone symptom checker would not deliver the same next-step experience.
4. **Cross-functional ownership:** Clinical, digital, IT, patient-experience, operational, cybersecurity, marketing, executive, and vendor participants all contributed. Executive sponsorship supplied budget and authority.
5. **Continuous improvement:** Organizations should define success measures, monitor user behavior and clinical safety, refine algorithms and interfaces, and tie the tool to access, retention, operational efficiency, and resource-use goals.

## The Challenge

- MSHS focus groups in 2021 found that people with new symptoms often did not know which care option to choose.
- Some patients delayed necessary care; others made unnecessary clinic or emergency-room visits.
- At system scale, this uncertainty contributed to inappropriate facility and provider use, higher delivery costs, emergency-department crowding, and pressure from workforce shortages.

## The Goal

MSHS sought a scalable, evidence-based, patient-centered self-triage system able to manage thousands of interactions across many clinical scenarios. Requirements included:

- recommendations grounded in clinically trusted, independently auditable algorithms;
- an experience that was fast, simple, and engaging for distressed lay users;
- an always-available digital front door;
- a guided symptom questionnaire followed by personalized next-step recommendations;
- availability to both public-web users and authenticated app users; and
- a shorter path to appropriate care, with improved outcomes and satisfaction as the intended result.

The article places CSGC in a longer history: nurse telephone triage emerged in the 1980s and 1990s; Schmitt–Thompson protocols became a common U.S. call-center standard; web symptom checkers appeared in the late 1990s and 2000s; and newer products such as Ada, Buoy, Babylon, and EHR-vendor tools combine questionnaires, rule-based content, and machine learning. The authors say that end-to-end U.S. implementations integrating EHRs, actionable scheduling, and large-scale outcomes remain sparsely documented.

## The Execution

### Vendor selection

- In 2021, a cross-functional team surveyed available symptom-checker platforms.
- The built-in EHR self-triage module lacked a complete protocol library. Scaling it would have required MSHS clinicians to create, validate, and continuously maintain chief-complaint pathways, escalation criteria, and age- and sex-specific logic.
- That EHR module also did not serve unauthenticated visitors arriving through Mount Sinai's public website.
- MSHS therefore preferred an externally validated and continuously maintained protocol library.
- Vendors were scored on clinical content, integration, user experience, and scalability through a market evaluation and request-for-proposals process.
- Clearstep was selected. The article says its underlying telephone-triage protocols are used by roughly 95% of U.S. nurse call centers, while also disclosing that several coauthors have financial ties to Clearstep.

### Technical architecture

- Free-text symptom descriptions are mapped to structured chief complaints by a probabilistic NLP layer.
- The NLP component is described as a supervised neural-network text classifier trained on labeled patient-reported symptom data.
- At inference time, a large language model helps process paraphrases and ambiguous input.
- Calibrated confidence scores trigger a user-facing confirmation step: the user can confirm the proposed complaint, reject it, or choose an alternative before triage proceeds.
- The actual triage disposition is **not generated probabilistically**. It is calculated deterministically by an expert-authored rules engine based on enhanced Schmitt protocols.

### Implementation and user flow

- Mount Sinai's Digital and Technology Partners worked with Clearstep to configure and white-label the tool as CSGC.
- Two main channels were used:
  - multiple entry points on the public Mount Sinai website, including the patient-tools page; and
  - an Epic/MyChart launch point inside the MyMountSinai app.
- This reached unauthenticated prospective patients as well as existing patients with Mount Sinai accounts.
- The chatbot asks about symptoms and runs a questionnaire expected to take 2–4 minutes.
- Users can choose the guided symptom route or bypass it through a direct-to-care option.
- The interface presents a three-step progression: check symptoms, receive care recommendations, then choose and book care.
- It asks whether the user is answering for themself or someone else, collects a symptom description, and warns against entering personally identifiable information.
- Mount Sinai configured local endpoints so recommendations led to its facilities and clinicians. Epic integration exposed schedulable appointment slots.
- A typical outcome might state that emergency care is unnecessary while recommending near-term care. The next actions could include immediate virtual urgent care, a primary-care appointment, or a nearby urgent-care location.
- By late 2022, the authors say Mount Sinai was the first New York City health system to launch AI-driven digital triage at scale. They also describe it as the largest urban AI-triage deployment reported in the literature at publication time.

## Hurdles

### Technical integration

- Early app testing sometimes launched the symptom checker in an external browser and made it difficult to return to the app.
- MSHS and Epic support enabled in-app web views and single sign-on.
- This required custom development and repeated testing.

### Stakeholder alignment and funding

- Clinicians needed confidence in patient safety, and leadership needed a case for buying a third-party product.
- The team emphasized digital access, the evidence base behind the rules, and the fact that similar protocols support roughly 95% of U.S. nurse call centers.
- MSHS argued that purchasing the maintained platform would cost less than building and maintaining its own clinical rules.
- Before launch, clinicians reviewed sample chief-complaint pathways, escalation thresholds, and mappings from dispositions to local care venues.

### Operations and adoption

- A virtual-urgent-care recommendation was useful only if providers and handoff workflows were available.
- The virtual-care service therefore had to coordinate capacity and timely follow-up with CSGC demand.
- MSHS promoted the tool through website prompts, the app, and newsletters.

## The Team

- The Chief Clinical Innovation Officer led clinical alignment.
- The Chief Digital Transformation Officer served as champion and sponsor.
- Digital and Technology Partners and Digital Marketing configured the product, integrated it into the app, and handled data flow and security under senior digital, information, and marketing leadership.
- Operational participants included a product owner, project manager, web-production director, EHR analyst, product directors, digital-marketing leaders, IT leaders, clinicians, cybersecurity staff, and service operators.
- The vendor contributed product management, product leadership, design, clinical, and engineering roles.
- Weekly implementation meetings kept the joint team aligned.
- Mount Sinai clinicians and user-experience specialists revised question wording and interface design. Clearstep white-labeled the product.
- The patient-experience group ran focus groups and pilots, and independent user testers measured usability.
- Executive leaders secured the budget and treated CSGC as a flagship access initiative.

## Metrics

### Measurement window and scope

- The case study reports first-year results from approximately mid-2023 to mid-2024 after the 2023 launch.
- 2025 data were still being analyzed and validated for a later study.
- Reported page-level totals: more than 60,000 visits and about 22,000 completed triage sessions.
- The article labels 37% as the initiation rate and says about 80% of initiators completed a conversation.

### Top chief complaints in completed conversations (Figure 3)

| Rank | Chief complaint | Completed conversations |
|---:|---|---:|
| 1 | Abdominal pain | 2,009 |
| 2 | Weakness, fatigue, or both | 952 |
| 3 | Cough | 832 |
| 4 | Sore or scratchy throat | 762 |
| 5 | Leg or foot swelling | 727 |
| 6 | Headache | 706 |
| 7 | Back pain | 664 |
| 8 | Chest or rib pain | 501 |
| 9 | Flank/side pain | 446 |
| 10 | Rash or redness | 407 |
| 11 | Diarrhea | 393 |
| 12 | Concern about Covid-19 | 387 |
| 13 | Dizziness | 384 |
| 14 | Fever | 379 |
| 15 | Congestion | 377 |
| 16 | Leg pain | 366 |
| 17 | Numbness or tingling | 356 |
| 18 | Lymph-node problem | 319 |
| 19 | Foot or ankle injury/pain | 310 |
| 20 | Itching | 304 |
| 21 | Trouble breathing | 288 |

The authors say this complaint mix resembles conventional nurse-call-center demand.

### Recommended care venues (Figure 4)

| Recommended destination | Share of completed conversations |
|---|---:|
| Primary care | 36.06% |
| Telemedicine | 26.79% |
| Emergency room | 18.18% |
| Urgent care | 6.91% |
| Ambulance | 4.04% |
| Specialist | 3.72% |
| Home care | 1.62% |
| Behavioral health | 0.73% |
| Information/education | 0.71% |
| Asynchronous care | 0.67% |
| Testing | 0.33% |
| Dentist | 0.16% |
| Poison control | 0.06% |
| Labor and delivery | 0.01% |

The displayed values sum to approximately 100% after rounding.

### Call-to-action engagement (Figure 5)

| Recommendation | CTA engagement rate |
|---|---:|
| Behavioral health | 58.3% |
| Asynchronous care/e-visits | 57.6% |
| Specialist | 52.4% |
| Telemedicine | 48.2% |
| Information | 42.1% |
| Primary care | 39.8% |
| Dentist | 35.2% |
| Urgent care | 31.1% |
| Testing | 25.4% |
| Ambulance | 15.2% |
| Emergency room | 10.5% |
| Home care | 5.1% |
| Figure's displayed grand total | 38.5% |

The prose separately says CTA engagement averaged about 33% across bookable care types. This appears to use a different denominator or subset from the figure's 38.5% grand total; the page does not reconcile them.

### Use by day and after hours (Figure 6)

| Day | Sessions shown |
|---|---:|
| Sunday | 7,765 |
| Monday | 11,298 |
| Tuesday | 11,361 |
| Wednesday | 10,480 |
| Thursday | 14,005 |
| Friday | 10,887 |
| Saturday | 8,896 |

- The authors report that 71% of interactions occurred outside ordinary business hours.
- The text and figure caption state that 26% occurred on weekends and argue that the tool absorbs demand that might otherwise require a continuously staffed nurse line.
- The displayed day counts total 74,692; Saturday plus Sunday is 16,661, or approximately 22.3% of that displayed total. The page does not explain why this differs from the stated 26%.

### Demographics and language (Figure 7)

- Mean age: 36.4 years.
- Range: newborn to 100 years.
- The plotted age distribution peaks in the mid-30s and declines with age, with a smaller infant cluster.
- Biological sex at birth, asked only when needed for triage:
  - female: 31.23%;
  - male: 12.74%;
  - other/intersex: 0.29%;
  - unknown: 55.74%.
- The authors say female was reported 2.58 times as often as male and attribute the high “unknown” share partly to sex being requested only when clinically relevant.
- Language:
  - English–American: 99.78%;
  - Spanish–Mexican: 0.22%.

### Patient-reported experience (Figure 8)

Experience rating counts on a 1–10 scale:

| Score | Count |
|---:|---:|
| 1 | 24 |
| 2 | 28 |
| 3 | 42 |
| 4 | 34 |
| 5 | 89 |
| 6 | 33 |
| 7 | 74 |
| 8 | 127 |
| 9 | 128 |
| 10 | 292 |

The chart totals 871 ratings. Scores of 9–10 account for 420 ratings (48.2%), consistent with the prose's “approximately 50%” statement. Scores of 8–10 account for 547 ratings (62.8%), which does **not** match the prose claim that more than 75% rated the tool at least 8. The page offers no explanation for the mismatch.

Customer Effort Score counts on a 1–7 scale:

| Score | Count |
|---:|---:|
| 1 | 51 |
| 2 | 34 |
| 3 | 50 |
| 4 | 143 |
| 5 | 173 |
| 6 | 201 |
| 7 | 253 |

The chart totals 905 responses; 627 (69.3%) are scores of 5–7. The article describes the distribution as positively skewed toward easier experiences.

The displayed patient comments emphasize reassurance, fast responses, helpful and appropriate questions, ease of use, clarity, and willingness to contact a nurse or clinician after receiving guidance. These comments are illustrative testimonials, not a representative qualitative analysis.

### System usability (Figure 2)

- Mean SUS score: 85.5 among independent testers.
- The article classifies this as “excellent” and within the acceptable range under published SUS interpretation thresholds.

## Preliminary clinical process measures

### Stated plans before triage

CSGC randomly asked some users what they planned to do before showing a recommendation.

- Unsure: 26% — the largest response.
- Primary-care intent: 23%.
- Specialty-care intent: 18%.
- Self-care intent: 11%.
- Figure 9 identifies **491 users** with a “clear” preintent, meaning they were neither unsure nor selected no plan.

### Preintent compared with the CSGC recommendation (Figure 9)

- 38% of those 491 clear preintents matched the recommendation.
- 62% were redirected.
- Among redirected users:
  - 79% were escalated to a more urgent option than they had intended;
  - 21% were de-escalated to a less acute option.
- CTA engagement:
  - validated/matching intent: 48%;
  - escalated users: 38%;
  - de-escalated users: 39%.

The article interprets this as evidence that the tool can redirect both under-triaged and over-triaged users. However, this is a comparison with the tool's recommendation, not an independently measured clinical outcome for every patient.

### Booking measurement and downstream outcomes

- Mount Sinai could measure CTA clicks but had not yet implemented a link-source parameter needed to prove that a clicked recommendation produced a booked visit.
- Appointments associated with the experience ranged from same-day care to bookings 90 days later.
- The article cites another U.S. integrated delivery network using the same AI-triage product and EHR scheduling system. That external implementation had a 51% aggregate confirmed-booking rate within seven days after a scheduling CTA.
- Diagnostic tests, final diagnoses, treatment, symptom relief, morbidity, and mortality are reserved for another study.
- Cost-effectiveness was out of scope because the analytic dataset lacked claims and downstream encounter linkage, and the authors did not have a counterfactual model of utilization without CSGC.

### Table 1: external delivery-network booking conversion

These are **not Mount Sinai conversion results**; they come from another U.S. integrated delivery network using the same technology.

| Workflow | Conversion definition | Confirmed completion within 7 days |
|---|---|---:|
| Primary care, established patient | Scheduling CTA click to confirmed EHR appointment | 35% |
| Primary care, new patient | Same, through new-patient pathway | 50% |
| Specialty, new patient | Specialty new-patient scheduling pathway | 75% |
| On-demand virtual visit | Click to initiated/confirmed virtual visit | 63% |
| Specialty, established patient | Established-patient specialty pathway, such as musculoskeletal or chronic respiratory care | 100% |
| Aggregate | Weighted across all pathways over a prospective seven-day window | 51% |

### Safety and clinician concordance

- Mount Sinai had received zero CSGC-related patient-safety incident reports through users, clinicians, staff, or the health-system incident channel at the time of publication.
- Monitoring included random sampling, blinded physician review, review of misclassification errors, low-confidence NLP cases, and a user-affirmation step for chief-complaint mapping.
- “Zero reported incidents” should not be read as proof that no unobserved harm occurred.

### Table 2: human-clinician comparisons

| Evaluation | Design and setting | Result |
|---|---|---|
| Same-patient blinded comparison | 76 patients with 40 unique chief complaints in a U.S. community emergency department. Patients used the AI checker on an iPad; treating clinicians independently assessed them while blinded to AI output. | 88% exact triage concordance; 7% overtriage; 5% undertriage. No case was undertriaged to zero care. Four undertriaged cases were reviewed in detail. |
| Continuous post-deployment review | Monthly random production samples stratified by triage endpoint. Two or three emergency-medicine physicians reviewed 911/ER cases; a licensed urgent-care physician reviewed urgent-care cases; an internal-medicine physician reviewed nonurgent cases. A second reviewer adjudicated disagreements. Dozens to hundreds of cases were reviewed monthly. | Twelve-month mean concordance: 93% for 911/ER, 95% for urgent care, and 96% for nonurgent recommendations. |
| Misclassification and safety monitoring | Confidence-scored chief-complaint mapping, user confirmation, review of low-confidence cases, and the health system's formal incident channel. | Zero CSGC-related patient-safety incidents reported to the system as of publication. |

The study did not compare CSGC head to head with a 24/7 nurse line, unrestricted same-day primary care, or another care-navigation method. The authors identify such a comparator as an important future study.

## Further limitations

1. **Single-system context:** Results may differ in organizations with different demographics, clinical complexity, case mix, and digital access.
2. **Selection and input quality:** Age, language needs, socioeconomic conditions, Internet access, portal adoption, and comfort with mobile tools can affect who uses the system and how accurately symptoms are described.
3. **Complex populations:** Performance may differ for multimorbid or immunocompromised patients.
4. **Jurisdiction:** Privacy, consent, medical-device/software regulation, and clinical-decision-support rules vary and may constrain workflows, integration, and monitoring.
5. **Limited generalizability:** Smaller health systems, rural networks, and international settings may require language localization, local-care-pathway configuration, accessibility work, and regulatory review.
6. **No direct comparator:** Safety and routing were not tested against an alternative navigation service in this case study.
7. **Incomplete downstream linkage:** The study could not prove Mount Sinai booking conversion or report clinical outcomes and cost-effectiveness.
8. **Author/vendor conflicts:** Three authors report personal financial interests in Clearstep, and one has a dual academic/vendor appointment.

### Tiered implementation ladder

- **Foundational:** Website triage routes patients to existing access channels and static resources.
- **Intermediate:** Deep links to online scheduling, telehealth, and callback workflows.
- **Advanced:** An integrated digital front door with EHR authentication, in-app web views, single sign-on, and scheduling APIs.

The authors recommend starting at the level current infrastructure supports and adding integration over time.

## Where to Start: the seven-step road map

1. **Research the problem and define success.** Identify the access problem, involve patients, align stakeholders, and predefine measures such as completion, redirection, SUS, CTA use, after-hours use, and satisfaction.
2. **Secure leadership and form a cross-functional group.** Obtain clinical and digital executive sponsors, include operations, IT/EHR, patient experience, call-center or telehealth staff, and use a physician champion to bridge technical and clinical work.
3. **Evaluate vendors rigorously.** Use an RFP or pilot; assess validation, protocol content, configurability, EHR integration, safety record, and collaboration. The authors recommend comparing general foundation models with purpose-built clinical systems and cite a separate evaluation finding under- and over-triage by ChatGPT Health relative to adjudicated standards.
4. **Design integration and workflows early.** Decide on single sign-on, portal/app embedding, scheduling and telehealth handoffs, whether results return to the EHR, and privacy, security, and compliance governance.
5. **Pilot and iterate.** Start with a subset or service line, monitor patients and clinicians, fix integration bugs, and use short 1–2 week sprints with a backlog, daily stand-ups, demonstrations, and retrospectives rather than a single large release.
6. **Define KPIs and monitor them.** Track use, completion, recommended-action follow-through, satisfaction, safety, booking conversion, and changes in service volumes. Real-time dashboards can identify abandonment or problematic pathways.
7. **Align with organizational strategy.** Connect the tool to digital transformation, access, patient retention, resource optimization, quality, and financial sustainability so support and funding persist.

## Figure-by-figure inventory

1. **Figure 1:** Public-website and MyChart/MyMountSinai entry points plus the branded symptom-checker interface. It shows a 2–4 minute guided survey and a separate direct-care choice.
2. **Figure 2:** SUS score of 85.5, categorized as excellent/acceptable.
3. **Figure 3:** Counts for 21 leading chief complaints; abdominal pain is highest at 2,009.
4. **Figure 4:** Full percentage distribution of 14 recommended care destinations; primary care, telemedicine, and ER dominate.
5. **Figure 5:** CTA engagement by recommendation, ranging from 58.3% for behavioral health to 5.1% for home care; displayed total 38.5%.
6. **Figure 6:** Sessions by weekday, with Thursday highest at 14,005; caption reports 26% weekend use and prose reports 71% outside business hours.
7. **Figure 7:** Age, biological sex at birth, and language distribution.
8. **Figure 8:** Post-session rating counts, Customer Effort Score counts, and illustrative positive patient feedback.
9. **Figure 9:** The 491-user preintent cohort, 38% concordance, 62% redirection, escalation/de-escalation split, and CTA engagement by group.

## Disclosures, funding, and supplementary material

- Partial funding: U.S. National Institutes of Health, National Center for Advancing Translational Sciences, grant UM1TR005121, associated with Bilal Naved and Yuan Luo.
- Bilal Naved, Quintan Slott, and Michael Amygdalidis report personal financial interests in Clearstep.
- Bilal Naved holds appointments at Icahn School of Medicine and Clearstep; the article says this conflict is managed through a business-management plan.
- Minh Tran, Paul Francaviglia, Phyllis Crandall, Girish Nadkarni, Robert Freeman, Yuan Luo, and Nicholas Gavin report no competing interests or financial ties to Clearstep.
- Supplementary appendix: `cat.25.0394-appendix.pdf`, 264.67 KB.
- Disclosure forms: `cat.25.0394-disclosures.pdf`, 1.10 MB.
- The linked supplementary PDFs are identified here but their off-page contents were not included in this webpage digest.

## Article visibility metrics shown on the page

These are dynamic and reflect what the page displayed when accessed, not fixed study results.

- Citation tab: 1 citing item.
- Altmetric score: 24.
- Coverage shown: 2 news outlets, 8 X users, and 1 Bluesky user.

## Critical reading: what the case study does and does not establish

### Supported by the reported data

- MSHS deployed an integrated digital triage pathway across public and authenticated channels.
- Users completed thousands of conversations and often used the service after hours.
- Independent testers rated usability highly.
- The system used deterministic clinical rules for disposition, with machine learning/LLM components confined to symptom-language interpretation and a user confirmation step.
- Sampled clinician reviews found high triage concordance.

### Not established by this paper

- A causal reduction in emergency visits, delays, morbidity, mortality, or cost.
- Mount Sinai's confirmed appointment-booking conversion after CTA clicks.
- Superiority to nurse lines, open same-day primary care, competing digital triage products, or no intervention.
- Complete detection of patient harm; the evidence is zero **reported** incidents plus sampled reviews.
- Broad generalizability outside this health system and its patient population.

### Internal numerical issues worth checking

1. About 22,000 divided by more than 60,000 is approximately the stated 37%, yet the article calls 37% the initiation rate while separately reporting 80% completion among initiators. Those labels do not cleanly reconcile with “22,000 completed sessions.”
2. Figure 5 shows a 38.5% grand-total CTA engagement rate; prose states about 33% across bookable care types. A denominator difference is plausible but unstated.
3. Figure 6's displayed daily counts imply approximately 22.3% weekend use, while the prose and caption say 26%.
4. Figure 8's visible rating counts imply 62.8% gave 8–10, while the prose says more than 75%. The 9–10 share is 48.2%, which does support the separate “approximately 50%” claim.

These discrepancies do not invalidate the implementation account, but they weaken confidence in unqualified use of the headline percentages.

## References listed by the article

1. Naved BA, Luo Y. Contrasting rule and machine learning based digital self triage systems in the USA. *NPJ Digital Medicine*. 2024;7:381.
2. Judson TJ, Odisho AY, Neinstein AB, et al. Rapid design and implementation of an integrated patient self-triage and self-scheduling tool for COVID-19. *Journal of the American Medical Informatics Association*. 2020;27:860–866.
3. Naved BA, Ravishankar S, Colbert GE, Johnston A, Slott QM, Luo Y. LLM enabled classification of patient self-reported symptoms and needs in health systems across the USA. *NPJ Digital Medicine*. 2025;8:390.
4. Spratt SE, Ravneberg D, Derstine B, Granger BB. Feasibility of electronic health record integration of a SMART application to facilitate patient-provider communication for medication management. *Computers, Informatics, Nursing*. 2022;40:538–546.
5. Bloomfield RA Jr, Polo-Wood F, Mandel JC, Mandl KD. Opening the Duke electronic health record to apps: implementing SMART on FHIR. *International Journal of Medical Informatics*. 2017;99:1–10.
6. Mandel JC, Kreda DA, Mandl KD, Kohane IS, Ramoni RB. SMART on FHIR: a standards-based, interoperable apps platform for electronic health records. *Journal of the American Medical Informatics Association*. 2016;23:899–908.
7. Mount Sinai. Mount Sinai patients receive greater and faster access to care with new expanded digital tools. June 21, 2023.
8. Schwartz N. Mount Sinai to install digital AI assistant. *Becker's Hospital Review*. August 10, 2023.
9. Schmitt BD. Telephone triage. *Annals of Emergency Medicine*. 2000;35:99–100.
10. Poole SR, Schmitt BD, Carruth T, Peterson-Smith A, Slusarski M. After-hours telephone coverage: the application of an area-wide telephone triage and advice system for pediatric practices. *Pediatrics*. 1993;92:670–679.
11. Schmitt BD. Telephone triage liability: protecting your patients and your practice from harm. *Advances in Pediatrics*. 2008;55:29–42.
12. Poole S, Ambardekar E, Gablehouse B, et al. Office “phone first” systems reduce emergency department/urgent care utilization by Medicaid-enrolled children. *Academic Pediatrics*. 2022;22:606–613.
13. Doctor K, Correa K, Olympia RP. Evaluation of an after-hours call center: are pediatric patients appropriately referred to the emergency department? *Pediatric Emergency Care*. 2014;30:798–804.
14. Choudhary A, Adhikari S, White PC. Implementation of after-hours nurse line in an academic pediatric endocrinology practice. *Pediatric Diabetes*. 2023;2023:2550101.
15. Maramba I, Chatterjee A, Newman C. Methods of usability testing in the development of eHealth applications: a scoping review. *International Journal of Medical Informatics*. 2019;126:95–104.
16. Wu DTY, Vennemeyer S, Brown K, et al. Usability testing of an interactive dashboard for surgical quality improvement in a large congenital heart center. *Applied Clinical Informatics*. 2019;10:859–869.
17. Simola S, Horhammer I, Xu Y, et al. Patients' experiences of a national patient portal and its usability: cross-sectional survey study. *Journal of Medical Internet Research*. 2023;25:e45974.
18. Sullivan PS, Driggers R, Stekler JD, et al. Usability and acceptability of a mobile comprehensive HIV prevention app for men who have sex with men: a pilot study. *JMIR mHealth and uHealth*. 2017;5:e26.
19. Kim MS, Aro MR, Lage KJ, Ingalls KL, Sindhwani V, Markey MK. Exploring the usability of mobile apps supporting radiologists' training in diagnostic decision making. *Journal of the American College of Radiology*. 2016;13:335–343.
20. Alduhailan HW, Alshamari MA, Wahsheh HAM. A comprehensive comparison and evaluation of AI-powered healthcare mobile applications' usability. *Healthcare (Basel)*. 2025;13:1829.
21. Poudyal A, Lewis DM, Taha S, et al. Designing an app to support measurement-based peer supervision of frontline health workers delivering brief psychosocial interventions in Texas: multimethod study. *JMIR Formative Research*. 2024;8:e55205.
22. Wetta-Hall R, Berg-Copas GM, Dismuke SE. Help on the line: telephone-triage use, outcomes, and satisfaction within an uninsured population. *Evaluation & the Health Professions*. 2005;28:414–427.
23. Lee TJ, Guzy J, Johnson D, Woo H, Baraff LJ. Caller satisfaction with after-hours telephone advice: nurse advice service versus on-call pediatricians. *Pediatrics*. 2002;110:865–872.
24. Ramaswamy A, Tyagi A, Hugo H, et al. ChatGPT Health performance in a structured test of triage recommendations. *Nature Medicine*. 2026;32:1671–1675.
