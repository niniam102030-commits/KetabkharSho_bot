# Graph Report - ربات کتابخوارشو  (2026-11-21)

## Corpus Check
- 16 files · ~110,383 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 810 nodes · 3645 edges · 21 communities (14 shown, 7 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 444 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c1270497`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- run_all_tests
- fine_service.py
- _complete_and_rollover_cycle
- AbsenceService
- database.py
- League
- send_database_backup
- AdminFlowInterruptMiddleware
- deploy.sh
- User
- run_tests.py
- os
- send_startup_notification
- cleanse_prestart_activity_and_scores
- handlers.py
- BaleAiohttpSession
- admin_handlers.py
- .today_str
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 161 edges
2. `run_all_tests()` - 119 edges
3. `League` - 107 edges
4. `User` - 98 edges
5. `escape_md()` - 93 edges
6. `DateService` - 89 edges
7. `is_user_admin()` - 84 edges
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
- `_format_user_admin_card()` --uses--> `League`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (21 total, 7 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (74): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+66 more)

### Community 1 - "run_all_tests"
Cohesion: 0.16
Nodes (16): cb_execute_user_add_second_league(), cb_execute_user_move_league(), _execute_user_add_second_league_impl(), _get_user_past_days(), process_league_new_date(), _split_league_user_payload(), get_or_create_active_cycle(), _build_single_admin_report_sync() (+8 more)

### Community 2 - "fine_service.py"
Cohesion: 0.11
Nodes (20): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance() (+12 more)

### Community 3 - "_complete_and_rollover_cycle"
Cohesion: 0.12
Nodes (4): _build_cycle_history_excel_sync(), _collect_league_export_sync(), _complete_and_rollover_cycle(), ReportService

### Community 4 - "AbsenceService"
Cohesion: 0.16
Nodes (3): _post_merge_sync(), _midnight_job_sync(), AbsenceService

### Community 6 - "database.py"
Cohesion: 0.06
Nodes (21): backup_database(), _backup_postgres(), demote_super_admin(), _ensure_indexes(), get_live_sqlite_path(), _get_table_columns_info(), init_db(), _prepare_row_for_destination() (+13 more)

### Community 7 - "League"
Cohesion: 0.13
Nodes (11): _build_global_stats_text_sync(), sync_all_enabled_leagues(), sync_league_fines(), _sync_league_fines_impl(), _build_league_morning_cards_sync(), _build_morning_cards(), _get_database_stats_sync(), _rollover_league_cycle_sync() (+3 more)

### Community 8 - "send_database_backup"
Cohesion: 0.16
Nodes (11): BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox(), safe_send(), safe_send_document(), _send_daily_user_reports_impl(), send_database_backup(), send_study_reminders() (+3 more)

### Community 12 - "User"
Cohesion: 0.13
Nodes (5): _get_admin_profile_lock(), _fetch_user_profile_sync(), User, ScoringService, _build_weekly_task_sync()

### Community 13 - "run_tests.py"
Cohesion: 0.06
Nodes (12): _cleanup_expired_db_uploads(), handle_admin_database_upload(), _format_file_size(), StudyStates, GroupMessage, make_fsm(), MockBot, MockCallbackQuery (+4 more)

### Community 19 - "send_startup_notification"
Cohesion: 0.15
Nodes (8): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), send_startup_notification(), main(), on_startup(), SystemService

### Community 21 - "handlers.py"
Cohesion: 0.06
Nodes (54): generate_new_profile_id(), get_active_user(), get_system_state(), get_user_profiles(), set_active_user_id(), set_system_state(), _build_study_reminders_outbox_sync(), _base() (+46 more)

### Community 28 - "admin_handlers.py"
Cohesion: 0.05
Nodes (151): AdminStates, _build_admin_help_text(), _cancel_flow(), cb_adm_main_menu(), cb_admin_cancel(), cb_apply_db_cancel(), cb_apply_db_merge(), cb_apply_db_replace() (+143 more)

### Community 34 - ".today_str"
Cohesion: 0.14
Nodes (9): cmd_test_all_jobs(), midnight_job(), send_daily_admin_reports(), send_daily_user_reports(), _read_startup_states_and_cleanup_sync(), run_startup_catchups(), _run_safe_job(), setup_scheduler() (+1 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 260 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `run_all_tests`, `.today_str`, `_complete_and_rollover_cycle`, `AbsenceService`, `database.py`, `League`, `send_database_backup`, `User`, `run_tests.py`, `services.py`, `os`, `handlers.py`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07083333333333333 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `run_all_tests` to `fine_handlers.py`, `.today_str`, `fine_service.py`, `AbsenceService`, `_complete_and_rollover_cycle`, `database.py`, `League`, `send_database_backup`, `Config`, `User`, `run_tests.py`, `os`, `send_startup_notification`, `cleanse_prestart_activity_and_scores`, `handlers.py`, `admin_handlers.py`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Are the 91 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 91 INFERRED edges - model-reasoned connections that need verification._
- **Should `fine_service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11097560975609756 - nodes in this community are weakly interconnected._