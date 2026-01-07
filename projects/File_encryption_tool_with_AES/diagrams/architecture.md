```mermaid
flowchart TD
    subgraph EncryptionTool["File Encryption Tool"]
        direction TB
        A[User Interface] -->|CLI/GUI| B[Encryption/Decryption Module]
        B --> C[Key Management Module]
        B --> D[Error Handling & Logging Module]
    end

    subgraph EncryptionProcess["Encryption Process"]
        direction LR
        E[Select File & Enter Key] --> F[Read File]
        F --> G[Encrypt File]
        G --> H[Save Encrypted File]
        H --> I[Log Success]
    end

    subgraph DecryptionProcess["Decryption Process"]
        direction LR
        J[Select Encrypted File & Enter Key] --> K[Read File]
        K --> L[Decrypt File]
        L --> M[Save Decrypted File]
        M --> N[Log Success]
    end

    subgraph KeyManagement["Key Management"]
        direction TB
        O[Generate Key] --> P[Store Key]
        P --> Q[Retrieve Key]
    end

    subgraph Interfaces["Interfaces"]
        direction TB
        R[CLI] -->|Commands: encrypt, decrypt, generate-key| A
        S[GUI] -->|Buttons & Input Fields| A
    end

    EncryptionTool -->|Uses| EncryptionProcess
    EncryptionTool -->|Uses| DecryptionProcess
    EncryptionTool -->|Uses| KeyManagement
    EncryptionTool -->|Provides| Interfaces
```

This diagram represents the architecture of a file encryption tool using AES. It includes modules for encryption/decryption, key management, error handling, and logging. The tool supports both CLI and GUI interfaces for user interaction. The data flow for encryption and decryption processes is shown, highlighting the steps from file selection to logging the success of operations. Key management processes such as key generation, storage, and retrieval are also depicted.