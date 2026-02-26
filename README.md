## Architecture Flowchart

```mermaid
flowchart TD
  A[POST /process-payment] --> B{Idempotency-Key present?}
  B -- No --> B1[400 Bad Request]
  B -- Yes --> C[Compute request body hash]
  C --> D{Key exists?}

  D -- No --> E[Store key: IN_FLIGHT + hash]
  E --> F[Simulate processing (2s)]
  F --> G[Store response + status COMPLETED]
  G --> H[Return response]

  D -- Yes --> I{Hash matches stored hash?}
  I -- No --> J[409/422 Error: key used for different body]
  I -- Yes --> K{Status?}

  K -- COMPLETED --> L[Return saved response + X-Cache-Hit: true]
  K -- IN_FLIGHT --> M[Wait until completed]
  M --> L