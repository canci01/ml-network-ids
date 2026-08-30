"""
Veri sızıntısına karşı güvenli özellik/deney kurulumu (bu projenin EN KRİTİK modülü).

IDS literatüründeki şişirilmiş skorların ana nedeni hatalı deney kurulumudur:
- Kimlik sütunları (IP, port, zaman damgası) özellik olarak kullanılırsa model "bu IP hep
  saldırgandı" gibi ezberler yapar; gerçek dünyada hiç görmediği bir IP karşısında işe yaramaz.
- Ölçekleyici tüm veriyle fit edilirse test setinin istatistikleri (ortalama/varyans) train
  aşamasına sızmış olur (data leakage) ve test skoru gerçekte olduğundan iyi görünür.
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Bu sütunlar modelin "ezberlemesine" yol açabileceği için ÖZELLİK OLARAK KULLANILMAZ.
# (CICIDS2017'nin bu sürümünde IP/Timestamp sütunları zaten yok; source_file de sizinti riski taşır
# çünkü hangi güne ait olduğunu değil, doğrudan hangi saldırı senaryosunun çalıştığı günü ele verir.)
IDENTITY_COLUMNS = [
    "Flow ID", "Source IP", "Src IP", "Destination IP", "Dst IP",
    "Source Port", "Src Port", "Timestamp", "source_file",
]
# "Destination Port" tartışmalıdır: gerçek bir bilgi taşır (443/80/22 gibi bilinen servis portları),
# bu yüzden başta dahil edilir. Aşama 3'te feature importance'ta aşırı baskın çıkarsa çıkarılıp
# fark raporlanacaktır (yorum: bkz. notebooks/02_binary_models.ipynb).

LABEL_COLUMNS = ["Label", "Category", "IsAttack"]


def get_feature_columns(df: pd.DataFrame) -> list:
    """Kimlik ve etiket sütunları hariç, modelin kullanacağı özellik sütunlarını döndürür."""
    exclude = set(IDENTITY_COLUMNS) | set(LABEL_COLUMNS)
    return [c for c in df.columns if c not in exclude]


def split_data(df: pd.DataFrame, target_col: str, random_state: int = 42):
    """%70/%15/%15 train/val/test ayrımı yapar (stratify=target_col ile sınıf oranları korunur)."""
    train_df, temp_df = train_test_split(
        df, test_size=0.30, random_state=random_state, stratify=df[target_col]
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=0.50, random_state=random_state, stratify=temp_df[target_col]
    )
    return train_df, val_df, test_df


def fit_scaler(train_df: pd.DataFrame, feature_cols: list) -> StandardScaler:
    """Ölçekleyiciyi SADECE train verisiyle fit eder (kritik kural: test/val'i asla görmez)."""
    scaler = StandardScaler()
    scaler.fit(train_df[feature_cols])
    return scaler
