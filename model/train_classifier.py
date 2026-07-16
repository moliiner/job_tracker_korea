from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import pandas as pd
import joblib

df = pd.read_csv("data/processed/processed_offers.csv")
X = df["description"]
Y = df["mentions_visa"]

# --- Check class balance before doing anything else ---
print("Class distribution:")
print(Y.value_counts())
print()

positive_count = Y.sum()
if positive_count < 10:
    print(f"WARNING: only {positive_count} positive example(s) found in the data.")
    print("With this few examples, the model cannot learn a real pattern —")
    print("it will likely just predict the majority class every time.")
    print("Collect more offers that explicitly mention visa sponsorship before trusting this model.")
    print()

vectorizer = TfidfVectorizer(max_features=300, stop_words="english")
X_vectorized = vectorizer.fit_transform(X)

# --- stratify keeps the same class proportion in train and test sets ---
# Only works if there are enough positive examples to appear in both splits;
# falls back to a plain split otherwise.
try:
    X_train, X_test, Y_train, Y_test = train_test_split(
        X_vectorized, Y, test_size=0.2, random_state=42, stratify=Y
    )
except ValueError:
    print("Not enough samples per class to stratify — using a plain random split instead.")
    X_train, X_test, Y_train, Y_test = train_test_split(
        X_vectorized, Y, test_size=0.2, random_state=42
    )

# --- class_weight="balanced" tells the model to penalize mistakes on the
# minority class more heavily, instead of ignoring it to chase accuracy ---
model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
model.fit(X_train, Y_train)

Y_pred = model.predict(X_test)

print(f"Accuracy: {model.score(X_test, Y_test):.2f}")
print("(Accuracy alone is misleading on imbalanced data — see the report below)")
print()

print("Classification report (precision / recall / F1 per class):")
print(classification_report(Y_test, Y_pred, zero_division=0))

print("Confusion matrix:")
print(confusion_matrix(Y_test, Y_pred))

joblib.dump(model, "model/visa_classifier.pkl")
joblib.dump(vectorizer, "model/vectorizer.pkl")