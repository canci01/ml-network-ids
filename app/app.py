"""
Ağ Saldırı Tespit Demo (Gradio arayüzü).
Kullanıcı, CICFlowMeter formatında bir CSV yükler; sistem her satırı (akışı) sınıflandırıp
özet bir saldırı raporu üretir.
"""
import os
import sys

import gradio as gr
import joblib
import matplotlib.pyplot as plt
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "multiclass_best_model.joblib")
BUNDLE = joblib.load(MODEL_PATH)
SCALER = BUNDLE["scaler"]
MODEL = BUNDLE["model"]
LABEL_ENCODER = BUNDLE["label_encoder"]
FEATURE_COLUMNS = BUNDLE["feature_columns"]


def classify_csv(file_obj):
    """Yüklenen CSV'deki her akışı sınıflandırır; özet metin + şüpheli akış tablosu + grafik döndürür."""
    if file_obj is None:
        return "Lütfen bir CSV dosyası yükleyin.", None, None

    try:
        df = pd.read_csv(file_obj.name)
    except Exception as exc:  # noqa: BLE001
        return f"CSV okunamadı: {exc}", None, None

    df.columns = df.columns.str.strip()
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        preview = ", ".join(missing[:8]) + ("..." if len(missing) > 8 else "")
        return (
            f"Beklenen {len(missing)} sütun CSV'de bulunamadı (örn: {preview}). "
            "Lütfen CICFlowMeter formatında bir dosya yükleyin (bkz. app/sample_input.csv).",
            None,
            None,
        )

    X = df[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce")
    bad_rows = X.isna().any(axis=1) | ~X.replace([float("inf"), float("-inf")], pd.NA).notna().all(axis=1)
    X_clean = X[~bad_rows].fillna(0).replace([float("inf"), float("-inf")], 0)

    if len(X_clean) == 0:
        return "Hiçbir satır sayısal olarak işlenemedi; dosya formatını kontrol edin.", None, None

    X_scaled = SCALER.transform(X_clean)
    probs = MODEL.predict_proba(X_scaled)
    pred_idx = probs.argmax(axis=1)
    pred_labels = LABEL_ENCODER.inverse_transform(pred_idx)
    confidences = probs.max(axis=1)

    result_df = df.loc[X_clean.index].copy()
    result_df["Tahmin"] = pred_labels
    result_df["Güven"] = (confidences * 100).round(1)

    suspicious = result_df[result_df["Tahmin"] != "BENIGN"]
    category_counts = suspicious["Tahmin"].value_counts()

    total = len(result_df)
    n_suspicious = len(suspicious)
    if bad_rows.sum() > 0:
        skipped_note = f" ({bad_rows.sum()} satır sayısal olmayan/geçersiz değer nedeniyle atlandı)"
    else:
        skipped_note = ""

    if n_suspicious == 0:
        summary = f"✅ {total} akışın {skipped_note}tamamı normal (BENIGN) görünüyor."
    else:
        breakdown = ", ".join(f"{count} {cat}" for cat, count in category_counts.items())
        summary = f"⚠️ {total} akıştan{skipped_note} {n_suspicious}'i şüpheli: {breakdown}"

    fig = None
    if n_suspicious > 0:
        fig, ax = plt.subplots(figsize=(5, 3.5))
        category_counts.plot(kind="bar", ax=ax, color="#d95f5f")
        ax.set_ylabel("Akış sayısı")
        ax.set_title("Şüpheli Akışların Kategori Dağılımı")
        plt.tight_layout()

    suspicious_display = suspicious[["Tahmin", "Güven"]].reset_index(drop=True) if n_suspicious > 0 else None

    return summary, suspicious_display, fig


demo = gr.Interface(
    fn=classify_csv,
    inputs=gr.File(label="Flow CSV dosyanızı yükleyin (CICFlowMeter formatı)", file_types=[".csv"]),
    outputs=[
        gr.Textbox(label="Özet Rapor"),
        gr.Dataframe(label="Şüpheli Akışlar (varsa)"),
        gr.Plot(label="Kategori Dağılımı"),
    ],
    examples=[[os.path.join(os.path.dirname(__file__), "sample_input.csv")]],
    title="Yapay Zeka Destekli Ağ Saldırı Tespit Sistemi (IDS)",
    description=(
        "CICIDS2017 veri setiyle eğitilmiş bir XGBoost modeli, yüklediğiniz ağ akışı (flow) "
        "CSV'sindeki her satırı normal veya saldırı türlerinden biri (DoS/DDoS, PortScan, "
        "BruteForce, WebAttack, Botnet, Infiltration) olarak sınıflandırır. "
        "**Not:** Eğitim/araştırma amaçlıdır; üretim ortamı IDS'i yerine geçmez."
    ),
)

if __name__ == "__main__":
    demo.launch()
