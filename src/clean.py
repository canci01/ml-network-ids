"""
CICIDS2017 birleşik veri setini temizleme fonksiyonları:
Inf/NaN satırlarını atma, sabit/kopya sütunları silme, kopya satırları atma,
14 alt saldırı türünü 7 ana kategoriye indirgeme.
"""
import numpy as np
import pandas as pd

# Bilinen sabit (varyansı 0) sütunlar — her satırda aynı değeri taşıdığından modele katkısı yok.
CONSTANT_COLUMNS = [
    "Bwd PSH Flags", "Bwd URG Flags",
    "Fwd Avg Bytes/Bulk", "Fwd Avg Packets/Bulk", "Fwd Avg Bulk Rate",
    "Bwd Avg Bytes/Bulk", "Bwd Avg Packets/Bulk", "Bwd Avg Bulk Rate",
]
# "Fwd Header Length.1", "Fwd Header Length" ile birebir aynı (dogrulandi) -> kopya sütun.
DUPLICATE_COLUMNS = ["Fwd Header Length.1"]

# Fiziksel olarak anlamsız (negatif bir hiz olamaz) satirlar; CICFlowMeter'in
# nadir durumlarda urettigi bilinen bir hata (sadece 115/2.8M satirda gorulur).
RATE_COLUMNS = ["Flow Bytes/s", "Flow Packets/s"]

# 14 alt saldiri turunu 7 ana kategoriye indirgeyen kural tabanli esleme.
# Not: Kaynak CSV'lerdeki "Web Attack" etiketlerinde encoding bozuklugu var
# (ör. "Web Attack ï¿½ Brute Force"), bu yuzden tam string yerine alt string eslemesi kullanilir.
def map_to_category(label: str) -> str:
    """Ham 'Label' değerini 7 ana saldırı kategorisinden birine eşler."""
    if label == "BENIGN":
        return "BENIGN"
    if label == "PortScan":
        return "PortScan"
    if label == "Bot":
        return "Botnet"
    if label == "Infiltration":
        return "Infiltration"
    if "Web Attack" in label:
        return "WebAttack"
    if label.endswith("Patator"):
        return "BruteForce"
    if label.startswith("DoS") or label in ("DDoS", "Heartbleed"):
        return "DoS/DDoS"
    return "Other"


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Tüm temizleme adımlarını sırayla uygular ve özet istatistikleri yazdırır."""
    df = df.drop(columns=[c for c in CONSTANT_COLUMNS + DUPLICATE_COLUMNS if c in df.columns])

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)

    before = len(df)
    df = df.dropna(subset=numeric_cols)
    inf_nan_dropped = before - len(df)
    print(f"Inf/NaN nedeniyle silinen satır: {inf_nan_dropped} (%{100 * inf_nan_dropped / before:.3f})")

    before = len(df)
    df = df.drop_duplicates()
    duplicate_dropped = before - len(df)
    print(f"Tam kopya nedeniyle silinen satır: {duplicate_dropped} (%{100 * duplicate_dropped / before:.2f})")

    before = len(df)
    for col in RATE_COLUMNS:
        df = df[df[col] >= 0]
    negative_rate_dropped = before - len(df)
    print(f"Negatif hız (Flow Bytes/s veya Flow Packets/s < 0) nedeniyle silinen satır: {negative_rate_dropped}")

    df["Category"] = df["Label"].apply(map_to_category)
    df["IsAttack"] = (df["Category"] != "BENIGN").astype(int)

    print("\nKategori dağılımı:")
    print(df["Category"].value_counts())

    return df


if __name__ == "__main__":
    dataset = pd.read_parquet("data/processed/full.parquet")
    cleaned = clean_dataset(dataset)
    cleaned.to_parquet("data/processed/clean.parquet", index=False)
    print(f"\nKaydedildi: data/processed/clean.parquet ({len(cleaned):,} satır)")
