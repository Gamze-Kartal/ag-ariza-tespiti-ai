"""
model_egit.py — Etiketli ağ ölçümlerinden arıza türü sınıflandırma modeli eğitir
ve modelleri karşılaştırır.

Kullanım:
    python src/model_egit.py data/ornek_veri.csv      (simüle veri)
    python src/model_egit.py data/lab_veri.csv        (kendi topladığın veri)

Çıktılar (sonuclar/ klasörü):
    model_karsilastirma.csv, confusion_matrix.png, feature_importance.png,
    karar_agaci.png, en_iyi_model.joblib
Gerekli paketler: pip install pandas scikit-learn matplotlib joblib
"""
import os, sys
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, f1_score, classification_report, ConfusionMatrixDisplay
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

OZELLIKLER = ["gw_ping_ok", "gw_rtt_ms", "ext_ping_ok", "rtt_avg", "rtt_std",
              "loss_pct", "dns_ok", "dns_time_ms", "tcp_ok", "tcp_ms"]

dosya = sys.argv[1] if len(sys.argv) > 1 else "data/ornek_veri.csv"
os.makedirs("sonuclar", exist_ok=True)

df = pd.read_csv(dosya)
print(f"Veri: {dosya} — {len(df)} satır\n{df['label'].value_counts()}\n")
X, y = df[OZELLIKLER], df["label"]
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=0)

modeller = {
    "Logistic Regression (baseline)": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
    "Decision Tree": DecisionTreeClassifier(max_depth=5, random_state=0),
    "Random Forest": RandomForestClassifier(n_estimators=200, random_state=0),
}

satirlar = []
cv = StratifiedKFold(5, shuffle=True, random_state=0)
for ad, m in modeller.items():
    cv_f1 = cross_val_score(m, X_tr, y_tr, cv=cv, scoring="f1_macro")
    m.fit(X_tr, y_tr)
    tahmin = m.predict(X_te)
    satirlar.append({"Model": ad,
                     "CV F1 (ort.)": round(cv_f1.mean(), 3),
                     "Test Accuracy": round(accuracy_score(y_te, tahmin), 3),
                     "Test F1 (macro)": round(f1_score(y_te, tahmin, average="macro"), 3)})
    print(f"=== {ad} ===\n{classification_report(y_te, tahmin, digits=3)}")

sonuc = pd.DataFrame(satirlar)
sonuc.to_csv("sonuclar/model_karsilastirma.csv", index=False)
print(sonuc.to_string(index=False))

# En iyi model
en_iyi_ad = sonuc.sort_values("Test F1 (macro)", ascending=False).iloc[0]["Model"]
en_iyi = modeller[en_iyi_ad]
joblib.dump(en_iyi, "sonuclar/en_iyi_model.joblib")
print(f"\nEn iyi model: {en_iyi_ad} -> sonuclar/en_iyi_model.joblib")

# Confusion matrix (Random Forest)
rf = modeller["Random Forest"]
fig, ax = plt.subplots(figsize=(7, 6))
ConfusionMatrixDisplay.from_estimator(rf, X_te, y_te, ax=ax, cmap="Blues", xticks_rotation=30, colorbar=False)
ax.set_title("Random Forest — Confusion Matrix (test verisi)")
ax.set_xlabel("Tahmin edilen"); ax.set_ylabel("Gerçek")
plt.tight_layout(); plt.savefig("sonuclar/confusion_matrix.png", dpi=150); plt.close()

# Feature importance
imp = pd.Series(rf.feature_importances_, index=OZELLIKLER).sort_values()
fig, ax = plt.subplots(figsize=(7, 4.5))
imp.plot.barh(ax=ax, color="#2E7D6B")
ax.set_title("Random Forest — Hangi ölçüm daha belirleyici?")
ax.set_xlabel("Önem (feature importance)")
plt.tight_layout(); plt.savefig("sonuclar/feature_importance.png", dpi=150); plt.close()

# Karar ağacı (ilk 3 seviye, okunabilir olsun diye)
dt = modeller["Decision Tree"]
fig, ax = plt.subplots(figsize=(16, 8))
plot_tree(dt, feature_names=OZELLIKLER, class_names=dt.classes_, filled=True, max_depth=3, fontsize=8, ax=ax, impurity=False)
plt.tight_layout(); plt.savefig("sonuclar/karar_agaci.png", dpi=130); plt.close()

print("Grafikler sonuclar/ klasörüne kaydedildi.")
