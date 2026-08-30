# CLAUDE.md — Yapay Zeka Destekli Ağ Saldırı Tespit Sistemi (IDS)

> Bu dosya, projenin tam geliştirme planı ve Claude ile çalışırken kullanılacak proje bağlamıdır.
> Her oturumda bu dosyayı referans al; adımları sırayla, atlamadan uygula.

---

## 1. PROJE ÖZETİ

**Proje adı:** `ml-network-ids`
**Amaç:** Ağ trafiği kayıtlarını (flow verisi) analiz ederek DDoS, port taraması, brute force, botnet gibi saldırı türlerini otomatik tespit eden ve sınıflandıran bir makine öğrenmesi sistemi geliştirmek.
**Hedef:** Siber Güvenlik Başkanlığı / savunma sanayii başvuruları için ikinci portföy projesi. İlk proje (tr-phishing-detector) metin sınıflandırmaydı; bu proje tablo verisi + anomali tespiti becerisi ekleyerek portföyü genişletir.
**Geliştirici profili:** Bir projeyi bitirmiş başlangıç-orta seviye. Ağ trafiği kavramları YENİ — her ağ terimi ilk geçtiğinde kısaca açıklanmalı.

**Başarı kriterleri:**
- [ ] İkili sınıflandırma (normal/saldırı) VE çok sınıflı sınıflandırma (saldırı türü) sonuçları
- [ ] En az 3 model karşılaştırması (Lojistik Regresyon, Random Forest, XGBoost)
- [ ] Özellik önemi (feature importance) analizi — "model neye bakarak karar veriyor?"
- [ ] Gerçekçi değerlendirme: veri sızıntısı (data leakage) kontrolü yapılmış
- [ ] Canlı demo: CSV yükle → saldırı raporu al (Gradio/Streamlit)
- [ ] Teknik rapor (PDF)

---

## 2. ALAN BİLGİSİ — BAŞLAMADAN OKU

**IDS nedir?** Intrusion Detection System = Saldırı Tespit Sistemi. Ağ trafiğini izler, şüpheli aktiviteyi raporlar. İki yaklaşım: imza tabanlı (bilinen saldırı kalıpları) ve anomali/ML tabanlı (bu proje).

**Flow (akış) nedir?** Ham paketleri tek tek incelemek yerine, aynı kaynak-hedef arasındaki paket grubunun özet istatistikleri: süre, paket sayısı, bayt sayısı, bayrak sayıları vb. Veri setlerimiz bu formatta — yani her satır bir bağlantı özeti, her sütun bir istatistik.

**Bu projede tespit edilecek saldırı türleri:**
| Saldırı | Ne yapar? |
|---|---|
| DDoS/DoS | Hedefi trafik bombardımanıyla hizmet dışı bırakır |
| Port Scan | Açık kapıları (portları) tarayarak keşif yapar |
| Brute Force | Parolaları deneme-yanılmayla kırmaya çalışır (FTP/SSH) |
| Botnet | Ele geçirilmiş cihazların komuta trafiği |
| Web saldırıları | SQL injection, XSS vb. |
| Infiltration | İçeri sızma sonrası hareket |

---

## 3. TEKNOLOJİ YIĞINI

| Katman | Araç | Neden |
|---|---|---|
| Dil | Python 3.10+ | Standart |
| Veri işleme | pandas, numpy | Büyük CSV'ler için `dtype` optimizasyonu önemli |
| Klasik ML | scikit-learn | Baseline + metrikler |
| Gradient boosting | XGBoost (veya LightGBM) | Tablo veride en güçlü model ailesi |
| Dengesizlik | imbalanced-learn | SMOTE / undersampling |
| Görselleştirme | matplotlib, seaborn | EDA, feature importance, ROC |
| Açıklanabilirlik | SHAP (opsiyonel, ileri seviye) | "Model neden bu kararı verdi?" |
| Demo | Gradio veya Streamlit | CSV yükle → rapor |
| Ortam | Yerel makine yeterli (GPU GEREKMEZ) | Tablo verisi, derin öğrenme şart değil |

---

## 4. VERİ SETLERİ

**Ana veri seti: CICIDS2017** (Canadian Institute for Cybersecurity)
- Kaynak: https://www.unb.ca/cic/datasets/ids-2017.html (Kaggle aynaları da var: "CICIDS2017" ara)
- 5 günlük gerçekçi trafik; normal + 14 saldırı türü; ~2.8 milyon satır, 78 özellik sütunu
- Format: MachineLearningCSV klasöründeki CSV dosyaları

