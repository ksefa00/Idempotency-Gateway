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

### Requirements
- Python 3.10+
- Git

### Clone Repository
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

3. ## API Documentation section
Examples:
POST /process-payment

Header: Idempotency-Key: test123

Body: {"amount":100,"currency":"GHS"}

Response: "Charged 100 GHS"

