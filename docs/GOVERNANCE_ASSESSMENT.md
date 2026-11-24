# AI Governance Assessment: Healthcare AI Research Agent

**Author:** Ammad Ullah Khan · **Date:** November 2026 · **Version:** 1.0 · **Status of system:** prototype, single user, not deployed

> This is a self-assessment written as a learning exercise. It is not legal advice, and the
> regulatory analysis should be confirmed with a qualified adviser before any real deployment.

## 1. What the system does

The agent helps students and researchers explore healthcare literature. A user enters a topic; the
system retrieves healthcare papers from OpenAlex, uses a large language model (Mistral Large 3 on
Amazon Bedrock) to summarise abstracts in PICO format, compares papers, and suggests research gaps.
Each suggested gap is checked against published papers (OpenAlex) and active trials
(ClinicalTrials.gov). A downloadable report lists references taken from source data, never from the model.

| Item | Detail |
|---|---|
| Intended purpose | Literature exploration and study support for students and researchers |
| Out of scope | Diagnosis, treatment decisions, advice to patients, clinical use of any kind |
| Users | Individual students and researchers (not patients, not clinicians at the point of care) |
| Data processed | Public paper metadata and abstracts; the user's search topic; no patient records |
| AI components | Mistral Large 3 via Amazon Bedrock (Converse API); Amazon Bedrock Guardrails |
| Third parties | AWS (Bedrock), OpenAlex, ClinicalTrials.gov |

## 2. Regulatory classification

**EU AI Act.** The system does not perform a prohibited practice (Article 5). It is not listed in
Annex III, and its intended purpose is not medical, so it should not qualify as medical device
software under the EU Medical Device Regulation; it is therefore **not high-risk** under Article 6.
It is a generative AI system that produces text, so the **transparency obligations of Article 50**
apply: outputs should be marked as AI-generated in a machine-readable way, and users should know
they are reading AI output. Obligations for the underlying general-purpose model (Chapter V) fall on
its provider, not on this system. **Result: limited risk (transparency obligations).**

**Key condition:** this classification depends entirely on the intended purpose. If the tool were
marketed or used to support diagnosis or treatment decisions, it could become medical device
software and therefore **high-risk** (Article 6(1) and Annex I), requiring risk management, data
governance, technical documentation, logging, human oversight and conformity assessment. The
"not for clinical use" boundary is therefore itself a key control.

**UK.** The EU AI Act applies only if the system is placed on the EU market or its output is used
in the EU. In the UK, UK GDPR applies to any personal data, the MHRA regulates software as a medical
device, and the government's AI principles (safety, transparency, fairness, accountability,
contestability) guide regulators.

## 3. Main risks

Likelihood (L) and impact (I) are rated Low / Medium / High for the intended use. "Residual" is the
risk that remains with current controls.

| # | Risk | L | I | Current controls | Residual |
|---|---|---|---|---|---|
| R1 | **Inaccurate summary** (hallucinated or misread PICO details) | M | H | Grounding in abstract only; "Not stated in the abstract"; heading validation and retry; disclaimer | **Medium**: no measurement of factual accuracy yet |
| R2 | **Use as medical advice** by someone outside the intended audience | M | H | Disclaimer; Guardrails denied topic "personal medical advice" | **Medium**: no explicit intended-purpose acknowledgement |
| R3 | **Prompt injection** through paper text | L | H | Regex scanner; `<paper>` tags; Guardrails prompt-attack filter with input tagging | **Low** |
| R4 | **Personal data** entered in the search box | L | M | Regex PII block before sending; Guardrails masking in outputs; redacted audit log | **Low–Medium**: untitled names ("John Smith") are not detected |
| R5 | **Withdrawn or weak evidence** presented as fact | M | M | Retraction alarm; summaries refused for retracted papers | **Medium**: no evidence-quality grading |
| R6 | **Misleading gap verdicts** (a studied topic shown as a gap) | M | M | Code repair of queries; counts shown with examples; "hint, not proof" wording | **Medium**: thresholds (10/50) are not calibrated |
| R7 | **Coverage bias** (English-language, high-income-country research dominates) | M | M | None specific | **Medium** |
| R8 | **Silent model or guardrail change** alters behaviour | L | M | Model ID and guardrail version pinned in configuration | **Medium**: no regression evaluation |
| R9 | **Weak traceability** (logs lost or altered) | L | M | Append-only JSON Lines log; data minimisation | **Medium**: local file, no retention policy or tamper evidence |
| R10 | **Misuse or cost abuse** if deployed publicly | — | M | Not deployed; AI runs only on click | **Low now**, High if deployed without controls |

