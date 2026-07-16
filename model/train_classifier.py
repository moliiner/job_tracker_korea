from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pandas as pd
import joblib

df = pd.read_csv("data/processed/processed_offers.csv")
X = df["description"]
Y = df["mentions_visa"]

vectorizer = TfidfVectorizer(max_features=300, stop_words="english")
X_vectorized = vectorizer.fit_transform(X)

X_train, X_test, Y_train, Y_test = train_test_split(X_vectorized, Y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, Y_train)

print(f"Accuracy: {model.score(X_test, Y_test):.2f}")

joblib.dump(model, "model/visa_classifier.pkl")
joblib.dump(vectorizer, "model/vectorizer.pkl")