import os
import re
import html
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.neighbors import NearestNeighbors

RANDOM_STATE = 42

INTENTS = [
    "ios_or_software_update",
    "device_or_hardware",
    "battery_or_charging",
    "account_or_icloud",
    "purchase_or_billing",
    "connectivity_or_network",
    "app_or_media_service",
    "order_or_repair",
    "support_contact_or_dm",
    "general_or_other",
]

def clean_text(text):
    text = html.unescape(str(text))
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def assign_intent(text):
    text = text.lower()

    if any(w in text for w in [
        "update", "ios", "software"
    ]):
        return "ios_or_software_update"

    if any(w in text for w in [
        "iphone", "ipad", "mac", "screen", "keyboard",
        "camera", "speaker", "button", "broken", "hardware"
    ]):
        return "device_or_hardware"

    if any(w in text for w in [
        "battery", "charging", "charge", "charger",
        "battery life", "power"
    ]):
        return "battery_or_charging"

    if any(w in text for w in [
        "icloud", "apple id", "password", "login",
        "account", "verification"
    ]):
        return "account_or_icloud"

    if any(w in text for w in [
        "refund", "payment", "charged", "billing",
        "purchase", "subscription", "money"
    ]):
        return "purchase_or_billing"

    if any(w in text for w in [
        "wifi", "wi-fi", "internet", "network",
        "bluetooth", "connection", "connect"
    ]):
        return "connectivity_or_network"

    if any(w in text for w in [
        "app", "itunes", "music", "apple music",
        "podcast", "store"
    ]):
        return "app_or_media_service"

    if any(w in text for w in [
        "repair", "replacement", "order", "delivery",
        "shipping", "service"
    ]):
        return "order_or_repair"

    if any(w in text for w in [
        "dm", "direct message", "call", "support",
        "contact", "customer service"
    ]):
        return "support_contact_or_dm"

    return "general_or_other"


def build_pairs(df):
    tweet_lookup = df.set_index("tweet_id")

    replies = df[
        (df["author_id"] == "AppleSupport") &
        (df["inbound"] == False)
    ].copy()

    replies["customer_id"] = (
        replies["in_response_to_tweet_id"].astype("Int64")
    )

    replies["customer_text"] = replies["customer_id"].map(
        tweet_lookup["text"]
    )

    replies["support_reply"] = replies["text"]

    pairs = replies[
        [
            "customer_id",
            "tweet_id",
            "customer_text",
            "support_reply",
            "created_at",
        ]
    ].copy()

    pairs = pairs.rename(
        columns={
            "tweet_id": "support_tweet_id",
            "created_at": "support_created_at",
        }
    )

    pairs = pairs[pairs["customer_text"].notna()].copy()
    pairs = pairs.drop_duplicates("customer_id")
    pairs["clean_text"] = pairs["customer_text"].apply(clean_text)
    pairs = pairs[pairs["clean_text"].str.len() >= 5]
    pairs = pairs.drop_duplicates("clean_text").reset_index(drop=True)

    pairs["intent"] = pairs["clean_text"].apply(assign_intent)

    return pairs


def train_model(pairs):
    X = pairs["clean_text"]
    y = pairs["intent"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=y
    )

    model = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                min_df=2,
                max_features=50000
            )
        ),
        (
            "classifier",
            LogisticRegression(
                max_iter=1000,
                random_state=RANDOM_STATE
            )
        )
    ])

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "macro_f1": f1_score(
            y_test,
            predictions,
            average="macro",
            zero_division=0
        )
    }

    return model, metrics


def predict_intent(model, customer_message):
    text = clean_text(customer_message)

    probabilities = model.predict_proba([text])[0]
    classes = model.classes_

    index = np.argmax(probabilities)

    return classes[index], float(probabilities[index])


def retrieve_reply(model, pairs, customer_message):
    intent, confidence = predict_intent(
        model,
        customer_message
    )

    intent_pairs = pairs[
        pairs["intent"] == intent
    ].copy()

    if len(intent_pairs) == 0:
        return intent, confidence, None, 0.0

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        max_features=30000
    )

    matrix = vectorizer.fit_transform(
        intent_pairs["clean_text"]
    )

    query_vector = vectorizer.transform(
        [clean_text(customer_message)]
    )

    retriever = NearestNeighbors(
        n_neighbors=min(10, len(intent_pairs)),
        metric="cosine"
    )

    retriever.fit(matrix)

    distances, indices = retriever.kneighbors(
        query_vector
    )

    query_clean = clean_text(customer_message).lower()

    for distance, index in zip(
        distances[0],
        indices[0]
    ):
        historical = intent_pairs.iloc[index]["clean_text"]

        if historical.strip().lower() == query_clean:
            continue

        similarity = round(1 - distance, 3)

        return (
            intent,
            confidence,
            intent_pairs.iloc[index]["support_reply"],
            similarity
        )

    return intent, confidence, None, 0.0


def decide_action(intent, confidence):
    escalate_intents = {
        "purchase_or_billing",
        "order_or_repair",
        "account_or_icloud"
    }

    if intent in escalate_intents:
        return (
            "ESCALATE",
            "This intent may require account, payment, order, "
            "or service-specific handling."
        )

    if confidence < 0.70:
        return (
            "ESCALATE",
            f"Model confidence is only {confidence:.2f}, "
            "so human review is safer."
        )

    return (
        "AUTO-HANDLE",
        f"Model confidence is {confidence:.2f} for {intent}."
    )


def generate_reply(model, pairs, customer_message):
    intent, confidence, historical_reply, similarity = (
        retrieve_reply(
            model,
            pairs,
            customer_message
        )
    )

    if historical_reply is None or similarity < 0.45:
        reply = (
            "Thanks for reaching out. We'd like to understand "
            "your issue better before suggesting a solution. "
            "Please share a few more details so we can help."
        )
        evidence_used = False
    else:
        reply = re.sub(
            r"@\w+",
            "",
            str(historical_reply)
        )
        reply = re.sub(
            r"https?://\S+",
            "",
            reply
        )
        reply = re.sub(
            r"\s+",
            " ",
            reply
        ).strip()
        evidence_used = True

    action, reason = decide_action(
        intent,
        confidence
    )

    return {
        "intent": intent,
        "confidence": round(confidence, 3),
        "action": action,
        "reason": reason,
        "reply": reply,
        "similarity": similarity,
        "historical_evidence_used": evidence_used
    }


if __name__ == "__main__":

    DATA_FILE = "twcs.csv"

    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            "Place twcs.csv in the project directory first."
        )

    df = pd.read_csv(
        DATA_FILE,
        usecols=[
            "tweet_id",
            "author_id",
            "inbound",
            "created_at",
            "text",
            "in_response_to_tweet_id"
        ]
    )

    pairs = build_pairs(df)

    model, metrics = train_model(pairs)

    print("AppleSupport AI Agent")
    print("---------------------")
    print("Usable customer messages:", len(pairs))
    print("Held-out accuracy:", round(metrics["accuracy"], 4))
    print("Held-out macro F1:", round(metrics["macro_f1"], 4))

    print("\nExample:")
    message = "I forgot my Apple ID password and cannot log in."

    result = generate_reply(
        model,
        pairs,
        message
    )

    for key, value in result.items():
        print(f"{key}: {value}")