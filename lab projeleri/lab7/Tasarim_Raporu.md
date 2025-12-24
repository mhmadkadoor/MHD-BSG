# Kriptografik Algoritma Tasarım Raporu: SimpleSwap-8

**Ders:** Kriptografi ve Ağ Güvenliği  
**Tarih:** 19.12.2025  
**Aşama:** 1 - Algoritma Tasarımı ve Şartname

---

## 1. Algoritmanın Adı
**SimpleSwap-8**

## 2. Gerekçe ve Felsefe

### Tasarım Kararları
SimpleSwap-8, modern blok şifreleme prensiplerinin (karıştırma ve yayılma) temel bir düzeyde uygulanmasını amaçlayan, eğitim odaklı simetrik bir blok şifreleme algoritmasıdır. 

*   **Blok Yapısı:** Algoritma, veriyi 8 karakterlik (64-bit) bloklar halinde işler. Bu, her karakterin bağımsız şifrelendiği akış şifrelerine göre frekans analizini zorlaştırır.
*   **Hibrit Yapı:** Hem **İkame (Substitution)** hem de **Permütasyon (Permutation)** tekniklerini birleştirir.
    *   *İkame:* Anahtar değerlerinin metin değerlerine eklenmesiyle (Vigenère benzeri) karakter değerleri değiştirilir.
    *   *Permütasyon:* Blok içerisindeki verinin ters çevrilmesi (reverse) ile konumları değiştirilir.
*   **Çift Katmanlı Güvenlik:** Anahtar, permütasyon işleminden önce ve sonra olmak üzere iki kez uygulanır. Bu, "Sandviç" yapısı oluşturarak lineer analizi zorlaştırmayı hedefler.

### Hedeflenen Güvenlik
Bu tasarım, basit tek alfabeli (monoalphabetic) yerine koyma şifrelerine ve sadece yer değiştirme (transposition) şifrelerine karşı dayanıklı olmayı amaçlar. Permütasyon adımı, bitişik karakterler arasındaki ilişkiyi bozarak (yayılma), şifreli metindeki desenlerin gizlenmesine yardımcı olur.

## 3. Algoritma Özellikleri (Şartname)

*   **Algoritma Tipi:** Blok Şifre (Block Cipher)
*   **Blok Boyutu:** 64 bit (8 Karakter / Byte)
*   **Anahtar Boyutu:** 64 bit (8 Karakter). Eğer anahtar kısa ise 'X' ile doldurulur (padding), uzun ise kırpılır.
*   **Kullanılan İşlemler:**
    1.  Toplamsal Kaydırma (Additive Shift / Substitution)
    2.  Dizi Ters Çevirme (Reverse Array / Permutation)

## 4. Detaylı Şema (Akış)

### Şifreleme Süreci (Encryption)
1.  **Hazırlık:** Düz metin (Plaintext), 8'in katı olacak şekilde boşluk karakteri ile doldurulur (Padding).
2.  **Bloklama:** Metin 8 karakterlik bloklara ayrılır.
3.  **Her Blok İçin İşlemler:**
    *   **Adım 1 (ASCII Dönüşümü):** Karakterler sayısal ASCII değerlerine çevrilir.
    *   **Adım 2 (1. Tur - İkame):** Her blok elemanı, anahtarın karşılık gelen elemanı ile toplanır.
    *   **Adım 3 (Permütasyon):** Elde edilen dizi ters çevrilir (Reverse).
    *   **Adım 4 (2. Tur - İkame):** Ters çevrilmiş dizinin her elemanı, anahtarın karşılık gelen elemanı ile tekrar toplanır.
4.  **Çıktı:** Elde edilen sayısal değerler şifreli metni oluşturur.

### Deşifreleme Süreci (Decryption)
Şifreleme adımlarının tam tersi sırayla uygulanır:
1.  **Adım 1 (2. Tur Tersi):** Şifreli değerlerden anahtar çıkarılır.
2.  **Adım 2 (Permütasyon Tersi):** Dizi tekrar ters çevrilir (Reverse işleminin tersi kendisidir).
3.  **Adım 3 (1. Tur Tersi):** Elde edilen değerlerden anahtar tekrar çıkarılır.
4.  **Sonuç:** Sayısal değerler karakterlere dönüştürülür ve dolgu karakterleri temizlenir.

## 5. Matematiksel Fonksiyonlar

Bir blok $P$ (Plaintext) ve Anahtar $K$ (Key) 8 elemanlı vektörler olarak düşünülsün:
$$ P = [p_0, p_1, ..., p_7] $$
$$ K = [k_0, k_1, ..., k_7] $$

### Şifreleme (Encryption)
1.  **1. Tur (Toplama):**
    $$ R1_i = p_i + k_i $$
    *(Burada $i = 0..7$)*

2.  **Permütasyon (Ters Çevirme):**
    $$ Perm_i = R1_{7-i} $$
    $$ Perm_i = p_{7-i} + k_{7-i} $$

3.  **2. Tur (Toplama):**
    $$ C_i = Perm_i + k_i $$
    
    **Genel Şifreleme Denklemi:**
    $$ C_i = (p_{7-i} + k_{7-i}) + k_i $$

### Deşifreleme (Decryption)
Şifreli metin $C$ verildiğinde $P$'yi bulmak için:

1.  **2. Tur Tersi:**
    $$ Perm_i = C_i - k_i $$

2.  **Permütasyon Tersi:**
    $$ R1_i = Perm_{7-i} $$
    *(Tersin tersi düzdür)*

3.  **1. Tur Tersi:**
    $$ p_i = R1_i - k_i $$

    **Genel Deşifreleme Denklemi:**
    $$ p_i = (C_{7-i} - k_{7-i}) - k_i $$
