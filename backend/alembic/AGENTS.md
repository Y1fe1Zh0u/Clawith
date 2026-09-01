# Alembic AGENTS.md — Clawith Database Migration Guidelines

> Auto-loads when editing anything under `backend/alembic/`.
> Read this **before** creating or editing a migration. Complements [`backend/AGENTS.md`](../AGENTS.md) and [`docs/constitution.md`](../../docs/constitution.md).

---

## 0. Clean-break Baseline and Single-head Rule

The target schema has one initial-baseline exception. Only after every first-release target model is frozen, all S0-S3 PostgreSQL gates pass, and every rewrite coverage row is terminal may the serialized baseline owner replace the legacy migration history with one target baseline generated from the single application metadata registry. The baseline targets an empty, explicitly named target database; it never upgrades, reads, repairs, or preserves an existing legacy database.

The baseline may downgrade to an empty database only in disposable test and development environments. That destructive downgrade is not an operational rollback or data-preservation promise.

After the target baseline is committed, it is immutable migration history. Every schema change is a forward migration from the current single head. Never regenerate the baseline, rewrite a released revision, add a second lineage, or introduce compatibility migrations for legacy tables, data, APIs, Redis keys, Workspace layouts, Runtime protocols, or storage paths.

> **A new migration's `down_revision` MUST be the current single head — never an older revision, and never guessed from the filename.**

Mounting a `down_revision` on an already-applied revision forks the migration graph into **multiple heads**. Multiple heads cause application startup failure (`alembic upgrade head` aborts with "Multiple head revisions present").

The migration graph MUST always have **exactly one head**:

```bash
cd backend
uv run alembic heads      # MUST print exactly ONE revision
```

---

## 1. Creating Migrations Safely

### 1.1 Preferred Method (Auto-fill `down_revision`)
Let Alembic load the current migration graph and determine `down_revision`:

```bash
cd backend
uv run alembic revision --autogenerate -m "add_agent_credentials_table"
```

### 1.2 Verification Step
After creating or hand-editing a migration, verify head integrity:

```bash
cd backend
uv run alembic heads      # Check that exactly ONE line is output
```

### 1.3 Preventing Multiple Heads

Migration creation is serialized. Rebase the schema change onto the current head and create its revision from that head before it is shared. Do not create parallel heads or repair an avoidable fork by editing released history.

---

## 2. DDL-Only Rule (纯 DDL 变更规范)

**Migrations are DDL-only — no inline data migration or cleaning.**

- **Permitted**: Schema DDL (`create_table`, `add_column`, `drop_table`, `alter_column`, `create_index`, `create_foreign_key`).
- **Permitted Default Fill**: Declarative `server_default` on an added column.
- **FORBIDDEN (Data Ops)**:
  - Reading rows then writing based on them (`SELECT` → `UPDATE` / `INSERT`).
  - Data dedup / cleanup / backfill / purge loops.
  - Operations conditional on existing business data state.

> **Why**: Inline data operations are non-resumable and can stall or timeout during startup on production databases with large datasets. Data migrations must be placed in a separate one-off script under `scripts/` or `backend/scripts/` to be run out-of-band.

---

## 3. Schema Ownership and Safety

- **Single metadata source**: `alembic/env.py` imports the application's one complete metadata registry. Do not construct another `MetaData`, declarative base, or partial migration-only model graph.
- **Owner-private persistence**: Each module owns its ORM models, repositories, tables, constraints, and indexes. Cross-owner work uses typed public services and the shared `TransactionContext`; migrations must not create a second write path or transfer table ownership implicitly.
- **No compatibility or repair DDL**: Do not make target DDL conditional on legacy objects, silently accept an unexpected target schema, repair drift, or add dual-schema bridges. A non-empty or invalid target database fails the owning migration gate.
- **No startup DDL**: Application startup never calls `create_all`, applies Alembic, repairs data, or creates missing objects. Deployment applies migrations explicitly before readiness.
- **Rollback Symmetry**: Every `upgrade()` migration MUST have a corresponding, functional `downgrade()` implementation for rollback capability.
- **No Unindexed Large Table Locks**: Avoid adding unindexed foreign keys or columns blocking concurrent runtime queries on large product tables.

Before baseline generation, S0-S3 are schema-registration test waves, not Alembic lineages:

| Wave | Owners |
| --- | --- |
| S0 | `identity_tenant` |
| S1 | `agent`, `credential`, `model`, `audit`, `run`, `permission`, `context` |
| S2 | `workspace`, `tool`, `capability_market`, `session`, `a2a`, `group`, `trigger`, `heartbeat`, `channel` |
| S3 | `auth`, `sso`, `organization`, `invitation`, `onboarding`, `okr`, `focus`, `notification`, `published_page`, `plaza`, `enterprise_settings`, `platform_administration`, `agentbay`, `directory`, `agent_template`, `observability`, `tenant_knowledge` |

Each wave first requires every represented owner to be `contract_approved` in `rewrite/owner-contracts.json`. Its real PostgreSQL gate imports the complete registered metadata, creates and drops all tables, constraints, and indexes, rejects unresolved foreign keys and duplicate table ownership, and exercises the wave's positive and negative constraints. Do not generate the initial Alembic baseline until all waves pass, every `rewrite/coverage.json` row is terminal, and every required S3 decision is complete in `rewrite/product-contracts.json` and linked to its approved owner row.

---

## 4. Pre-Merge Checklist

- [ ] `uv run alembic heads` prints **exactly one** revision.
- [ ] `down_revision` equals the head that existed *before* this change.
- [ ] `upgrade()` and `downgrade()` are DDL-only (no inline `SELECT`→`UPDATE`/`INSERT` data loops).
- [ ] `alembic/env.py` uses the one application metadata registry; no migration-only registry or partial model graph exists.
- [ ] The migration contains no legacy detection, schema repair, compatibility path, startup DDL, or cross-owner private write.
- [ ] Migration filename follows `v{Major}_{Minor}_{Patch}_f{Feature_Num}_{description}.py` convention (e.g., `v1_0_0_f060_tenant_id_backfill.py`).
- [ ] Revision ID follows `f{Feature_Num}_{description}` convention (e.g., `f060_tenant_id_backfill`, <=32 chars).
- [ ] Tested rollbacks locally: `uv run alembic downgrade -1` followed by `uv run alembic upgrade head`.

---

## 5. Migration & Revision Naming Standard (Bisheng Specification)

To ensure version traceability and strict alphabetical sorting, file names and revision IDs must follow the Bisheng convention:

### 5.1 File Naming Format
```text
v{Major}_{Minor}_{Patch}_f{Feature_Num}_{description}.py
```
- **Version Prefix (`v1_0_0`)**: Indicates the product release milestone. Keeps migrations sorted chronologically.
- **Feature Number (`f060`)**: Sequential feature/PR ID (3-digit minimum) preventing git branch merge collisions.
- **Brief Description**: Concise snake_case description of the change.

### 5.2 Revision ID Format
Use meaningful, feature-bound revision IDs instead of random hashes:
```python
revision: str = "f060_add_tenant_id_missing_tables"
down_revision: str | None = "allow_checkpoint_deliveries"
```

### 5.3 Structured Docstrings
Include `Background`, `Scope`, and `Idempotent` sections in every migration docstring to document technical intent and rollback safety.
