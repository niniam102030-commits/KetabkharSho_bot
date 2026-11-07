# Graph Report - ketabkharsho-argon  (2026-11-07)

## Corpus Check
- 14 files · ~74,070 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 589 nodes · 2624 edges · 20 communities (12 shown, 8 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 330 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9dbb9c09`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- League
- set_sqlite_pragma
- services.py
- asyncio
- run_db
- database.py
- User
- run_all_tests
- AdminFlowInterruptMiddleware
- DateService
- deploy.sh
- ReportService
- MockBot
- format_league_leaderboard
- _get_admin_profile_lock
- run_tests.py
- admin_handlers.py
- handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 133 edges
2. `run_all_tests()` - 84 edges
3. `User` - 83 edges
4. `DateService` - 79 edges
5. `League` - 78 edges
6. `escape_md()` - 72 edges
7. `is_user_admin()` - 68 edges
8. `safe_send_message()` - 56 edges
9. `MessageService` - 49 edges
10. `safe_reply()` - 47 edges

## Surprising Connections (you probably didn't know these)
- `🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب)` --references--> `main()`  [INFERRED]
  docker/README.md → main.py
- `run_all_tests()` --uses--> `AdminStates`  [INFERRED]
  run_tests.py → admin_handlers.py
- `_get_user_past_days()` --uses--> `User`  [INFERRED]
  admin_handlers.py → models.py
- `_get_user_past_days()` --uses--> `DateService`  [INFERRED]
  admin_handlers.py → services.py
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (20 total, 8 thin omitted)

### Community 0 - "League"
Cohesion: 0.15
Nodes (8): _get_user_past_days(), process_league_new_date(), get_or_create_active_cycle(), _check_league_morning_mode_sync(), _midnight_job_sync(), process_study_pages(), League, AbsenceService

### Community 2 - "services.py"
Cohesion: 0.11
Nodes (8): _build_global_stats_text_sync(), ActivityLog, Cycle, CycleResult, generate_league_id(), GroupMessage, GroupTerm, SystemState

### Community 3 - "asyncio"
Cohesion: 0.06
Nodes (26): cmd_export_cycle_history_excel(), cmd_test_all_jobs(), راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), BroadcastThrottle, _dispatch_cycle_rollover() (+18 more)

### Community 6 - "database.py"
Cohesion: 0.14
Nodes (7): backup_database(), _backup_postgres(), _ensure_indexes(), init_db(), _run_migrations(), _sync_postgres_sequences(), GroupAdmin

### Community 7 - "User"
Cohesion: 0.12
Nodes (8): _build_league_morning_cards_sync(), _build_morning_cards(), _complete_and_rollover_cycle(), _fetch_user_profile_sync(), _rollover_league_cycle_sync(), User, ScoringService, _build_weekly_task_sync()

### Community 8 - "run_all_tests"
Cohesion: 0.11
Nodes (33): cmd_add_league(), cmd_create_group(), cmd_global_stats(), cmd_test_archive(), cmd_test_daily_user_report(), cmd_test_reminder(), cmd_test_startup_notification(), cmd_test_status() (+25 more)

### Community 10 - "DateService"
Cohesion: 0.10
Nodes (4): cmd_datetest(), cmd_export_system_logs(), _prepare_log_snapshot_sync(), DateService

### Community 12 - "ReportService"
Cohesion: 0.18
Nodes (3): _build_cycle_history_excel_sync(), _read_startup_states_and_cleanup_sync(), ReportService

### Community 13 - "MockBot"
Cohesion: 0.15
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "format_league_leaderboard"
Cohesion: 0.29
Nodes (3): _collect_league_export_sync(), _build_single_admin_report_sync(), format_league_leaderboard()

### Community 18 - "admin_handlers.py"
Cohesion: 0.07
Nodes (101): _build_admin_help_text(), _cancel_flow(), cb_admin_cancel(), cb_broadcast_confirm_send(), cb_broadcast_pick_group(), cb_broadcast_pick_league(), cb_broadcast_target_all(), cb_broadcast_target_group() (+93 more)

### Community 21 - "handlers.py"
Cohesion: 0.06
Nodes (51): cb_execute_user_move_league(), generate_new_profile_id(), get_active_user(), get_system_state(), get_user_profiles(), set_active_user_id(), set_system_state(), _build_study_reminders_outbox_sync() (+43 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 204 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DateService` connect `DateService` to `League`, `services.py`, `asyncio`, `main.py`, `database.py`, `User`, `run_all_tests`, `format_league_leaderboard`, `run_tests.py`, `admin_handlers.py`, `handlers.py`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `services.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11396011396011396 - nodes in this community are weakly interconnected._
- **Why does `get_db()` connect `admin_handlers.py` to `League`, `services.py`, `asyncio`, `run_db`, `main.py`, `database.py`, `User`, `run_all_tests`, `DateService`, `ReportService`, `format_league_leaderboard`, `_get_admin_profile_lock`, `run_tests.py`, `handlers.py`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Are the 57 inferred relationships involving `User` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`User` has 57 INFERRED edges - model-reasoned connections that need verification._
- **Should `asyncio` be split into smaller, more focused modules?**
  _Cohesion score 0.060814383923849816 - nodes in this community are weakly interconnected._