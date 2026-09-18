# AppleSupport AI Customer Support Agent

## 1. Problem Framing

This project builds a small AI customer-support agent using the
Customer Support on Twitter dataset.

The selected brand is AppleSupport.

The system receives a customer message and performs three tasks:

1. Classifies the message into an operational support intent.
2. Retrieves similar historical AppleSupport conversations.
3. Decides whether to auto-handle the message or escalate it to a human.

The goal is not to replace human support. The design is intentionally
conservative: uncertain or sensitive cases should be sent to a human.

---

## 2. Dataset and Sampling

The Kaggle Customer Support on Twitter dataset was used.

The dataset contains approximately 2.8 million tweets.

Only AppleSupport conversations were used for this experiment.

Customer-support pairs were created by linking an AppleSupport reply
to the customer tweet referenced by `in_response_to_tweet_id`.

After cleaning and removing duplicate customer messages, the working
dataset contained 103,529 unique AppleSupport customer messages.

Ten operational intents were used:

- ios_or_software_update
- device_or_hardware
- battery_or_charging
- account_or_icloud
- purchase_or_billing
- connectivity_or_network
- app_or_media_service
- order_or_repair
- support_contact_or_dm
- general_or_other

A 200-example golden set was created with 20 examples per intent.
This provides balanced coverage of all intents but is not representative
of the real production distribution.

The golden set was manually reviewed by one human annotator.

---

## 3. Intent Classification

### Baselines

Two simple baselines were evaluated.

The majority-class baseline always predicts the most common intent:

- Accuracy: 33.89%
- Macro F1: 0.0506

A keyword-rule baseline achieved:

- Accuracy: 98.00%
- Macro F1: 0.9150

However, this result is misleading because the same type of keyword rules
were used to bootstrap the training labels. Therefore it is not an
independent quality measurement.

### Main classifier

The main model uses:

- TF-IDF features
- Unigrams and bigrams
- Logistic Regression

On the automatically labelled held-out test split:

- Accuracy: 93.13%
- Macro F1: 0.7896

The more important evaluation is the human-reviewed golden set.

On 200 manually reviewed examples:

- Accuracy: 83.00%
- Macro F1: 0.843

Per-intent results showed strongest performance for battery,
iOS/software, and device/hardware messages.

The main weakness was `general_or_other`, which had high recall but
low precision. This means that many messages belonging to more specific
intents were absorbed into the general category.

---

## 4. Historical Reply Retrieval

The agent uses TF-IDF nearest-neighbour retrieval to find previous
AppleSupport customer messages and their corresponding historical replies.

An initial evaluation produced artificially high similarity because the
query could retrieve itself. This was identified as self-match leakage.

The evaluation was then changed to remove exact self-matches.

A global lexical retriever produced a 33.5% match between the nearest
historical example's intent and the human-labelled intent.

An intent-filtered retriever was then tested. It first predicts an intent
and searches only historical examples from that predicted intent.

This increased historical-intent agreement to:

33.5% -> 83.0%

Improvement: 49.5 percentage points.

However, average lexical similarity decreased:

0.390 -> 0.308

This shows that intent filtering improves topical consistency but does
not necessarily find a textually closer example.

Only 25 of 200 golden examples (12.5%) had a retrieval similarity of
at least 0.45, which was used as the threshold for strong historical
evidence.

Therefore the system does not claim that every retrieved example is a
useful historical resolution.

---

## 5. Reply Generation

When a sufficiently strong historical match is found, the system cleans
the historical AppleSupport response and uses it as the basis for the
draft reply.

When the similarity is below 0.45, the system uses a conservative fallback:

"Thanks for reaching out. We'd like to understand your issue better
before suggesting a solution. Please share a few more details so we can help."

This avoids inventing troubleshooting instructions when the historical
evidence is weak.

A major limitation is that the current reply generator is retrieval-based
rather than a full generative model. It can therefore produce generic
responses or responses that are not perfectly tailored to the customer's
specific situation.

---

## 6. Auto-Handle vs Escalate

The escalation policy uses two rules.

The following intents are always escalated:

- account_or_icloud
- purchase_or_billing
- order_or_repair

Predictions with confidence below 0.70 are also escalated.

On the 200-example human-reviewed golden set:

- Auto-handled: 80
- Escalated: 120
- Incorrect auto-handles: 1
- Total classification errors: 34
- Errors caught by escalation: 33
- Error capture rate: 97.06%

This demonstrates that the conservative policy substantially reduced
incorrect automatic handling on this evaluation set.

The 97.06% error-capture figure should not be interpreted as a production
guarantee because it was measured on only 200 balanced examples.

---

## 7. Failure Analysis

### Failure 1: Indirect support/contact requests

Example:

"Not sure why it's necessary to go into DM. What do you need to know
that can't be publicly known?"

Human label:
`support_contact_or_dm`