**Doğrulama veri seti: UNSW-NB15**
- Kaynak: https://research.unsw.edu.au/projects/unsw-nb15-dataset (Kaggle'da da mevcut)
- 9 saldırı kategorisi; hazır train/test ayrımı var
- Kullanım amacı: CICIDS2017'de eğitilen yaklaşımın başka veri setinde de çalıştığını göstermek (genellenebilirlik) — bu, raporu güçlendiren ileri seviye bir adımdır; zorunlu değil, Aşama 5'te opsiyonel.

**⚠️ CICIDS2017 bilinen sorunları (raporda belirtmek artı puan):**
1. Bazı CSV'lerde sütun adlarında baştaki/sondaki boşluklar var → `df.columns = df.columns.str.strip()`
2. `Infinity` ve `NaN` değerler var (özellikle Flow Bytes/s sütunlarında) → temizlenmeli
3. Ciddi sınıf dengesizliği: bazı saldırılar milyonlarca, bazıları birkaç yüz örnek
4. Literatürde bilinen etiketleme hataları vardır; %100'e yakın skorlar şüpheyle karşılanmalı — bunu bilmek ve söylemek olgunluk göstergesidir

---

## 5. REPO YAPISI

```
ml-network-ids/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── .gitignore                 # data/, models/, __pycache__
├── data/
│   ├── raw/                   # İndirilen CSV'ler (git'e GİRMEZ, ~1GB+)
│   └── processed/             # Temizlenmiş, örneklenmiş parquet dosyaları
├── notebooks/
│   ├── 01_eda.ipynb           # Keşif + temizlik kararları
│   ├── 02_binary_models.ipynb # Normal vs Saldırı
│   ├── 03_multiclass.ipynb    # Saldırı türü sınıflandırma
│   └── 04_evaluation.ipynb    # Karşılaştırma, feature importance, hata analizi
├── src/
│   ├── load_data.py           # Okuma + dtype optimizasyonu + birleştirme
│   ├── clean.py               # Temizlik fonksiyonları
│   ├── features.py            # Ölçekleme, encoding
│   └── train.py               # Eğitim pipeline'ı
├── app/
│   └── app.py                 # Demo: CSV yükle → tahmin raporu
├── models/                    # .joblib dosyaları (git'e GİRMEZ)
├── results/
│   ├── metrics.md
│   └── figures/
└── report/
    └── teknik_rapor.md
```

---

## 6. GELİŞTİRME PLANI — AŞAMA AŞAMA

### AŞAMA 0 — Kurulum (Gün 1)
1. Repo aç, sanal ortam kur.
2. `pip install pandas numpy scikit-learn xgboost imbalanced-learn matplotlib seaborn jupyter pyarrow`
3. `requirements.txt` + `.gitignore` + ilk commit.

**Tamamlanma kriteri:** İskelet repo GitHub'da.

### AŞAMA 1 — Veri İndirme ve Keşif (Gün 2-7)

**1.1 İndirme:** CICIDS2017 MachineLearningCSV'yi indir, `data/raw/` içine aç. Toplam ~1GB — sabırlı ol.

**1.2 Bellek dostu okuma (`src/load_data.py`):**
1. Tek dosyayla başla (örn. Wednesday — DoS ağırlıklı gün).
2. `float64→float32`, `int64→int32` dönüşümüyle belleği yarıya indir.
3. Tüm günleri birleştirip `data/processed/full.parquet` olarak kaydet (parquet: hızlı + küçük).

**1.3 EDA (`notebooks/01_eda.ipynb`):**
1. Sütun adlarını temizle (`str.strip()`), etiket dağılımını çıkar (bar grafiği, log ölçek — dengesizlik çok büyük).
2. `Infinity`/`NaN` içeren sütunları ve satır sayılarını raporla.
3. Sabit (varyansı 0) ve birbirinin kopyası sütunları tespit et → silinecekler listesi.
4. Saldırı vs normal için 4-5 anahtar özelliğin dağılımını karşılaştır (örn. Flow Duration, Packet Length Mean) — "saldırı trafiği gözle görülür şekilde farklı mı?" sorusuna grafiklerle cevap ver.
5. Bulguları markdown hücresine yaz.

