## Architecture Flowchart

```mermaid
flowchart TD
    A[POST /process-payment] --> B{Idempotency-Key present?}
    B -- No --> C[Return 400 Bad Request]
    B -- Yes --> D[Compute request body hash]
    D --> E{Does key exist?}

    E -- No --> F[Store key as IN_FLIGHT]
    F --> G[Simulate processing 2 seconds]
    G --> H[Store response as COMPLETED]
    H --> I[Return response]

    E -- Yes --> J{Does hash match?}
    J -- No --> K[Return 409 Conflict]
    J -- Yes --> L{Status?}

    L -- COMPLETED --> M[Return cached response]
    L -- IN_FLIGHT --> N[Wait until completed]
    N --> M