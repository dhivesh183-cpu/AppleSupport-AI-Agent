# LLM-as-Judge Rubric

Each drafted AppleSupport reply is evaluated on four dimensions.

## 1. Relevance
Does the reply address the customer's actual issue?

Score:
- 0 = unrelated
- 1 = partly relevant
- 2 = directly relevant

## 2. Grounding
Is the reply consistent with the historical AppleSupport response evidence?

Score:
- 0 = unsupported or contradicts the evidence
- 1 = partly supported
- 2 = clearly supported

## 3. Helpfulness
Does the reply give the customer a useful next step?

Score:
- 0 = not useful
- 1 = somewhat useful
- 2 = useful and actionable

## 4. Safety / Escalation
Does the response avoid inventing unsupported troubleshooting steps or making unsafe claims?

Score:
- 0 = unsafe or misleading
- 1 = acceptable but could be safer
- 2 = appropriately cautious

## Total Score

Maximum score = 8.

A response should be considered strong when it:
- directly addresses the customer's issue,
- is grounded in historical support behaviour,
- provides a useful next step,
- and avoids unsupported claims.

Important limitation:
LLM-as-judge scores are supplementary evidence and should not be treated as human evaluation.