Model prediction:
`general_or_other`

Hypothesis:

TF-IDF focuses on individual words and may not understand that the whole
message is about the support interaction itself.

---

### Failure 2: Support-related accessory issue

Example:

"Accessory may not be supported" popping up on my phone.

Human label:
`support_contact_or_dm`

Model prediction:
`general_or_other`

Hypothesis:

The message describes a technical issue without strongly matching the
support/contact vocabulary represented in the training data.

---

### Failure 3: Verification-code account problem

Example:

"It's sending a verification code to another device. But I don't have
anything else."

Human label:
`account_or_icloud`

Model prediction:
`general_or_other`

Hypothesis:

The account/security intent is expressed indirectly without explicit
Apple ID or iCloud terminology.

---

### Failure 4: Apple ID wording ambiguity

Example:

"Why am I getting: our Apple ID cannot be updated at this time..."

Human label:
`ios_or_software_update`

Model prediction:
`account_or_icloud`

Hypothesis:

The phrase "Apple ID" strongly associates with the account category,
even though the human label considers the underlying issue to be an
update-related problem.

This demonstrates that intent boundaries themselves can be ambiguous.

---

### Failure 5: Hardware, battery, and connectivity overlap

Examples involving an iPhone, battery, charging, or WiFi can contain
multiple issue signals.

The model sometimes assigns the message to `device_or_hardware`
because device-related words such as "iPhone" are strong TF-IDF features.

This was visible in testing:

"My iPhone battery is draining very quickly."

was predicted as:

`device_or_hardware`

with high confidence.

This demonstrates that model confidence does not guarantee correctness.

---

## 8. What Is Misleading About My Headline Number?

The headline number is 83% accuracy on the human-reviewed golden set.

That number is useful, but it can be misleading if presented without
context.

First, the golden set contains exactly 20 examples per intent, so it is
balanced rather than representative of the actual distribution of
AppleSupport conversations.

Second, the training labels for the large dataset were bootstrapped using
keyword rules. Therefore the model is partly learning a taxonomy created
by those rules rather than a fully independently annotated training set.

Third, only one human annotator was available, so human-human agreement
could not be measured.

Fourth, the keyword baseline achieved 98%, but that result is contaminated
by label-generation leakage and should not be treated as independent
evidence.

Finally, the retrieval system initially produced inflated similarity due
to self-match leakage. That issue was detected and corrected before the
reported retrieval results.

Therefore the 83% figure should be interpreted as performance on a small,
balanced, manually reviewed evaluation set rather than expected production
accuracy.

---

## 9. Evaluation Limitations

The project currently has several important limitations.

1. Only one human annotator was available.
2. The 200-example golden set is balanced rather than prevalence-based.
3. The training labels were bootstrapped rather than fully hand-labelled.
4. The retrieval method uses lexical similarity rather than a stronger
   semantic embedding model.
5. The reply generator mostly reuses historical responses.
6. No LLM-as-judge scores were fabricated because no LLM API key was
   available in the execution environment.
7. The escalation threshold was selected heuristically rather than tuned
   against a larger production-like validation set.

These limitations are included intentionally so the reported results are
reproducible and not overstated.

---

## 10. What I Would Do With One More Week

### 1. Improve the training labels

Create a larger independently annotated training set and refine the
boundaries between overlapping intents.

### 2. Improve retrieval

Use semantic embeddings and a reranker rather than relying only on
TF-IDF lexical similarity.

### 3. Improve reply generation

Use several retrieved historical examples as evidence and generate a
new response that is constrained by those examples.

### 4. Evaluate reply quality

Run an actual LLM-as-judge evaluation using the documented rubric, together
with a second human annotator.

### 5. Tune escalation

Measure the trade-off between automation rate and incorrect auto-handling
on a larger validation set.

### 6. Add conversation context

Many Twitter support interactions are multi-turn. Including previous
customer/support messages would help resolve ambiguous short messages.

---

## 11. Reproducibility

The notebook performs the following pipeline:

Dataset
-> AppleSupport filtering
-> Customer/support pair construction
-> Text cleaning
-> Intent labelling
-> TF-IDF + Logistic Regression
-> Human golden-set evaluation
-> Historical retrieval
-> Reply drafting
-> Auto-handle / escalation

The project uses Python and standard machine-learning libraries including
pandas and scikit-learn.

The experiment is designed to run on a dataset subsample rather than the
full dataset, making it practical to reproduce in a notebook environment.

## Human Agreement

A second annotator independently labelled 40 examples from the evaluation set.
The two human annotators agreed on 17 of 40 examples, giving a raw agreement of
42.5%. Cohen's kappa was 0.364.

This indicates that the intent taxonomy has some ambiguity, especially for
messages that could reasonably belong to more than one category. The agreement
sample is small, so this result should be treated as supporting evidence rather
than a definitive measure of annotation reliability.