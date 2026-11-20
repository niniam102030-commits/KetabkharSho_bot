# Graph Report - ربات کتابخوارشو  (2026-11-20)

## Corpus Check
- 16 files · ~89,917 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 743 nodes · 3305 edges · 23 communities (18 shown, 5 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 405 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4d6de963`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- main.py
- fine_service.py
- process_user_new_no_study
- League
- run_tests.py
- database.py
- run_all_tests
- safe_send
- AdminFlowInterruptMiddleware
- User
- deploy.sh
- ReportService
- MockBot
- get_or_create_active_cycle
- send_startup_notification
- services.py
- _build_morning_cards
- admin_handlers.py
- BaleAiohttpSession
- run_db
- handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 159 edges
2. `League` - 102 edges
3. `run_all_tests()` - 96 edges
4. `User` - 93 edges
5. `escape_md()` - 87 edges
6. `DateService` - 86 edges
7. `is_user_admin()` - 73 edges
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
- `_get_user_past_days()` --uses--> `DateService`  [INFERRED]
  admin_handlers.py → services.py

## Import Cycles
- None detected.

## Communities (23 total, 5 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (74): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+66 more)

### Community 1 - "main.py"
Cohesion: 0.12
Nodes (8): cmd_test_all_jobs(), midnight_job(), send_daily_user_reports(), _read_startup_states_and_cleanup_sync(), run_startup_catchups(), _run_safe_job(), setup_scheduler(), send_weekly_reports()

### Community 2 - "fine_service.py"
Cohesion: 0.11
Nodes (20): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance() (+12 more)

### Community 3 - "process_user_new_no_study"
Cohesion: 0.27
Nodes (4): _get_user_past_days(), process_user_new_late(), process_user_new_no_study(), _sync_league_fines_impl()

### Community 4 - "League"
Cohesion: 0.16
Nodes (7): _build_global_stats_text_sync(), process_user_new_streak(), sync_all_enabled_leagues(), _midnight_job_sync(), Cycle, League, AbsenceService

### Community 5 - "run_tests.py"
Cohesion: 0.12
Nodes (3): AdminStates, StudyStates, make_fsm()

### Community 6 - "database.py"
Cohesion: 0.11
Nodes (8): backup_database(), _backup_postgres(), _ensure_indexes(), init_db(), _run_migrations(), _run_postgres_fine_migrations(), set_sqlite_pragma(), _sync_postgres_sequences()

### Community 7 - "run_all_tests"
Cohesion: 0.10
Nodes (9): cmd_datetest(), cmd_export_system_logs(), cmd_global_stats(), _prepare_log_snapshot_sync(), process_al_league_floor(), process_league_new_cycle(), user_can_log_late(), run_all_tests() (+1 more)

### Community 8 - "safe_send"
Cohesion: 0.16
Nodes (10): BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox(), safe_send(), safe_send_document(), send_daily_admin_reports(), _send_daily_user_reports_impl(), send_study_reminders() (+2 more)

### Community 10 - "User"
Cohesion: 0.13
Nodes (5): sync_league_fines(), _complete_and_rollover_cycle(), process_study_pages(), User, ScoringService

### Community 12 - "ReportService"
Cohesion: 0.16
Nodes (3): _build_cycle_history_excel_sync(), _collect_league_export_sync(), ReportService

### Community 13 - "MockBot"
Cohesion: 0.15
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "get_or_create_active_cycle"
Cohesion: 0.13
Nodes (7): process_league_new_date(), get_or_create_active_cycle(), _build_single_admin_report_sync(), _check_league_morning_mode_sync(), _fetch_user_profile_sync(), format_league_leaderboard(), _build_weekly_task_sync()

### Community 15 - "send_startup_notification"
Cohesion: 0.15
Nodes (8): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), send_startup_notification(), main(), on_startup(), SystemService

### Community 16 - "services.py"
Cohesion: 0.11
Nodes (6): CycleResult, generate_league_id(), GroupAdmin, GroupMessage, GroupTerm, SystemState

### Community 17 - "_build_morning_cards"
Cohesion: 0.22
Nodes (5): _build_league_morning_cards_sync(), _build_morning_cards(), reset_league_members_for_new_start(), _rollover_league_cycle_sync(), ActivityLog

### Community 18 - "admin_handlers.py"
Cohesion: 0.06
Nodes (129): _build_admin_help_text(), _cancel_flow(), cb_admin_cancel(), cb_broadcast_confirm_send(), cb_broadcast_pick_group(), cb_broadcast_pick_league(), cb_broadcast_target_all(), cb_broadcast_target_group() (+121 more)

### Community 21 - "handlers.py"
Cohesion: 0.06
Nodes (52): generate_new_profile_id(), get_active_user(), get_system_state(), get_user_profiles(), set_active_user_id(), set_system_state(), _build_study_reminders_outbox_sync(), _base() (+44 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 243 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `main.py`, `process_user_new_no_study`, `League`, `run_tests.py`, `database.py`, `run_all_tests`, `User`, `ReportService`, `get_or_create_active_cycle`, `services.py`, `_build_morning_cards`, `run_db`, `handlers.py`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 86 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 86 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0706140350877193 - nodes in this community are weakly interconnected._
- **Why does `League` connect `League` to `fine_handlers.py`, `main.py`, `fine_service.py`, `process_user_new_no_study`, `run_tests.py`, `database.py`, `run_all_tests`, `User`, `ReportService`, `get_or_create_active_cycle`, `services.py`, `_build_morning_cards`, `admin_handlers.py`, `handlers.py`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1164021164021164 - nodes in this community are weakly interconnected._