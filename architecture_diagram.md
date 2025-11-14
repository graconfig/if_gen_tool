# SAP IF Design Generation Tool - Technical Architecture Diagram

## System Architecture Overview

```mermaid
graph TB
    %% Input Layer
    subgraph "Input Layer"
        A[Excel Files] --> B[Excel Processor]
        A1[Configuration Files] --> B
    end

    %% Core Processing Layer
    subgraph "Core Processing Layer"
        B --> C[Field Extraction Engine]
        C --> D{Custom Field Priority Match}
        D -->|Found| E[Direct Match Results]
        D -->|Not Found| F[CDS View Processing]

        F --> G[Business Scenario Discovery]
        G --> H[AI-Powered View Selection]
        H --> I[Vector-based Field Matching]
        I --> J[AI Field Mapping]
    end

    %% AI Services Layer
    subgraph "AI Services Layer"
        K[AI Service Manager]
        L[Claude Service]
        M[Gemini Service]
        N[OpenAI Service]
        K --> L
        K --> M
        K --> N
        J --> K
        H --> K
    end

    %% Data Layer
    subgraph "Data Layer (SAP HANA)"
        O[HANA DB Client]
        P[Business Scenarios Table]
        Q[CDS Views Table]
        R[View Fields Table]
        S[Custom Fields Table]

        O --> P
        O --> Q
        O --> R
        O --> S

        G --> O
        I --> O
    end

    %% Verification Layer
    subgraph "Verification Layer"
        T[OData Verification Service]
        E --> U[Result Aggregation]
        J --> U
        U --> V{OData Verification Enabled?}
        V -->|Yes| T
        V -->|No| W[Final Results]
        T --> W
    end

    %% Output Layer
    subgraph "Output Layer"
        W --> X[Processed Excel Files]
        W --> Y[Processing Logs]
        W --> Z[Token Usage Reports]
    end

    %% Cross-cutting Concerns
    subgraph "Cross-cutting Services"
        AA[Configuration Manager]
        AB[Logging Service]
        AC[i18n Service]
        AD[Token Statistics Tracker]
    end

    AA --> B
    AA --> K
    AA --> O
    AB --> B
    AB --> K
    AC --> B
    AD --> K
```

## Component Interaction Flow

```mermaid
sequenceDiagram
    participant Main as Main Application
    participant Excel as Excel Processor
    participant HANA as HANA Database
    participant AI as AI Services
    participant OData as OData Service

    Main->>Excel: Process Excel File
    Excel->>Excel: Extract Interface Fields

    alt Custom Field Priority Match
        Excel->>HANA: Vector Search Custom Fields
        HANA-->>Excel: Custom Field Matches
    else No Custom Match Found
        Excel->>HANA: Search Business Scenarios
        HANA-->>Excel: Scenario Data

        Excel->>AI: Select Relevant CDS Views
        AI-->>Excel: Selected Views

        Excel->>HANA: Get View Field Details
        HANA-->>Excel: Field Information

        Excel->>AI: Map Input Fields to View Fields
        AI-->>Excel: Field Mapping Results
    end

    Excel->>Excel: Aggregate Results

    alt OData Verification Enabled
        Excel->>OData: Verify Field Mappings
        OData-->>Excel: Verification Results
    end

    Excel->>Excel: Generate Output Excel
    Excel-->>Main: Processing Complete
```

## Technology Stack

### Core Technologies
- **Language**: Python 3.12
- **Excel Processing**: openpyxl, pandas
- **Database**: SAP HANA Cloud
- **Vector Operations**: HANA VECTOR_EMBEDDING
- **AI Framework**: SAP AI Core Integration

### AI Services
- **Claude**: Anthropic Claude via SAP AI Core
- **Gemini**: Google Gemini via SAP AI Core
- **OpenAI**: GPT models via SAP AI Core

### Data Processing
- **Batch Processing**: ThreadPoolExecutor
- **Vector Search**: Cosine similarity with SAP NEB model
- **Multi-language**: Japanese, English, Chinese support

### Integration Points
- **SAP Systems**: OData services for verification
- **File System**: Excel input/output/archive management
- **Configuration**: Environment-based configuration
- **Logging**: Structured logging with file-specific tracking

## Key Architectural Patterns

### 1. **Pipeline Processing Pattern**
- Sequential stages of field processing
- Conditional routing based on match results
- Result aggregation and verification

### 2. **Service Layer Pattern**
- Abstracted AI service interfaces
- Provider-agnostic service selection
- Automatic fallback and resilience

### 3. **Repository Pattern**
- HANA database abstraction
- Vector search operations
- Data access object (DAO) pattern

### 4. **Strategy Pattern**
- Different column mapping strategies (SAP vs Standard)
- Configurable processing strategies
- Language-specific prompt management

### 5. **Observer Pattern**
- Token usage tracking
- Progress monitoring and logging
- Error handling and recovery

## Scalability Features

### Parallel Processing
- Multi-threaded batch processing
- Concurrent file processing
- Configurable concurrency limits

### Resource Management
- Connection pooling for HANA
- Memory-efficient Excel handling
- Token usage optimization

### Error Isolation
- Failed batch isolation
- Independent file processing
- Graceful degradation patterns