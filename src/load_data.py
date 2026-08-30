"""
CICIDS2017 CSV dosyalarını bellek dostu şekilde okuyup birleştirir ve
tek bir parquet dosyası olarak kaydeder (hızlı okuma + küçük disk alanı için).
"""
import glob
import os

import pandas as pd


def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """float64->float32, int64->int32 dönüşümüyle bellek kullanımını yaklaşık yarıya indirir."""
    float_cols = df.select_dtypes(include=["float64"]).columns
    df[float_cols] = df[float_cols].astype("float32")
    int_cols = df.select_dtypes(include=["int64"]).columns
    df[int_cols] = df[int_cols].astype("int32")
    return df


def load_all_csvs(raw_dir: str) -> pd.DataFrame:
    """raw_dir içindeki tüm CICIDS2017 günlük CSV dosyalarını okur ve birleştirir.
    Sütun adlarındaki baştaki/sondaki boşluklar (kaynak veri setinin bilinen bir sorunu) temizlenir.
    """
    csv_paths = sorted(glob.glob(os.path.join(raw_dir, "*.csv")))
    if not csv_paths:
        raise FileNotFoundError(f"{raw_dir} içinde CSV dosyası bulunamadı.")

    frames = []
    for path in csv_paths:
        print(f"Okunuyor: {os.path.basename(path)}")
        df = pd.read_csv(path, encoding="latin1", low_memory=False)
        df.columns = df.columns.str.strip()
        df = optimize_dtypes(df)
        df["source_file"] = os.path.basename(path)
        frames.append(df)
        print(f"  -> {len(df):,} satır, {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")

    combined = pd.concat(frames, ignore_index=True)
    print(f"\nToplam: {len(combined):,} satır, {combined.memory_usage(deep=True).sum() / 1e6:.1f} MB")
    return combined


if __name__ == "__main__":
    dataset = load_all_csvs("data/raw")
    os.makedirs("data/processed", exist_ok=True)
    dataset.to_parquet("data/processed/full.parquet", index=False)
    print("Kaydedildi: data/processed/full.parquet")