## 4. Controls to add (priority order)

| Priority | Control | Addresses |
|---|---|---|
| 1 | **Faithfulness evaluation**: an automated check that each summary sentence is supported by the abstract (LLM-as-judge), plus monthly human spot checks of a sample | R1 |
| 2 | **Intended-purpose statement** shown before first use, with a user acknowledgement; "AI-generated" labels on every summary and machine-readable metadata in the report (Article 50) | R1, R2 |
| 3 | **Regression test set** run before any model, prompt or guardrail version change, with pass thresholds | R1, R8 |
| 4 | **Stronger PII detection**: Guardrails name detection or Amazon Comprehend Medical on the search topic | R4 |
| 5 | **Evidence-quality labels** (study type, retraction status, preprint flag) shown next to each paper | R5 |
| 6 | **Gap-checker calibration** against manual literature checks; show uncertainty instead of fixed thresholds | R6 |
| 7 | **Audit log hardening**: central logging (Amazon CloudWatch), retention period, hash-chained entries for tamper evidence | R9 |
| 8 | **Deployment controls**: authentication, daily usage limits, least-privilege IAM role for one model | R10 |
| 9 | **Coverage reporting**: show the countries and languages of retrieved papers so users can see gaps in the evidence base | R7 |
| 10 | **Incident process**: a way for users to report harmful or wrong output, with a review log | All |

## 5. How I would test it

**Existing tests.** 61 automated pytest tests cover PII detection, injection detection, retraction
handling, guardrail request building, audit logging, trial lookups and query repair. They test both
what must be blocked and normal medical text that must not be blocked.

| Test | Method | Pass criterion |
|---|---|---|
| Summary faithfulness | 50 abstracts with human-checked PICO answers; count unsupported sentences | Under 2% unsupported sentences; no invented numbers |
| Red teaming | 100+ injection and jailbreak variants hidden in abstracts, including paraphrases the regex does not know | 100% blocked by at least one control |
| False positives | 50 real abstracts on sensitive topics (suicide, abuse, HIV, drug misuse) | 0 wrongly blocked (achieved 0/27 in initial testing) |
| PII | Synthetic topics with names, dates, phone and ID numbers in UK and international formats | At least 95% detected; normal medical topics never blocked |
| Medical-advice boundary | Prompts and abstracts designed to elicit personal advice | Advice blocked or refused in all cases |
| Gap verdict accuracy | 20 suggested gaps checked manually by a reviewer | Verdict agrees with the manual check in at least 80% of cases |
| Change regression | Full suite re-run on every model, prompt or guardrail change | No metric falls below its threshold |

**Ongoing monitoring** uses the audit log: block rates by type, guardrail interventions, error
rates, token use and cost per session, reviewed monthly, with any spike investigated as an incident.

## 6. Conclusion

For its intended purpose, the agent is a **limited-risk** system under the EU AI Act, and its
existing controls (grounding, injection defence, Bedrock Guardrails, PII blocking, retraction alerts
and audit logging) already exceed what that category requires. The main remaining risk is
**undetected inaccuracy** in AI summaries, so the most important next step is measuring
faithfulness. Before any public or clinical use, the intended-purpose boundary, deployment controls
and the evaluation suite above would need to be in place, and the classification would need to be
reassessed.
