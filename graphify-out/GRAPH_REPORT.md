# Graph Report - ربات کتابخوارشو  (2026-11-23)

## Corpus Check
- 17 files · ~112,937 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .example 1, .bat 1)

## Summary
- 816 nodes · 3685 edges · 22 communities (17 shown, 5 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 448 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9618e0d1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- run_all_tests
- fine_service.py
- ReportService
- League
- send_startup_notification
- database.py
- User
- send_database_backup
- AdminFlowInterruptMiddleware
- BaleAiohttpSession
- deploy.sh
- AbsenceService
- MockBot
- services.py
- entrypoint.sh
- get_or_create_active_cycle
- midnight_job
- handlers.py
- run_tests.py
- admin_handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 167 edges
2. `run_all_tests()` - 124 edges
3. `League` - 108 edges
4. `User` - 98 edges
5. `escape_md()` - 93 edges
6. `DateService` - 90 edges
7. `is_user_admin()` - 87 edges
8. `safe_send_message()` - 64 edges
9. `safe_reply()` - 52 edges
10. `MessageService` - 50 edges

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

## Communities (22 total, 5 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (74): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+66 more)

### Community 1 - "run_all_tests"
Cohesion: 0.11
Nodes (8): _matches_superadmin_root_id(), process_al_league_floor(), process_league_new_date(), cleanse_prestart_activity_and_scores(), reset_league_members_for_new_start(), ActivityLog, run_all_tests(), DateService

### Community 2 - "fine_service.py"
Cohesion: 0.09
Nodes (24): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance() (+16 more)

### Community 3 - "ReportService"
Cohesion: 0.15
Nodes (4): _build_cycle_history_excel_sync(), _collect_league_export_sync(), CycleResult, ReportService

### Community 4 - "League"
Cohesion: 0.18
Nodes (8): _build_global_stats_text_sync(), _get_or_create_active_cycle_impl(), _build_league_morning_cards_sync(), _build_morning_cards(), _get_database_stats_sync(), _rollover_league_cycle_sync(), Cycle, League

### Community 5 - "send_startup_notification"
Cohesion: 0.15
Nodes (8): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), send_startup_notification(), main(), on_startup(), SystemService

### Community 6 - "database.py"
Cohesion: 0.05
Nodes (25): _cleanup_expired_db_uploads(), handle_admin_database_upload(), backup_database(), _backup_postgres(), demote_super_admin(), _ensure_indexes(), get_live_sqlite_path(), _get_table_columns_info() (+17 more)

### Community 7 - "User"
Cohesion: 0.14
Nodes (5): _complete_and_rollover_cycle(), process_study_pages(), User, ScoringService, _build_weekly_task_sync()

### Community 8 - "send_database_backup"
Cohesion: 0.14
Nodes (12): BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox(), safe_send(), safe_send_document(), send_daily_admin_reports(), _send_daily_user_reports_impl(), send_database_backup() (+4 more)

### Community 12 - "AbsenceService"
Cohesion: 0.16
Nodes (3): _post_merge_sync(), _midnight_job_sync(), AbsenceService

### Community 13 - "MockBot"
Cohesion: 0.13
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "services.py"
Cohesion: 0.13
Nodes (3): get_system_state(), _init_daily_admin_reports_sync(), _read_startup_states_and_cleanup_sync()

### Community 16 - "get_or_create_active_cycle"
Cohesion: 0.12
Nodes (15): cb_execute_user_add_second_league(), cb_execute_user_move_league(), _execute_user_add_second_league_impl(), _get_admin_profile_lock(), _split_league_user_payload(), generate_new_profile_id(), get_or_create_active_cycle(), set_active_user_id() (+7 more)

### Community 17 - "midnight_job"
Cohesion: 0.17
Nodes (7): cmd_test_all_jobs(), midnight_job(), send_daily_user_reports(), run_startup_catchups(), _run_safe_job(), setup_scheduler(), send_weekly_reports()

### Community 21 - "handlers.py"
Cohesion: 0.07
Nodes (48): get_active_user(), get_user_profiles(), _build_study_reminders_outbox_sync(), _base(), _terms(), build_user_main_menu(), cb_confirm_cancel_league(), cb_join_league() (+40 more)

### Community 27 - "run_tests.py"
Cohesion: 0.11
Nodes (4): AdminStates, StudyStates, make_fsm(), MockDocument

### Community 28 - "admin_handlers.py"
Cohesion: 0.05
Nodes (151): _build_admin_help_text(), _cancel_flow(), cb_adm_main_menu(), cb_admin_cancel(), cb_apply_db_cancel(), cb_apply_db_merge(), cb_apply_db_replace(), cb_broadcast_confirm_send() (+143 more)

## Knowledge Gaps
- **4 isolated node(s):** `deploy.sh script`, `entrypoint.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 264 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `run_all_tests`, `ReportService`, `League`, `database.py`, `User`, `send_database_backup`, `AbsenceService`, `services.py`, `get_or_create_active_cycle`, `handlers.py`, `run_tests.py`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `entrypoint.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07105263157894737 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `run_all_tests` to `fine_handlers.py`, `fine_service.py`, `ReportService`, `League`, `send_startup_notification`, `database.py`, `User`, `send_database_backup`, `Config`, `AbsenceService`, `MockBot`, `services.py`, `get_or_create_active_cycle`, `midnight_job`, `handlers.py`, `run_tests.py`, `admin_handlers.py`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 92 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 92 INFERRED edges - model-reasoned connections that need verification._
- **Should `run_all_tests` be split into smaller, more focused modules?**
  _Cohesion score 0.10853658536585366 - nodes in this community are weakly interconnected._