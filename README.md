# ml-network-ids

Ağ trafiği kayıtlarını (flow verisi) analiz ederek DDoS, port taraması, brute force, botnet ve web saldırılarını otomatik tespit eden bir makine öğrenmesi sistemi. CICIDS2017 veri setiyle eğitilmiş, sızıntısız (leakage-free) bir deney kurulumuyla ikili ve çok sınıflı sınıflandırma sonuçları karşılaştırılmış, sonuçlar canlı bir Gradio demosunda sunulmuştur.

**Canlı demo:** https://huggingface.co/spaces/suput01/ml-network-ids

## Problem Tanımı

Geleneksel imza tabanlı saldırı tespit sistemleri (IDS) sadece bilinen saldırı kalıplarını yakalayabilir. Bu proje, ağ akışı istatistiklerinden (paket boyutu, süre, bayrak sayıları vb.) öğrenen anomali/ML tabanlı bir yaklaşımla hem bilinen saldırı türlerini yüksek doğrulukla sınıflandırmayı hem de bunu yaparken IDS literatüründe sık görülen "şişirilmiş skor" tuzağına (veri sızıntısı) düşmemeyi amaçlar.

## Veri Seti

**CICIDS2017** (Canadian Institute for Cybersecurity) — Kaggle aynası: [chethuhn/network-intrusion-dataset](https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset) (CC0). 8 günlük gerçekçi ağ trafiği kaydı, 2.830.743 satır, 78 flow özelliği, BENIGN + 14 saldırı alt türü.

Ham veri lisans/boyut nedeniyle repoya dahil edilmemiştir (`data/` gitignore'da, ~1GB). `src/load_data.py` ile yeniden üretilebilir.

## Yöntem

1. **Veri yükleme ve temizleme** (`src/load_data.py`, `src/clean.py`): dtype optimizasyonu (float64→float32), Inf/NaN/negatif-hız satırlarının temizlenmesi, sabit+kopya sütunların silinmesi, kopya satırların (%9) atılması, 14 alt saldırı türünün 7 ana kategoriye (BENIGN, DoS/DDoS, PortScan, BruteForce, WebAttack, Botnet, Infiltration) indirgenmesi.
2. **Sızıntısız deney kurulumu** (`src/features.py`): kimlik/meta sütunların (`source_file`) özellik dışı bırakılması, %70/%15/%15 stratified split, `StandardScaler`'ın sadece train'de fit edilmesi, `Destination Port` sızıntı riskinin ölçülmesi (sonuç: %0.7 önem payı — güvenli).
3. **İkili sınıflandırma** (`notebooks/02_binary_models.ipynb`): Lojistik Regresyon, Random Forest, XGBoost karşılaştırması; recall odaklı değerlendirme.
4. **Çok sınıflı sınıflandırma** (`notebooks/03_multiclass.ipynb`): En iyi model (XGBoost) 7 kategoriyle yeniden eğitilir; SMOTE (sadece train'e, hedeflenmiş sayıda) denenip makro-F1 üzerindeki etkisi raporlanır.
5. **Demo** (`app/app.py`): Kullanıcı flow formatında bir CSV yükler, sistem her satırı sınıflandırıp özet saldırı raporu üretir.

## Sonuçlar

**İkili sınıflandırma (Normal vs Saldırı):**

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC | Eğitim süresi |
|---|---|---|---|---|---|---|
| Lojistik Regresyon | 0.9409 | 0.7451 | 0.9769 | 0.8454 | 0.9885 | 377s |
| Random Forest | 0.9985 | 0.9961 | 0.9950 | 0.9956 | 0.9997 | 256s |
| **XGBoost** | **0.9991** | 0.9949 | **0.9994** | **0.9972** | **1.0000** | **59s** |

**Çok sınıflı sınıflandırma (XGBoost, SMOTE ile):** Makro F1 = 0.940, Ağırlıklı F1 = 0.999. Sınıf başına detay için [`results/multiclass_per_class_report.csv`](results/multiclass_per_class_report.csv).

Detaylı analiz: [`results/metrics.md`](results/metrics.md), [`report/teknik_rapor.pdf`](report/teknik_rapor.pdf).

**Önemli bulgular:**
- XGBoost hem en hızlı (59s) hem en iyi recall'a (%99.94) sahip model — IDS'te en kritik metrik olan "kaçırılmayan saldırı" açısından en güvenilir seçim.
- `Destination Port` gibi potansiyel sızıntı riski taşıyan özellik, gerçek önem payının sadece %0.7 olduğu doğrulanarak güvenle kullanılabilir bulundu — model port ezberlemiyor, trafiğin gerçek şekline (paket boyutu, zamanlama, header oranı) bakıyor.
- Çok sınıflı modelde saldırı **türleri** birbiriyle neredeyse hiç karışmıyor (BruteForce/DoS/PortScan diyagonalde 1.00); asıl hata deseni az örnekli sınıfların (Botnet, Infiltration) BENIGN'e kaçması — bu, model hatasından çok veri kıtlığının doğal bir sonucu.

## Kurulum ve Çalıştırma

```bash
git clone https://github.com/canci01/ml-network-ids.git
cd ml-network-ids
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

[Kaggle'dan](https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset) CSV dosyalarını indirip `data/raw/` altına yerleştirin, ardından:

```bash
python src/load_data.py                                                          # data/processed/full.parquet uretir
python src/clean.py                                                              # data/processed/clean.parquet uretir
jupyter nbconvert --to notebook --execute --inplace notebooks/02_binary_models.ipynb
jupyter nbconvert --to notebook --execute --inplace notebooks/03_multiclass.ipynb
python app/app.py                                                                 # Gradio demosunu yerelde calistirir
```

## Sınırlılıklar ve Gelecek Çalışmalar

- **Laboratuvar veri seti ≠ gerçek ağ trafiği:** CICIDS2017, kontrollü bir test ortamında üretilmiştir; gerçek kurumsal ağların gürültüsünü, çeşitliliğini ve ölçeğini tam yansıtmayabilir.
- **Kavram kayması (concept drift):** Saldırı teknikleri zamanla evrilir; 2017 veri setiyle eğitilen bir model, günümüzün yeni saldırı varyantlarına karşı test edilmemiştir.
- **Gerçek zamanlı akış işleme kapsam dışıdır** — bu proje toplu (batch) CSV analizi yapar, canlı ağ trafiğini dinlemez.
- **Aşırı az örnekli sınıflar** (Infiltration: 36 satır) için güvenilir bir genelleme değerlendirmesi yapılamaz.
- **(Opsiyonel, yapılmadı) UNSW-NB15 ile çapraz doğrulama:** CLAUDE.md'de önerilen genellenebilirlik testi (farklı bir veri setinde yöntemi sıfırdan eğitip test etme) zaman kısıtı nedeniyle bu sürümde yapılmamıştır; gelecek çalışma olarak planlanmaktadır.
- **Gelecek çalışmalar:** UNSW-NB15 doğrulaması, SHAP ile daha derin açıklanabilirlik analizi, gerçek zamanlı akış entegrasyonu.

## Etik ve Güvenlik Notu

Bu proje yalnızca savunma amaçlıdır: saldırı **tespiti** yapar; saldırı üreten, tarama yapan veya exploit içeren hiçbir kod repoda bulunmaz. Sadece kamuya açık, akademik lisanslı veri seti kullanılmıştır. **Not:** Eğitim/araştırma amaçlıdır; üretim ortamı IDS'i yerine geçmez.

## Proje Yapısı

Bkz. [`CLAUDE.md`](CLAUDE.md) — geliştirme planı ve klasör yapısı.
