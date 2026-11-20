# Graph Report - ربات کتابخوارشو  (2026-11-20)

## Corpus Check
- 16 files · ~95,615 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 777 nodes · 3465 edges · 21 communities (18 shown, 3 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 425 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `386df67a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- DateService
- fine_service.py
- ReportService
- process_study_pages
- run_tests.py
- database.py
- run_all_tests
- BroadcastThrottle
- AdminFlowInterruptMiddleware
- send_startup_notification
- deploy.sh
- User
- MockBot
- main.py
- League
- weekly_report.py
- admin_handlers.py
- scheduler.py
- handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 162 edges
2. `run_all_tests()` - 108 edges
3. `League` - 104 edges
4. `User` - 95 edges
5. `escape_md()` - 91 edges
6. `DateService` - 88 edges
7. `is_user_admin()` - 73 edges
8. `safe_send_message()` - 59 edges
9. `safe_reply()` - 51 edges
10. `MessageService` - 49 edges

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

## Communities (21 total, 3 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (74): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+66 more)

### Community 1 - "DateService"
Cohesion: 0.10
Nodes (9): cmd_datetest(), cmd_global_stats(), process_league_new_date(), _build_single_admin_report_sync(), _check_league_morning_mode_sync(), _fetch_user_profile_sync(), format_league_leaderboard(), user_can_log_late() (+1 more)

### Community 2 - "fine_service.py"
Cohesion: 0.08
Nodes (25): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance() (+17 more)

### Community 3 - "ReportService"
Cohesion: 0.13
Nodes (3): _build_cycle_history_excel_sync(), _collect_league_export_sync(), ReportService

### Community 4 - "process_study_pages"
Cohesion: 0.11
Nodes (12): _get_user_past_days(), process_user_new_late(), process_user_new_no_study(), process_user_new_streak(), get_system_state(), set_system_state(), _init_daily_admin_reports_sync(), _init_morning_reports_sync() (+4 more)

### Community 5 - "run_tests.py"
Cohesion: 0.08
Nodes (4): AdminStates, StudyStates, make_fsm(), MockDocument

### Community 6 - "database.py"
Cohesion: 0.08
Nodes (15): backup_database(), _backup_postgres(), _ensure_indexes(), get_live_sqlite_path(), _get_table_columns_info(), _prepare_row_for_destination(), restore_database_merge(), restore_database_replace() (+7 more)

### Community 7 - "run_all_tests"
Cohesion: 0.17
Nodes (9): process_al_league_floor(), process_league_new_cycle(), get_or_create_active_cycle(), init_db(), cleanse_prestart_activity_and_scores(), reset_league_members_for_new_start(), ActivityLog, Cycle (+1 more)

### Community 8 - "BroadcastThrottle"
Cohesion: 0.17
Nodes (9): cmd_test_all_jobs(), BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox(), send_daily_admin_reports(), send_daily_user_reports(), _send_daily_user_reports_impl(), send_study_reminders() (+1 more)

### Community 10 - "send_startup_notification"
Cohesion: 0.15
Nodes (8): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), send_startup_notification(), main(), on_startup(), SystemService

### Community 12 - "User"
Cohesion: 0.14
Nodes (5): _build_global_stats_text_sync(), _complete_and_rollover_cycle(), User, ScoringService, _build_weekly_task_sync()

### Community 13 - "MockBot"
Cohesion: 0.13
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "main.py"
Cohesion: 0.10
Nodes (5): handle_admin_database_upload(), _format_file_size(), BaleAiohttpSession, _read_startup_states_and_cleanup_sync(), run_startup_catchups()

### Community 15 - "League"
Cohesion: 0.17
Nodes (9): sync_all_enabled_leagues(), sync_league_fines(), _sync_league_fines_impl(), _build_league_morning_cards_sync(), _build_morning_cards(), _build_study_reminders_outbox_sync(), _get_database_stats_sync(), _rollover_league_cycle_sync() (+1 more)

### Community 17 - "weekly_report.py"
Cohesion: 0.20
Nodes (7): cmd_export_system_logs(), _prepare_log_snapshot_sync(), safe_send(), safe_send_document(), send_database_backup(), send_weekly_reports(), _deliver()

### Community 18 - "admin_handlers.py"
Cohesion: 0.06
Nodes (136): _build_admin_help_text(), _cancel_flow(), cb_admin_cancel(), cb_apply_db_cancel(), cb_apply_db_merge(), cb_apply_db_replace(), cb_broadcast_confirm_send(), cb_broadcast_pick_group() (+128 more)

### Community 20 - "scheduler.py"
Cohesion: 0.21
Nodes (3): midnight_job(), _run_safe_job(), setup_scheduler()

### Community 21 - "handlers.py"
Cohesion: 0.07
Nodes (47): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), _base(), _terms(), build_user_main_menu(), cb_confirm_cancel_league() (+39 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 251 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `DateService`, `ReportService`, `process_study_pages`, `run_tests.py`, `database.py`, `run_all_tests`, `BroadcastThrottle`, `User`, `main.py`, `League`, `weekly_report.py`, `handlers.py`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0706140350877193 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `run_all_tests` to `fine_handlers.py`, `DateService`, `fine_service.py`, `ReportService`, `process_study_pages`, `run_tests.py`, `database.py`, `BroadcastThrottle`, `Config`, `send_startup_notification`, `User`, `MockBot`, `main.py`, `League`, `weekly_report.py`, `admin_handlers.py`, `scheduler.py`, `handlers.py`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Should `DateService` be split into smaller, more focused modules?**
  _Cohesion score 0.10042283298097252 - nodes in this community are weakly interconnected._