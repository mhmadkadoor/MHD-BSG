# Secure Connection Flow

This document explains how the `sender`, `unsecureTunnel`, and `receiver` establish a secure communication channel using a Hybrid Encryption scheme (RSA + DES).

## Components

1.  **Receiver (`receiver.py`)**: The server that holds the RSA Private Key and waits for messages.
2.  **Unsecure Tunnel (`unsecureTunnel.py`)**: A "Man-in-the-Middle" proxy that forwards traffic between Sender and Receiver. It can see the traffic but cannot decrypt the secure messages.
3.  **Sender (`sender.py`)**: The client that initiates the connection and sends encrypted messages.

## Protocol Steps

### 1. Initialization (Receiver)
*   **Action**: When `receiver.py` starts.
*   **Operation**: It generates a fresh **RSA 2048-bit Key Pair** (Public Key and Private Key).
*   **State**: The Receiver is now listening on port `65433`.

### 2. Connection & Public Key Exchange
*   **Action**: `sender.py` connects to `unsecureTunnel.py` (port `65432`), which forwards the connection to `receiver.py`.
*   **Handshake**:
    1.  **Receiver** immediately sends its **RSA Public Key** (in PEM format) to the Sender.
    2.  **Sender** receives and loads the Public Key.
    *   *Note: The Tunnel sees this Public Key, but it is public information.*

### 3. Session Key Exchange (Hybrid Encryption)
*   **Goal**: Establish a shared symmetric key for fast encryption (DES).
*   **Action**:
    1.  **Sender** generates a random **8-byte DES Key** (the Session Key).
    2.  **Sender** encrypts this DES Key using the **Receiver's RSA Public Key** (using OAEP padding with SHA-256).
    3.  **Sender** sends the encrypted key with the prefix `KEY:` (e.g., `KEY:<Base64 Encrypted Data>`).
    4.  **Receiver** receives the message, extracts the payload, and decrypts it using its **RSA Private Key**.
*   **Result**: Both Sender and Receiver now possess the same **DES Key**. The Tunnel only saw the encrypted blob and cannot derive the key.

### 4. Secure Messaging
*   **Action**: User types a message in the Sender terminal.
*   **Encryption (Sender)**:
    1.  Generates a random **8-byte IV** (Initialization Vector) for this specific message.
    2.  Pads the message to be a multiple of 8 bytes (DES block size).
    3.  Encrypts the message using **DES-CBC Mode** with the Session Key and IV.
    4.  Concatenates `IV + Ciphertext`.
    5.  Encodes the result in Base64.
    6.  Sends `MSG:<Base64 Payload>`.
*   **Forwarding**: The Tunnel logs the message `MSG:...` but sees only gibberish.
*   **Decryption (Receiver)**:
    1.  Decodes the Base64 payload.
    2.  Extracts the first 8 bytes as the **IV**.
    3.  Decrypts the rest using **DES-CBC** with the Session Key and extracted IV.
    4.  Unpads the result to get the original plaintext.
    5.  Prints the decrypted message.

## Diagram

```mermaid
sequenceDiagram
    participant Sender
    participant Tunnel
    participant Receiver

    Note over Receiver: Generate RSA Key Pair
    Sender->>Tunnel: Connect
    Tunnel->>Receiver: Connect
    Receiver-->>Sender: Send RSA Public Key (PEM)
    
    Note over Sender: Generate Random DES Key
    Note over Sender: Encrypt DES Key with RSA Public Key
    Sender->>Receiver: KEY: <Encrypted DES Key>
    Note over Receiver: Decrypt DES Key with RSA Private Key
    
    Note over Sender: User types "Hello"
    Note over Sender: Encrypt "Hello" with DES Key + IV
    Sender->>Receiver: MSG: <IV + DES Ciphertext>
    Note over Receiver: Decrypt with DES Key + IV
    Note over Receiver: Print "Hello"
```
