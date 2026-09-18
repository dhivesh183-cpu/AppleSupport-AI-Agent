# Decision Log — AppleSupport AI Agent

## 1. Brand selection
Selected AppleSupport because it has a large number of support interactions in the dataset, giving enough examples for both intent classification and historical-reply retrieval.

## 2. Conversation construction
Constructed customer-support pairs by linking each AppleSupport reply to the customer tweet referenced by `in_response_to_tweet_id`.

## 3. Sampling strategy
Used a subsample rather than the full dataset because the assignment expects a reproducible solution that can run quickly.

## 4. Text cleaning
Removed URLs, @mentions, HTML entities, and extra whitespace while keeping the customer's main wording.

## 5. Intent taxonomy
Created 10 operational intents from recurring themes in AppleSupport conversations rather than using a very large number of fine-grained categories.

## 6. Initial intent labelling
Used keyword rules to create an initial training taxonomy. These labels were treated as noisy operational labels rather than independent human ground truth.

## 7. Golden-set design
Created 200 evaluation examples with 20 examples per intent. This gives coverage across all intents but is not representative of real-world intent prevalence.

## 8. Human review
Manually reviewed all 200 golden examples and recorded the final `gold_intent` labels before evaluating the classifier.

## 9. Classifier choice
Used TF-IDF features with Logistic Regression because the method is lightweight, interpretable, fast to train, and suitable for a reproducible baseline agent.

## 10. Baseline comparison
Compared the classifier with a majority-class baseline and a keyword-rule baseline to measure how much improvement came from statistical learning.

## 11. Retrieval leakage fix
Detected that retrieval could return the same message used as the query, producing artificially perfect similarity. Exact self-matches were therefore excluded during evaluation.

## 12. Intent-filtered retrieval
Restricted historical-reply retrieval to examples belonging to the predicted intent. This substantially improved agreement between retrieved examples and human-labelled intent.

## 13. Conservative reply generation
Used historical evidence only when retrieval similarity reached a threshold. Otherwise the system returns a cautious request for more information instead of inventing troubleshooting advice.

## 14. Escalation policy
Automatically escalates account, billing, and order/repair cases, as well as low-confidence predictions. The goal is to reduce incorrect automatic handling rather than maximize automation.