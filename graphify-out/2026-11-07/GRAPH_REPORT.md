# Graph Report - ketabkharsho-argon  (2026-11-07)

## Corpus Check
- 16 files · ~85,603 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 711 nodes · 3154 edges · 20 communities (13 shown, 7 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 393 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `afcbf947`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- League
- main
- services.py
- .today_str
- run_db
- database.py
- safe_send
- run_all_tests
- AdminFlowInterruptMiddleware
- set_system_state
- deploy.sh
- ReportService
- MockBot
- send_weekly_reports
- run_tests.py
- admin_handlers.py
- handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 158 edges
2. `League` - 97 edges
3. `User` - 96 edges
4. `escape_md()` - 87 edges
5. `run_all_tests()` - 84 edges
6. `DateService` - 81 edges
7. `is_user_admin()` - 70 edges
8. `safe_send_message()` - 56 edges
9. `MessageService` - 49 edges
10. `safe_reply()` - 47 edges

## Surprising Connections (you probably didn't know these)
- `🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب)` --references--> `main()`  [INFERRED]
  docker/README.md → main.py
- `run_all_tests()` --uses--> `AdminStates`  [INFERRED]
  run_tests.py → admin_handlers.py
- `_get_user_past_days()` --uses--> `League`  [INFERRED]
  admin_handlers.py → models.py
- `_get_user_past_days()` --uses--> `User`  [INFERRED]
  admin_handlers.py → models.py
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (20 total, 7 thin omitted)

### Community 0 - "League"
Cohesion: 0.05
Nodes (88): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+80 more)

### Community 1 - "main"
Cohesion: 0.12
Nodes (6): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), BaleAiohttpSession, main()

### Community 2 - "services.py"
Cohesion: 0.12
Nodes (8): _build_global_stats_text_sync(), ActivityLog, Cycle, CycleResult, generate_league_id(), GroupMessage, GroupTerm, SystemState

### Community 3 - ".today_str"
Cohesion: 0.16
Nodes (8): cmd_test_all_jobs(), midnight_job(), send_daily_admin_reports(), send_daily_user_reports(), send_study_reminders(), run_startup_catchups(), _run_safe_job(), setup_scheduler()

### Community 6 - "database.py"
Cohesion: 0.10
Nodes (10): backup_database(), _backup_postgres(), _ensure_indexes(), init_db(), _run_migrations(), _run_postgres_fine_migrations(), set_sqlite_pragma(), _sync_postgres_sequences() (+2 more)

### Community 7 - "safe_send"
Cohesion: 0.16
Nodes (9): BroadcastThrottle, _build_league_morning_cards_sync(), _dispatch_cycle_rollover(), dispatch_outbox(), _rollover_league_cycle_sync(), safe_send(), _send_daily_user_reports_impl(), send_startup_notification() (+1 more)

### Community 8 - "run_all_tests"
Cohesion: 0.05
Nodes (44): cmd_add_league(), cmd_create_group(), cmd_datetest(), cmd_export_system_logs(), cmd_global_stats(), cmd_test_archive(), cmd_test_daily_user_report(), cmd_test_reminder() (+36 more)

### Community 10 - "set_system_state"
Cohesion: 0.24
Nodes (7): get_system_state(), set_system_state(), _build_study_reminders_outbox_sync(), _base(), _init_daily_admin_reports_sync(), _init_morning_reports_sync(), _read_startup_states_and_cleanup_sync()

### Community 13 - "MockBot"
Cohesion: 0.15
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "send_weekly_reports"
Cohesion: 0.33
Nodes (4): cmd_export_cycle_history_excel(), safe_send_document(), send_weekly_reports(), _deliver()

### Community 17 - "run_tests.py"
Cohesion: 0.12
Nodes (3): AdminStates, StudyStates, make_fsm()

### Community 18 - "admin_handlers.py"
Cohesion: 0.07
Nodes (103): _build_admin_help_text(), _cancel_flow(), cb_admin_cancel(), cb_broadcast_confirm_send(), cb_broadcast_pick_group(), cb_broadcast_pick_league(), cb_broadcast_target_all(), cb_broadcast_target_group() (+95 more)

### Community 21 - "handlers.py"
Cohesion: 0.05
Nodes (53): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), _build_morning_cards(), _terms(), build_user_main_menu(), cb_confirm_cancel_league() (+45 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 227 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `League`, `services.py`, `.today_str`, `run_db`, `main.py`, `database.py`, `safe_send`, `run_all_tests`, `set_system_state`, `ReportService`, `send_weekly_reports`, `run_tests.py`, `handlers.py`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Are the 82 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 82 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `League` be split into smaller, more focused modules?**
  _Cohesion score 0.05212903225806451 - nodes in this community are weakly interconnected._
- **Why does `User` connect `handlers.py` to `League`, `services.py`, `main.py`, `database.py`, `run_all_tests`, `set_system_state`, `ReportService`, `run_tests.py`, `admin_handlers.py`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 68 inferred relationships involving `User` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`User` has 68 INFERRED edges - model-reasoned connections that need verification._
- **Should `main` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._