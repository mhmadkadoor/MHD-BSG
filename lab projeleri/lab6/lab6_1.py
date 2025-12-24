import hashlib
import time
import itertools
import string

def brute_force_attack():
    # 1. Verilen Bilgiler
    # Gündüz A için hedef hash değeri
    target_hash = "c22051c3f481b4bd916bb8d10f9d332ad29c1353baad0781f1971b44fabd320d"
    
    # Karakter kümesi: a-z ve 0-9
    charset = string.ascii_lowercase + string.digits
    
    # Başlangıç zamanını kaydet
    start_time = time.time()
    attempts = 0
    
    print(f"Hedef Hash: {target_hash}")
    print("Saldırı başlatılıyor (Uzunluk: 3-5 karakter, Karakterler: a-z, 0-9)...\n")

    # 2. Tarama İşlemi (3, 4 ve 5 karakter uzunlukları için)
    # range(3, 6) -> 3, 4, 5
    for length in range(3, 6):
        print(f"--- {length} karakterli kombinasyonlar deneniyor ---")
        
        # itertools.product ile tüm olası kombinasyonları oluşturur
        for p in itertools.product(charset, repeat=length):
            attempts += 1
            
            # Tuple'ı stringe çevir (ör: ('a', 'b', 'c') -> "abc")
            candidate_password = ''.join(p)
            
            # Aday parolanın SHA-256 hash'ini hesapla
            # .encode('utf-8') stringi byte'a çevirir, hexdigest() hex formatında hash verir
            candidate_hash = hashlib.sha256(candidate_password.encode('utf-8')).hexdigest()
            
            # 3. Karşılaştırma
            if candidate_hash == target_hash:
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                print("\n" + "="*30)
                print("       PAROLA BULUNDU!")
                print("="*30)
                print(f"Bulunan Parola     : {candidate_password}")
                print(f"Toplam Deneme      : {attempts}")
                print(f"Geçen Süre (saniye): {elapsed_time:.5f}")
                return # Bulunca fonksiyondan çık
                
    print("\nParola belirtilen aralıkta bulunamadı.")

if __name__ == "__main__":
    brute_force_attack()