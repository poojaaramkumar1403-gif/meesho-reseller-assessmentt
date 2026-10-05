# Meesho Reseller Growth & Alert Intelligence Pipeline

An end-to-end automated monitoring system for Meesho reseller operations. This system ingests relational sales data, executes SQL business metrics, enforces Python data quality guardrails, calculates deterministic growth flags, and formats human-reviewed alert notifications.

---

## 1. System Architecture & Workflow Pattern Map

The pipeline mirrors a robust enterprise reporting workflow:

```text
  [Relational DB / SQLite]
             │
             ▼
[Part 1: SQL Engine] ──> Generates Monthly Baseline Metrics (CSV)
             │
             ▼
[Part 2: Python Engine] ─> Validates Schema & Computes Threshold Flags
             │
             ▼
[Part 3: Narrative Layer] ─> Formats Data-Grounded Alerts (Template/Masking)
             │
             ▼
[Part 4: Agentic Workflow] ─> Orchestrates Pipeline & Emits JSON Summary