# SAP IF Design Generation Tool - Technical Architecture

## System Architecture Overview

```mermaid
graph TB
    subgraph APP["🎯 Application Layer"]
        direction LR
        CLI["CLI Interface<br/>--file, --langu, --provider"]
        MAIN["Main Orchestrator<br/>Multi-file Processing"]
        CFG["Configuration<br/>Environment & Settings"]
    end

    subgraph BIZ["💼 Business Logic Layer"]
        direction LR
        EXCEL["Excel Processor<br/>Field Extraction"]
        CUSTOM["Custom CDS Matcher<br/>Priority Search"]
        CDS["Standard CDS Matcher<br/>LLM Selection"]
        BATCH["Batch Processor<br/>Concurrent Tasks"]
    end

    subgraph AI["🤖 SAP AICore Service Layer"]
        direction LR
        SELECTOR["AICore Selector<br/>Auto-detection"]
        CLAUDE["Claude<br/>Bedrock API"]
        GEMINI["Gemini<br/>Vertex AI"]
        OPENAI["OpenAI<br/>GPT"]
    end

    subgraph PROMPT["📝 Prompt & Schema Layer"]
        direction LR
        PMGR["Prompt Manager<br/>Templates"]
        SMGR["Schema Manager<br/>Function Schemas"]
        I18N["i18n<br/>en/zh/ja"]
    end

    subgraph DATA["💾 Data Access Layer"]
        direction LR
        HANA["HANA Client<br/>Vector Ops"]
        VSEARCH["Vector Search<br/>Cosine Similarity"]
        TABLES["Tables<br/>Scenarios/Views/Fields"]
    end

    subgraph INTG["🔗 Integration Layer"]
        direction LR
        ODATA["OData Service<br/>Verification"]
        FS["File System<br/>I/O/Archive"]
        TOKEN["Token Tracker<br/>Usage Stats"]
    end

    subgraph UTIL["🔧 Utility Layer"]
        direction LR
        LOG["Logger<br/>Multi-file Logs"]
        MODEL["Data Models<br/>InterfaceField"]
        HELP["Helpers<br/>Utilities"]
    end

    %% Layer connections
    CLI -.-> MAIN
    MAIN --> CFG
    MAIN --> EXCEL
    MAIN --> LOG
    
    EXCEL --> CUSTOM
    EXCEL --> CDS
    EXCEL --> BATCH
    EXCEL --> MODEL
    
    CUSTOM --> HANA
    CDS --> SELECTOR
    CDS --> HANA
    BATCH --> SELECTOR
    
    SELECTOR --> CLAUDE
    SELECTOR --> GEMINI
    SELECTOR --> OPENAI
    
    CLAUDE --> PMGR
    GEMINI --> PMGR
    OPENAI --> PMGR
    CLAUDE -.-> SMGR
    GEMINI -.-> SMGR
    OPENAI -.-> SMGR
    
    PMGR --> I18N
    
    HANA --> VSEARCH
    HANA --> TABLES
    
    EXCEL --> ODATA
    EXCEL --> FS
    SELECTOR --> TOKEN
    
    %% Styling
    classDef appStyle fill:#e1f5ff,stroke:#0066cc,stroke-width:2px,color:#000
    classDef bizStyle fill:#fff4e1,stroke:#ff9900,stroke-width:2px,color:#000
    classDef aiStyle fill:#ffe1f5,stroke:#cc00cc,stroke-width:2px,color:#000
    classDef promptStyle fill:#f0e1ff,stroke:#6600cc,stroke-width:2px,color:#000
    classDef dataStyle fill:#e1ffe1,stroke:#009900,stroke-width:2px,color:#000
    classDef intgStyle fill:#ffe1e1,stroke:#cc0000,stroke-width:2px,color:#000
    classDef utilStyle fill:#f5f5f5,stroke:#666666,stroke-width:2px,color:#000
    
    class CLI,MAIN,CFG appStyle
    class EXCEL,CUSTOM,CDS,BATCH bizStyle
    class SELECTOR,CLAUDE,GEMINI,OPENAI aiStyle
    class PMGR,SMGR,I18N promptStyle
    class HANA,VSEARCH,TABLES dataStyle
    class ODATA,FS,TOKEN intgStyle
    class LOG,MODEL,HELP utilStyle
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