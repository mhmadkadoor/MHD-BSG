import random
import logging
import sys
import time
from pathlib import Path

# Setup logging
LOG_FILE = Path(__file__).parent / "rsa_demo.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("RSA_Demo")

class RSA:
    """
    A simple educational implementation of RSA encryption and digital signatures.
    NOTE: This is for demonstration purposes only. NOT for production security.
    """

    def __init__(self, key_size=1024):
        self.key_size = key_size
        self.public_key = None
        self.private_key = None

    def gcd(self, a, b):
        while b != 0:
            a, b = b, a % b
        return a

    def multiplicative_inverse(self, e, phi):
        d = 0
        x1 = 0
        x2 = 1
        y1 = 1
        temp_phi = phi

        while e > 0:
            temp1 = temp_phi // e
            temp2 = temp_phi - temp1 * e
            temp_phi = e
            e = temp2

            x = x2 - temp1 * x1
            y = d - temp1 * y1

            x2 = x1
            x1 = x
            d = y1
            y1 = y

        if temp_phi == 1:
            return d + phi

    def is_prime(self, num):
        if num == 2:
            return True
        if num < 2 or num % 2 == 0:
            return False
        for n in range(3, int(num**0.5) + 2, 2):
            if num % n == 0:
                return False
        return True

    def generate_large_prime(self, keysize):
        """Generates a prime number roughly of keysize bits."""
        while True:
            num = random.randrange(2**(keysize-1), 2**(keysize))
            if self.is_prime(num):
                return num

    def generate_keys(self):
        logger.info("Generating prime numbers (this might take a moment)...")
        # For demo speed, we use smaller primes if key_size is small, 
        # but for the requested code let's stick to something fast enough for a demo.
        # Using small primes for instant execution in this demo script.
        # In real RSA, these would be much larger.
        
        # Generating actual large primes in pure python is slow without Miller-Rabin.
        # I will implement a simple Miller-Rabin for better performance/realism if needed,
        # but for a "one click demo", let's use smaller pre-calculated logic or a faster check.
        
        # Let's implement Miller-Rabin for better speed on larger numbers
        def is_prime_mr(n, k=5):
            if n == 2 or n == 3: return True
            if n % 2 == 0: return False

            r, s = 0, n - 1
            while s % 2 == 0:
                r += 1
                s //= 2
            for _ in range(k):
                a = random.randrange(2, n - 1)
                x = pow(a, s, n)
                if x == 1 or x == n - 1:
                    continue
                for _ in range(r - 1):
                    x = pow(x, 2, n)
                    if x == n - 1:
                        break
                else:
                    return False
            return True

        def generate_prime_candidate(length):
            p = random.getrandbits(length)
            p |= (1 << length - 1) | 1
            return p

        def generate_prime_number(length=1024):
            p = 4
            while not is_prime_mr(p, 128):
                p = generate_prime_candidate(length)
            return p

        # Use a smaller bit size for the demo to ensure it runs instantly
        # 512 bits is decent for a quick demo.
        bit_length = self.key_size // 2
        
        logger.info(f"Finding p (approx {bit_length} bits)...")
        p = generate_prime_number(bit_length)
        logger.info("Found p.")
        
        logger.info(f"Finding q (approx {bit_length} bits)...")
        q = generate_prime_number(bit_length)
        logger.info("Found q.")

        n = p * q
        phi = (p - 1) * (q - 1)

        e = 65537
        logger.info("Calculating private exponent d...")
        d = self.multiplicative_inverse(e, phi)

        self.public_key = (e, n)
        self.private_key = (d, n)
        
        logger.info("Keys generated successfully.")
        return (self.public_key, self.private_key)

    def encrypt(self, message, package):
        e, n = package
        # Convert string to int
        msg_int = int.from_bytes(message.encode('utf-8'), byteorder='big')
        if msg_int >= n:
            raise ValueError("Message is too long for the key size")
        cipher_int = pow(msg_int, e, n)
        return cipher_int

    def decrypt(self, cipher_int, package):
        d, n = package
        msg_int = pow(cipher_int, d, n)
        # Convert int back to string
        # Calculate number of bytes needed
        byte_len = (msg_int.bit_length() + 7) // 8
        return msg_int.to_bytes(byte_len, byteorder='big').decode('utf-8')

    def sign(self, message, private_key):
        """Signs a message hash (simulated) using private key."""
        # In real world, we sign the HASH of the message.
        # Here we'll just sign the message directly for simplicity, 
        # or a simple hash if it's too long.
        # Let's just sign the message directly assuming it's short.
        d, n = private_key
        msg_int = int.from_bytes(message.encode('utf-8'), byteorder='big')
        signature = pow(msg_int, d, n)
        return signature

    def verify(self, message, signature, public_key):
        e, n = public_key
        msg_int = int.from_bytes(message.encode('utf-8'), byteorder='big')
        # Decrypt signature to get the message hash/content
        decrypted_sig = pow(signature, e, n)
        return msg_int == decrypted_sig

def main():
    logger.info("=== RSA DEMO STARTED ===")
    
    # Initialize RSA
    rsa = RSA(key_size=512) # 512 bits for speed in demo
    
    # 1. Key Generation
    logger.info("--- Step 1: Key Generation ---")
    pub, priv = rsa.generate_keys()
    logger.info(f"Public Key (e, n): ({pub[0]}, {str(pub[1])[:20]}...)")
    logger.info(f"Private Key (d, n): ({str(priv[0])[:20]}..., {str(priv[1])[:20]}...)")

    # 2. Encryption / Decryption
    logger.info("\n--- Step 2: Encryption / Decryption ---")
    message = "Hello, this is a secret message!"
    logger.info(f"Original Message: {message}")
    
    encrypted_msg = rsa.encrypt(message, pub)
    logger.info(f"Encrypted (Ciphertext): {str(encrypted_msg)[:50]}...")
    
    decrypted_msg = rsa.decrypt(encrypted_msg, priv)
    logger.info(f"Decrypted Message: {decrypted_msg}")
    
    if message == decrypted_msg:
        logger.info("SUCCESS: Decrypted message matches original.")
    else:
        logger.error("FAILURE: Messages do not match.")

    # 3. Digital Signature
    logger.info("\n--- Step 3: Digital Signature ---")
    doc = "Authorize Payment: $500"
    logger.info(f"Document to sign: {doc}")
    
    signature = rsa.sign(doc, priv)
    logger.info(f"Signature generated: {str(signature)[:50]}...")
    
    is_valid = rsa.verify(doc, signature, pub)
    if is_valid:
        logger.info("SUCCESS: Signature verified correctly.")
    else:
        logger.error("FAILURE: Signature verification failed.")

    # 4. Tampering Test
    logger.info("\n--- Step 4: Tampering Test ---")
    tampered_doc = "Authorize Payment: $50000"
    logger.info(f"Tampered Document: {tampered_doc}")
    is_valid_tampered = rsa.verify(tampered_doc, signature, pub)
    
    if not is_valid_tampered:
        logger.info("SUCCESS: Tampered document rejected.")
    else:
        logger.error("FAILURE: Tampered document was accepted!")

    logger.info("\n=== RSA DEMO COMPLETED ===")
    print(f"\nFull logs saved to: {LOG_FILE}")
    
    # Keep window open if run via double-click
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
