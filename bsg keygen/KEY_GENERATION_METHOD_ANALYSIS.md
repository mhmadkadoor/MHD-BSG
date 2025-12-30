# Anahtar Üretim Yöntemi Analizi (BSG)

Bu doküman, [bsg keygen/key_generator.py](bsg%20keygen/key_generator.py) dosyasında bulunan anahtar üretim yöntemini açıklar.

Kapsam:
- `generate_key()` tarafından üretilen **değişken uzunluklu Collatz anahtarı** (int)
- `generate_key_bytes()` tarafından üretilen **sabit uzunluklu bayt akışı** (AES anahtarı + IV için)

> Not: Bu metin, 30 Aralık 2025 itibarıyla depodaki mevcut implementasyonu anlatır.

---

## 1) Girdiler ve çıktılar

### Seed (tohum)
- Üretici bir **seed (tamsayı)** kullanır.
- Seed verilmezse zamandan türetilir:
  - `seed = datetime.now().microsecond`

Bu varsayılan davranış her çalıştırmada farklı sonuç üretir (deterministik değildir) ve ayrıca **entropisi düşüktür** (yaklaşık 1.000.000 olası değer).

### Çıktılar
İki farklı çıktı tipi vardır:

1) `generate_key(seed) -> int`
- Collatz yolunun uzunluğuna bağlı olarak **değişken bit uzunluğuna** sahip bir tamsayı döner.

2) `generate_key_bytes(n_bytes, seed) -> bytes`
- **Tam olarak `n_bytes`** uzunluğunda bayt döner (aynı seed için deterministiktir)
- Sarmalayıcılar:
  - `generate_aes_key(seed)` → 16 bayt
  - `generate_aes_iv(seed)` → 16 bayt

---

## 2) Temel fikir: Collatz paritesinden bit üretmek

Her iki yöntem de **Collatz dönüşümünü** kullanır ve mevcut değerin tek/çift olmasına göre bit üretir.

### Ön işleme
Her iki yöntem seed’i önce kaydırır:

- `value = seed - 5`
- `value <= 1` ise `value = 2` yapılır

Amaç 0/1 gibi durumların hemen bitirmesini engellemektir.

### Collatz adımı + bit ekleme
Her iterasyonda:

- Çıktı 1 bit sola kaydırılır.
- `value` **tek** ise:
  - Bit `0` eklenir
  - `value = 3*value + 1`
- `value` **çift** ise:
  - Bit `1` eklenir
  - `value = value / 2`

Yani özetle:
- `value` tek → `bit = 0`
- `value` çift → `bit = 1`

---

## 3) Yöntem A: `generate_key(seed)` (değişken uzunluk)

### Ne yapar?
`generate_key()` Collatz adımlarını, dizi `1` olana kadar sürdürür ve bu süreçte üretilen bitleri bir tamsayıda toplar.

Farklı seed değerleri farklı Collatz yol uzunluklarına sahip olabileceği için anahtarın bit sayısı **değişkendir**.

### Akış diyagramı

```mermaid
flowchart TD
  A[seed] --> B[value = seed - 5]
  B --> C{value <= 1?}
  C -- Evet --> D[value = 2]
  C -- Hayır --> E[key = 0]
  D --> E
  E --> F{value > 1?}
  F -- Hayır --> Z[return key]
  F -- Evet --> G[key <<= 1]
  G --> H{value tek mi?}
  H -- Evet --> I[bit ekle: 0\nvalue = 3*value + 1]
  H -- Hayır --> J[bit ekle: 1\nkey |= 1\nvalue = value / 2]
  I --> F
  J --> F
```

### Pseudocode

```
value = seed - 5
if value <= 1:
    value = 2

key = 0
while value > 1:
    key = key << 1
    if value is odd:
        # bit 0
        value = 3*value + 1
    else:
        # bit 1
        key = key | 1
        value = value / 2

return key
```

---

## 4) Yöntem B: `generate_key_bytes(n_bytes, seed)` (sabit uzunluk)

### Neden var?
AES sabit uzunluk ister:
- AES-128 anahtar: **16 bayt**
- CBC IV: **16 bayt**

`generate_key()` bit sayısını garanti edemediği için, `generate_key_bytes()` **tam olarak** `n_bytes * 8` bit üretir.

