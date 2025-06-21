# Scalable, Real-Time Synthetic Telco Data Generator: Design Document

## Overview

The goal is to build a data generator that produces not just random CDR/xDR records, but rich, realistic telecom data streams with meaningful patterns—enabling powerful analytics demos for platforms like Vast Data. This generator goes beyond "randomness" and tells compelling stories through simulated personas, scenarios, and events.

---

## Core Design Principles

- **Stateful Simulation:** The generator maintains the evolving state of a synthetic world, including subscribers and network elements, to enable longitudinal and cross-event patterns.
- **Persona-Driven:** Each subscriber has a persona (e.g., "Business Traveler," "Gamer," "IoT Device") that governs behavior and enables segment-specific scenarios.
- **Event-Driven / Scenario Engine:** A central scheduler injects time-based or triggered events to drive interesting patterns (e.g., outages, fraud, marketing campaigns).
- **Microservices Architecture:** Each generator component is a scalable, stateless service, communicating over a message bus (Kafka).
- **Real-Time Streaming:** Data is continuously streamed to Kafka topics, ready for ingestion by analytics platforms.

---

## High-Level Architecture

```mermaid
graph TD
    subgraph Stateful Core (The "Digital Twin")
        A[Subscriber Profile Database]
        B[Network Infrastructure Model]
    end

    subgraph Dynamic Engine (The "Puppet Master")
        C[Scenario & Event Injector]
    end

    subgraph Event Generators (The "Actors")
        D[CDR/xDR Generator]
        E[Network Log Generator]
        F[Customer Service Log Generator]
        G[Location Update Generator]
    end

    subgraph Streaming Platform
        H[Apache Kafka]
        H1(Topic: cdrs)
        H2(Topic: network_logs)
        H3(Topic: customer_service)
        H4(Topic: location_updates)
    end

    subgraph Analytics Platform
        I[Vast Data Database]
    end

    C --Triggers--> D
    C --Triggers--> E
    C --Triggers--> F
    C --Triggers--> G

    A --Provides Personas--> D
    A --Provides Personas--> F
    A --Provides Personas--> G
    B --Provides State--> D
    B --Provides State--> E
    B --Provides State--> G

    D --> H1
    E --> H2
    F --> H3
    G --> H4

    H1 --> I
    H2 --> I
    H3 --> I
    H4 --> I
```

---

## Component Breakdown

### 1. **Stateful Core ("Digital Twin")**
- **Subscriber Profile Database:** Stores millions of synthetic subscribers with fields like IMSI, Persona, ChurnScore, Home/Work Cells, SatisfactionScore, CLV, etc.
- **Network Infrastructure Model:** Physical network abstraction (cell towers, locations, capacity, etc.), with dynamic fields (CurrentLoad, Status).

### 2. **Dynamic Engine ("Puppet Master")**
- **Scenario & Event Injector:** Scheduler and orchestrator that triggers events, updates the stateful core, and instructs generators to produce scenario-driven data.

### 3. **Event Generators ("Actors")**
- **CDR/xDR Generator:** Produces session-level telecom data (calls, SMS, data) per persona, scenario, and injected events.
- **Network Log Generator:** Simulates syslog-like events for network infrastructure (errors, warnings, outages).
- **Customer Service Log Generator:** Simulates customer interactions (support calls, chats, complaints).
- **Location Update Generator:** Simulates subscriber/device movement between towers.

### 4. **Streaming Platform**
- **Apache Kafka:** Message bus. Each data type goes to a dedicated topic (e.g., cdrs, network_logs), decoupling producers from consumers.

---

## Example Patterns by Use Case

| Use Case Category | Scenario Name | How Implemented | Generated Data Pattern |
|-------------------|--------------|-----------------|-----------------------|
| Network Ops | Predictive Maintenance | Gradually increase error logs for a tower with aging hardware | Increasing error density on a single network element before failure |
| Network Ops | Capacity Congestion | Simulate a mass event (e.g., concert) overloading a tower | Spike in load, dropped calls, increased latency for specific locations |
| Customer Experience | Churn Prediction | Sequence: Billing dispute → Lower satisfaction → Reduced usage → Calls to competitor | Multi-step pattern: negative service, declining engagement, churn signals |
| Fraud | SIM Box Fraud | Multiple IMSIs on one IMEI, rapid international calls from one tower | Unnatural call patterns, static location, IMEI reuse |
| Revenue Assurance | Service Misconfiguration | Wrong QoS applied to premium plan | Mismatch between PlanID and session QoS/charging |
| Marketing | Targeted Upgrade | Identify high-usage, old-device users nearing contract end | Segment with specific IMEIs, high usage, not on latest plan |
| IoT | Fleet Failure | Firmware push causes mass auth failures for IoT devices | Spike in auth failures from IoT IMSI range, shared error cause |

---

## Implementation Notes

- **Tech Stack:**
  - Generators: Python (with Faker, scenario logic)
  - Stateful Core: Redis (dynamic state), PostgreSQL (persistent profiles)
  - Orchestration: Docker, Kubernetes (for scaling microservices)
  - Streaming: Apache Kafka
- **Scalability:** Microservices allow independent scaling. Kafka ensures high throughput and durability.

---

## Summary

This design enables synthetic data generation with the richness, complexity, and realism required for advanced analytics and compelling demos. By combining stateful simulation, scenario-driven events, and real-time streaming, it tells the kinds of "stories" that telecom data teams need to unlock value in platforms like Vast Data.
