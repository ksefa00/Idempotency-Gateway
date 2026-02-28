1. ## Architecture Diagram

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
```

2. ## Setup Instructions

 Requirements
- Python 3.10+
- Git

 Clone Repository
```powershell
git clone https://github.com/ksefa00/Idempotency-Gateway.git
cd Idempotency-Gateway

## Create Virtual Environment
 python -m venv venv

 ## Activate Virtual Environment (Windows PowerShell)
  .\venv\Scripts\Activate.ps1

## Install Dependencies
pip install -r requirements.txt

## Run the Server
uvicorn main:app --reload

So the server will run at: http://127.0.0.1:8000

API documentation is available at: http://127.0.0.1:8000/docs
```


## 3. API Documentation

GET /

Health check endpoint.

**Response**
```json
{
  "message": "Idempotency Gateway is running"
}

##  POST /process-payment

Processes a payment request.

Header

Idempotency-Key: <unique-string>

Request Body
{
  "amount": 100,
  "currency": "GHS"
}

## First Request Response

- Status: 201 Created

- Header: X-Cache-Hit: false

- Body:
{
  "message": "Charged 100.0 GHS"
}

## Duplicate Request Response

- Status: 201 Created

- Header: X-Cache-Hit: true

- Same response body as first request

Conflict (Same Key, Different Body)

- Status: 409 Conflict

- Body:
{
  "detail": "Idempotency key already used for a different request body."
}
```

## 4. Design Decisions
- Used in-memory dictionary as allowed by the challenge.

- Used stable JSON hashing to detect payload tampering.

- Stored both response body and status code to ensure exact replay.

- Used async locking to prevent race conditions.

- Implemented in-flight waiting so concurrent identical requests do not double-process.