**1.4 Temizlik kararları (`src/clean.py`):**
1. `Inf → NaN → satır sil` (oranı raporla; %1'in altındaysa silmek güvenli).
2. Sabit ve kopya sütunları çıkar.
3. Etiketleri sadeleştir: 14 alt tür → 7 ana kategori (BENIGN, DoS/DDoS, PortScan, BruteForce, WebAttack, Botnet, Infiltration) — eşleme sözlüğünü kodda açıkça yaz.

**Tamamlanma kriteri:** Temiz `full.parquet` + bulgular yazılmış EDA notebook'u commit'te.

### AŞAMA 2 — Veri Sızıntısına Karşı Doğru Deney Kurulumu (Gün 8-10)

**Bu aşama projenin EN KRİTİK kısmı.** IDS literatüründe şişirilmiş skorların ana nedeni hatalı deney kurulumudur. Kurallar:

1. **Kimlik sütunlarını asla özellik olarak kullanma:** Flow ID, Source IP, Destination IP, Source Port, Timestamp → SİL. (Model "bu IP saldırgandı" diye ezberler; gerçek dünyada işe yaramaz. Destination Port tartışmalıdır — önce dahil et, feature importance'ta aşırı baskınsa çıkarıp farkı raporla.)
2. **Ölçekleme fit'i sadece train'de:** `StandardScaler().fit(X_train)` → `transform(X_test)`. Asla tüm veride fit etme.
3. **SMOTE sadece train setine uygulanır**, test setine ASLA.
4. Ayrım: %70/%15/%15, `stratify=y`, `random_state=42`.
5. Veri çok büyükse (2.8M satır) eğitim süresini kısaltmak için stratified örnekleme ile ~500K satırlık çalışma seti oluşturabilirsin — bunu raporda belirt.

**Tamamlanma kriteri:** `features.py` içinde sızıntısız pipeline hazır; silinen kimlik sütunları ve gerekçeleri kodda yorum olarak yazılı.

### AŞAMA 3 — İkili Sınıflandırma: Normal vs Saldırı (Gün 11-17)

**`notebooks/02_binary_models.ipynb`:**
1. Etiket: BENIGN=0, diğer her şey=1.
2. Üç model eğit ve karşılaştır:
   - `LogisticRegression(class_weight='balanced')` — baseline
   - `RandomForestClassifier(n_estimators=100, class_weight='balanced', n_jobs=-1)`
   - `XGBClassifier(scale_pos_weight=oran)` — genelde kazanan
3. Metrikler: precision, recall, F1, ROC-AUC. **IDS'te odak metrik recall'dur** (kaçan saldırı = en pahalı hata), ama false positive oranını da raporla (SOC analistini yanlış alarma boğmak da maliyetlidir — bu dengeyi kurabilmek mülakat altınıdır).
4. Confusion matrix + ROC eğrisi → `results/figures/`.
5. Random Forest ve XGBoost için feature importance grafiği: en önemli 15 özellik. Her birinin ağ anlamını 1 cümleyle açıkla (örn. "SYN Flag Count yüksek → SYN flood DDoS işareti").

**Tamamlanma kriteri:** 3 modelin karşılaştırma tablosu + feature importance analizi hazır.

### AŞAMA 4 — Çok Sınıflı Sınıflandırma: Saldırı Türü (Gün 18-24)

**`notebooks/03_multiclass.ipynb`:**
1. 7 ana kategoriyle en iyi modeli (muhtemelen XGBoost) yeniden eğit.
2. Sınıf başına precision/recall/F1 tablosu — makro ortalama ve ağırlıklı ortalama farkını açıkla.
3. 7x7 confusion matrix (normalize edilmiş, ısı haritası).
4. **Hata analizi:** En çok karışan sınıf çiftlerini bul (örn. DoS türleri birbirine karışır — normaldir, açıkla). Az örnekli sınıflarda (Infiltration, Botnet) düşük skor beklenir; SMOTE deneyip fark yaratıp yaratmadığını raporla.

**Tamamlanma kriteri:** Çok sınıflı sonuç tablosu + karışıklık analizi yazılmış.

### AŞAMA 5 — (OPSİYONEL, İLERİ) Genellenebilirlik Testi (Gün 25-28)
1. UNSW-NB15'i indir, ortak özellik alt kümesini eşle (birebir aynı sütunlar yok — kısmi eşleme yeterli).
2. CICIDS2017 yaklaşımını UNSW üzerinde sıfırdan eğit-test et (cross-dataset transfer DEĞİL; o çok zordur).
3. "Yöntemim iki farklı veri setinde de çalışıyor" bölümü olarak rapora ekle.

### AŞAMA 6 — Demo (Gün 29-32)

**`app/app.py` (Gradio):**
1. Kullanıcı flow formatında bir CSV yükler (repoya 100 satırlık `sample_input.csv` koy).
2. Sistem her satırı sınıflandırır, özet rapor üretir:
   - "1000 akıştan 37'si şüpheli: 30 DDoS, 5 PortScan, 2 BruteForce"
   - Şüpheli satırların tablosu + güven skorları
   - Basit pasta/bar grafiği
3. Model `joblib` ile yüklenir; ölçekleyici de kaydedilmiş olmalı (pipeline olarak kaydet, ayrı ayrı değil).
4. HF Spaces'e yükle (CPU yeterli).

**Tamamlanma kriteri:** Canlı link çalışıyor, örnek CSV ile test edilmiş.

### AŞAMA 7 — Dokümantasyon (Gün 33-36)
1. README: problem → veri → yöntem → sonuç tablosu → demo linki → sınırlılıklar.
2. Sınırlılıklar bölümüne mutlaka yaz: laboratuvar veri seti ≠ gerçek ağ trafiği; kavram kayması (concept drift — saldırılar zamanla evrilir); gerçek zamanlı akış işleme bu projenin kapsamı dışında.
3. Teknik rapor PDF (phishing projesindeki şablonla aynı yapı).
4. LinkedIn paylaşımı + CV satırı.

---

## 7. KODLAMA KURALLARI
1. Yorumlar Türkçe, adlandırma İngilizce; her fonksiyona docstring.
2. `random_state=42` her yerde.
3. Her kod bloğundan sonra ne yapıldığını 2-3 cümleyle açıkla; ağ terimlerini ilk geçtiğinde tanımla.
4. Ölçekleyici + model tek `Pipeline` nesnesi olarak kaydedilir (sızıntı ve demo kolaylığı için).
5. Bir aşamanın tamamlanma kriteri karşılanmadan sonrakine geçilmez.
6. Commit formatı: `feat|fix|docs|data|exp: açıklama`.
7. `data/` ve `models/` commit edilmez.

## 8. ETİK VE GÜVENLİK NOTLARI
1. Proje YALNIZCA savunma amaçlı: saldırı TESPİT eder; saldırı ÜRETEN, tarama yapan veya exploit içeren hiçbir kod repoda bulunmaz.
2. Sadece kamuya açık, akademik lisanslı veri setleri kullanılır; gerçek ağlardan trafik toplanmaz.
3. Demo sayfası notu: "Eğitim/araştırma amaçlıdır; üretim ortamı IDS'i yerine geçmez."

## 9. SIK SORUNLAR VE ÇÖZÜMLER
| Sorun | Çözüm |
|---|---|
| Bellek yetmiyor (2.8M satır) | dtype küçült, parquet kullan, stratified örnekleme ile 500K'ya in |
| Skorlar şüpheli derecede yüksek (%99.9) | Kimlik sütunu sızıntısı ara; Aşama 2 kontrol listesini yeniden uygula |
| XGBoost `Inf` hatası | Temizlik adımını kontrol et: `df.replace([np.inf,-np.inf], np.nan)` |
| SMOTE çok yavaş | Önce undersampling ile BENIGN'i küçült, sonra SMOTE |
| Az örnekli sınıflar hep yanlış | Sınıf birleştirme kararını raporla; odak metrik olarak makro-F1 kullan |
| Demo'da farklı sütunlu CSV çöküyor | Beklenen sütun listesini doğrula, eksikte anlaşılır hata mesajı göster |

## 10. İLERLEME TAKİBİ
- [x] Aşama 0: Kurulum
- [x] Aşama 1: Veri + EDA + temizlik
- [x] Aşama 2: Sızıntısız deney kurulumu
- [x] Aşama 3: İkili sınıflandırma (3 model)
- [x] Aşama 4: Çok sınıflı sınıflandırma
- [ ] Aşama 5: (Ops.) UNSW-NB15 doğrulaması
- [ ] Aşama 6: Demo
- [ ] Aşama 7: Dokümantasyon