### “Collatz tabanlı” kalması
Üretilen her bit yine Collatz paritesinden gelir. Fark, şu **yeniden başlatma kuralıdır**:

- Collatz dizisi `1`’e ulaşıp biterse ve hâlâ yeterli bit üretilmemişse, `value` yeni bir değere ayarlanır ve bit üretimi devam eder.

### Yeniden başlatma kuralı (kritik)
`value <= 1` olduğunda:

- `value = ((seed_value ^ (out & 0xFFFFFFFF)) + 2) | 1`

Açıklama:
- `seed_value`: orijinal seed
- `out`: o ana kadar birikmiş bitler
- `out & 0xFFFFFFFF`: birikmiş bitlerin yalnızca alt 32 bitini karıştırır
- `+ 2`: çok küçük değerleri önler
- `| 1`: değeri tek yapar (sonraki adımın “tek → 0” ile başlamasını garanti eder)

### Akış diyagramı

```mermaid
flowchart TD
  A[seed_value] --> B[value = seed_value - 5]
  B --> C{value <= 1?}
  C -- Evet --> D[value = 2]
  C -- Hayır --> E[out=0, bits_out=0]
  D --> E
  E --> F{bits_out < bits_needed?}
  F -- Hayır --> Z[return out as n_bytes]\
  F -- Evet --> R{value <= 1?}
  R -- Evet --> S[value = ((seed_value XOR (out & 0xFFFFFFFF)) + 2) OR 1]
  R -- Hayır --> G[out <<= 1]
  S --> G
  G --> H{value tek mi?}
  H -- Evet --> I[bit 0\nvalue = 3*value + 1]
  H -- Hayır --> J[bit 1\nout |= 1\nvalue = value/2]
  I --> K[bits_out += 1]
  J --> K
  K --> F
```

### Pseudocode

```
assert n_bytes > 0

bits_needed = n_bytes * 8
seed_value = seed or current_microsecond

value = seed_value - 5
if value <= 1:
    value = 2

out = 0
bits_out = 0

while bits_out < bits_needed:
    if value <= 1:
        value = ((seed_value XOR (out & 0xFFFFFFFF)) + 2) OR 1

    out = out << 1

    if value is odd:
        # bit 0
        value = 3*value + 1
    else:
        # bit 1
        out = out OR 1
        value = value / 2

    bits_out += 1

return out as big-endian bytes of length n_bytes
```

---

## 5) Determinizm ve tekrarlanabilirlik

- `--seed` verirseniz tüm çıktılar deterministik olur.
- Seed vermezseniz `datetime.now().microsecond` kullanıldığı için her çalıştırmada farklı sonuçlar gelir.

Örnek kullanım:
- `python "bsg keygen/key_generator.py" --seed 123456`
- `python "bsg keygen/key_generator.py" --seed 123456 --bytes 32`

Örnek ( `--seed 123456` ile deterministik çıktılar ):

- `generate_key(123456)`
  - bit sayısı: 86
  - hex: `2d7bf56badeab5f5ef56ef`
- `generate_aes_key(123456)` (16 bayt): `5af7ead75bd56bebdeaddeded57edaf7`
- `generate_aes_iv(123456)`  (16 bayt): `5af7ead75bd56bebdeaddeded57edaf7`
- `generate_key_bytes(32, 123456)` (32 bayt):
  - `5af7ead75bd56bebdeaddeded57edaf75b5babeab56d6bb76adad5aabbab6b76`

---

## 6) Güvenlik notları (önemli)

Bu yöntem **kriptografik olarak güvenli bir anahtar türetme fonksiyonu değildir**:

- Varsayılan seed (`microsecond`) düşük entropilidir ve brute-force ile denenebilir.
- Collatz paritesi saldırgana karşı “tasarlanmış” bir rastgelelik değildir.
- Salt yoktur, maliyet/faktör yoktur, standart bir güvenlik varsayımı yoktur.

Gerçek güvenlik gerekiyorsa (simülasyon/eğitim değilse) tipik alternatifler:
- Rastgele AES anahtarı: `secrets.token_bytes(16)`
- Paroladan türetme: HKDF / PBKDF2 / scrypt / Argon2

Yine de bu repo bağlamında, seed verildiğinde üretim yöntemi deterministik ve tutarlıdır.
