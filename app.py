import streamlit as st
import pandas as pd
from datetime import date
import os
import requests
from deep_translator import GoogleTranslator

FILE = "vocab.csv"

# ---------------- CREATE CSV IF NOT EXISTS ----------------
if not os.path.exists(FILE):
    pd.DataFrame(columns=[
        "date", "word", "type", "meaning", "article",
        "plural", "conjugation", "example", "correct", "wrong"
    ]).to_csv(FILE, index=False)

df = pd.read_csv(FILE)

# ---------------- AUTO GENERATE FUNCTION ----------------
def auto_generate(word):
    word_clean = word.strip()
    w = word_clean.lower()

    # 1. First check your own saved vocabulary
    if os.path.exists(FILE):
        saved_df = pd.read_csv(FILE)

        if len(saved_df) > 0 and "word" in saved_df.columns:
            saved_df["word_lower"] = saved_df["word"].astype(str).str.lower().str.strip()
            match = saved_df[saved_df["word_lower"] == w]

            if len(match) > 0:
                old = match.iloc[-1]

                return {
                    "type": old.get("type", ""),
                    "meaning": old.get("meaning", ""),
                    "article": old.get("article", ""),
                    "plural": old.get("plural", ""),
                    "conjugation": old.get("conjugation", ""),
                    "example": old.get("example", "")
                }

    # 2. Get English meaning automatically
    try:
        meaning = GoogleTranslator(source="de", target="en").translate(word_clean)
    except:
        meaning = "Please add meaning"

    # 3. Guess word type
    if w.endswith("en") and not word_clean[0].isupper():
        word_type = "Verb"
    elif word_clean[0].isupper() or w.endswith(("ung", "heit", "keit", "schaft", "tion")):
        word_type = "Noun"
    elif w.endswith(("lich", "ig", "isch", "bar", "sam")):
        word_type = "Adjective"
    else:
        word_type = "Other"

    # 4. Article and plural rules
    article = ""
    plural = ""

    if word_type == "Noun":
        if w.endswith(("ung", "heit", "keit", "schaft", "tion")):
            article = "die"
            plural = word_clean + "en"
        else:
            article = "Please check article"
            plural = "Please check plural"

    # 5. Verb conjugation rule
    conjugation = ""

    if word_type == "Verb" and w.endswith("en"):
        stem = w[:-2]
        conjugation = f"ich {stem}e, du {stem}st, er/sie/es {stem}t, wir {w}"

    # 6. Example sentence
    if word_type == "Verb":
        example = f"Ich möchte {word_clean}. = I want to {meaning}."
    elif word_type == "Noun":
        example = f"{article} {word_clean} ist wichtig. = The {meaning} is important."
    elif word_type == "Adjective":
        example = f"Das ist {word_clean}. = That is {meaning}."
    else:
        example = f"{word_clean} = {meaning}"

    return {
        "type": word_type,
        "meaning": meaning,
        "article": article,
        "plural": plural,
        "conjugation": conjugation,
        "example": example
    }

# ---------------- APP UI ----------------
st.title("DeutschMind")
st.caption("Learn • Practice • Improve")

menu = st.sidebar.radio(
    "Menu",
    ["Add Word", "Vocabulary List", "Quiz", "Weekly Review"]
)

# ---------------- ADD WORD PAGE ----------------
if menu == "Add Word":
    st.header("Add a German Word")

    word = st.text_input("Enter German word")

    if st.button("Auto-generate details"):
        if word.strip() == "":
            st.warning("Please enter a word first.")
        else:
            st.session_state["data"] = auto_generate(word)
            st.session_state["current_word"] = word

    data = st.session_state.get("data", {})

    word_type = st.text_input("Word type", value=data.get("type", ""))
    meaning = st.text_input("English meaning", value=data.get("meaning", ""))
    article = st.text_input("Article", value=data.get("article", ""))
    plural = st.text_input("Plural", value=data.get("plural", ""))
    conjugation = st.text_area("Conjugation / forms", value=data.get("conjugation", ""))
    example = st.text_area("Example sentence", value=data.get("example", ""))

    if st.button("Save Word"):
        if word.strip() == "":
            st.warning("Please enter a word first.")
        else:
            new_row = {
                "date": date.today(),
                "word": word,
                "type": word_type,
                "meaning": meaning,
                "article": article,
                "plural": plural,
                "conjugation": conjugation,
                "example": example,
                "correct": 0,
                "wrong": 0
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(FILE, index=False)

            st.success("Word saved!")

# ---------------- VOCABULARY LIST PAGE ----------------
elif menu == "Vocabulary List":
    st.header("Vocabulary List")
    st.dataframe(df)

# ---------------- QUIZ PAGE ----------------
elif menu == "Quiz":
    st.header("Quiz")

    if len(df) == 0:
        st.warning("Add words first.")
    else:
        row = df.sample(1).iloc[0]

        quiz_type = st.radio(
            "Quiz type",
            ["Meaning", "Article", "Word Type"]
        )

        if quiz_type == "Meaning":
            st.subheader(row["word"])
            answer = st.text_input("English meaning?")

            if st.button("Check"):
                if answer.lower().strip() == str(row["meaning"]).lower().strip():
                    st.success("Correct!")
                    df.loc[row.name, "correct"] += 1
                else:
                    st.error(f"Wrong. Correct answer: {row['meaning']}")
                    df.loc[row.name, "wrong"] += 1

                df.to_csv(FILE, index=False)

        elif quiz_type == "Article":
            st.subheader(row["word"])
            answer = st.radio("Choose article", ["der", "die", "das", "no article"])

            correct_article = str(row["article"])
            if correct_article == "nan":
                correct_article = ""

            if st.button("Check"):
                if answer == correct_article or (answer == "no article" and correct_article == ""):
                    st.success("Correct!")
                    df.loc[row.name, "correct"] += 1
                else:
                    st.error(f"Wrong. Correct answer: {correct_article}")
                    df.loc[row.name, "wrong"] += 1

                df.to_csv(FILE, index=False)

        elif quiz_type == "Word Type":
            st.subheader(row["word"])
            answer = st.radio("Choose type", ["Noun", "Verb", "Adjective", "Adverb", "Other"])

            if st.button("Check"):
                if answer == row["type"]:
                    st.success("Correct!")
                    df.loc[row.name, "correct"] += 1
                else:
                    st.error(f"Wrong. Correct answer: {row['type']}")
                    df.loc[row.name, "wrong"] += 1

                df.to_csv(FILE, index=False)

# ---------------- WEEKLY REVIEW PAGE ----------------
elif menu == "Weekly Review":
    st.header("Weekly Review")

    if len(df) == 0:
        st.warning("No words yet.")
    else:
        df["date"] = pd.to_datetime(df["date"])
        week_df = df[df["date"] >= pd.Timestamp.today() - pd.Timedelta(days=7)]

        st.metric("Words learned this week", len(week_df))

        st.subheader("Words by type")
        st.bar_chart(week_df["type"].value_counts())

        total_correct = df["correct"].sum()
        total_wrong = df["wrong"].sum()
        total = total_correct + total_wrong

        if total > 0:
            accuracy = round((total_correct / total) * 100, 2)
            st.metric("Overall quiz accuracy", f"{accuracy}%")

        st.subheader("Weak words")
        weak_words = df[df["wrong"] > df["correct"]]
        st.dataframe(weak_words)

        st.subheader("This week's words")
        st.dataframe(week_df)