# Graph Report - ketabkharsho-argon  (2026-11-07)

## Corpus Check
- 12 files · ~72,232 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .example 1, .bat 1)

## Summary
- 579 nodes · 2599 edges · 16 communities (9 shown, 7 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 327 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c47b7bf4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- _complete_and_rollover_cycle
- handlers.py
- database.py
- asyncio
- run_db
- main.py
- init_db
- .generate_cycle_history_excel
- run_tests.py
- AdminFlowInterruptMiddleware
- User
- set_sqlite_pragma
- BaleAiohttpSession
- admin_handlers.py
- MessageService
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 131 edges
2. `run_all_tests()` - 84 edges
3. `User` - 82 edges
4. `DateService` - 79 edges
5. `League` - 78 edges
6. `escape_md()` - 71 edges
7. `is_user_admin()` - 67 edges
8. `safe_send_message()` - 55 edges
9. `MessageService` - 49 edges
10. `safe_reply()` - 47 edges

## Surprising Connections (you probably didn't know these)
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py
- `_get_em_terms_keyboard()` --uses--> `MessageService`  [INFERRED]
  admin_handlers.py → message_service.py
- `process_cg_password()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py
- `process_cg_password()` --uses--> `DateService`  [INFERRED]
  admin_handlers.py → services.py
- `process_pg_new_password()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (16 total, 7 thin omitted)

### Community 0 - "_complete_and_rollover_cycle"
Cohesion: 0.17
Nodes (6): _build_league_morning_cards_sync(), _build_morning_cards(), _complete_and_rollover_cycle(), _rollover_league_cycle_sync(), ScoringService, _build_weekly_task_sync()

### Community 1 - "handlers.py"
Cohesion: 0.11
Nodes (11): get_system_state(), _get_all_admin_recipients_sync(), _init_daily_admin_reports_sync(), _init_morning_reports_sync(), _pwd_is_locked(), _pwd_register_failure(), _state_int(), get_cancel_league_confirm() (+3 more)

### Community 2 - "database.py"
Cohesion: 0.09
Nodes (10): backup_database(), _backup_postgres(), set_system_state(), ActivityLog, Cycle, CycleResult, generate_league_id(), GroupMessage (+2 more)

### Community 3 - "asyncio"
Cohesion: 0.10
Nodes (17): cmd_test_all_jobs(), BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox(), midnight_job(), safe_send(), safe_send_document(), send_daily_admin_reports() (+9 more)

### Community 6 - "init_db"
Cohesion: 0.18
Nodes (5): _ensure_indexes(), init_db(), _run_migrations(), _sync_postgres_sequences(), main()

### Community 8 - "run_tests.py"
Cohesion: 0.07
Nodes (34): AdminStates, cmd_add_league(), cmd_create_group(), cmd_export_cycle_history_excel(), cmd_global_stats(), cmd_test_archive(), cmd_test_daily_user_report(), cmd_test_reminder() (+26 more)

### Community 10 - "User"
Cohesion: 0.05
Nodes (26): _build_global_stats_text_sync(), cmd_datetest(), cmd_export_system_logs(), _collect_league_export_sync(), _format_user_admin_card(), _get_user_manage_keyboard(), _get_user_past_days(), _prepare_log_snapshot_sync() (+18 more)

### Community 18 - "admin_handlers.py"
Cohesion: 0.07
Nodes (100): _build_admin_help_text(), _cancel_flow(), cb_admin_cancel(), cb_broadcast_confirm_send(), cb_broadcast_pick_group(), cb_broadcast_pick_league(), cb_broadcast_target_all(), cb_broadcast_target_group() (+92 more)

### Community 21 - "MessageService"
Cohesion: 0.08
Nodes (41): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), _build_study_reminders_outbox_sync(), _base(), _terms(), build_user_main_menu() (+33 more)

## Knowledge Gaps
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DateService` connect `User` to `_complete_and_rollover_cycle`, `handlers.py`, `database.py`, `asyncio`, `main.py`, `init_db`, `run_tests.py`, `admin_handlers.py`, `MessageService`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11375661375661375 - nodes in this community are weakly interconnected._
- **Why does `get_db()` connect `admin_handlers.py` to `_complete_and_rollover_cycle`, `handlers.py`, `database.py`, `asyncio`, `run_db`, `main.py`, `init_db`, `.generate_cycle_history_excel`, `run_tests.py`, `User`, `MessageService`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Are the 56 inferred relationships involving `User` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`User` has 56 INFERRED edges - model-reasoned connections that need verification._
- **Should `database.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08717948717948718 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `run_tests.py` to `handlers.py`, `database.py`, `asyncio`, `main.py`, `init_db`, `.generate_cycle_history_excel`, `User`, `Config`, `admin_handlers.py`, `MessageService`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._