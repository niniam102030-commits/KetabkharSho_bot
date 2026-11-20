# Graph Report - ربات کتابخوارشو  (2026-11-20)

## Corpus Check
- 16 files · ~95,228 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 774 nodes · 3450 edges · 24 communities (15 shown, 9 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 423 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7c0fa44b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- cleanse_prestart_activity_and_scores
- fine_service.py
- User
- AbsenceService
- run_tests.py
- database.py
- DateService
- safe_send
- AdminFlowInterruptMiddleware
- send_startup_notification
- deploy.sh
- _get_em_terms_keyboard
- MockBot
- main.py
- services.py
- BaleAiohttpSession
- send_weekly_reports
- admin_handlers.py
- AdminStates
- setup_scheduler
- handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 161 edges
2. `run_all_tests()` - 106 edges
3. `League` - 104 edges
4. `User` - 95 edges
5. `escape_md()` - 91 edges
6. `DateService` - 88 edges
7. `is_user_admin()` - 73 edges
8. `safe_send_message()` - 59 edges
9. `safe_reply()` - 50 edges
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

## Communities (24 total, 9 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (74): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+66 more)

### Community 1 - "cleanse_prestart_activity_and_scores"
Cohesion: 0.13
Nodes (3): process_league_new_date(), cleanse_prestart_activity_and_scores(), ActivityLog

### Community 2 - "fine_service.py"
Cohesion: 0.06
Nodes (30): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance() (+22 more)

### Community 3 - "User"
Cohesion: 0.08
Nodes (7): _build_cycle_history_excel_sync(), _collect_league_export_sync(), _complete_and_rollover_cycle(), User, ReportService, ScoringService, _build_weekly_task_sync()

### Community 4 - "AbsenceService"
Cohesion: 0.14
Nodes (14): _format_user_admin_card(), _get_user_manage_keyboard(), _get_user_past_days(), process_league_new_cycle(), process_league_new_floor(), process_user_new_floor(), process_user_new_late(), process_user_new_minutes() (+6 more)

### Community 5 - "run_tests.py"
Cohesion: 0.13
Nodes (21): cmd_add_league(), cmd_create_group(), cmd_export_database(), cmd_global_stats(), cmd_restore_help(), cmd_test_startup_notification(), handle_admin_database_upload(), process_al_league_name() (+13 more)

### Community 6 - "database.py"
Cohesion: 0.08
Nodes (15): backup_database(), _backup_postgres(), _ensure_indexes(), get_live_sqlite_path(), _get_table_columns_info(), _prepare_row_for_destination(), restore_database_merge(), restore_database_replace() (+7 more)

### Community 7 - "DateService"
Cohesion: 0.16
Nodes (6): cmd_datetest(), cmd_export_system_logs(), _prepare_log_snapshot_sync(), process_al_league_floor(), init_db(), DateService

### Community 8 - "safe_send"
Cohesion: 0.16
Nodes (8): BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox(), safe_send(), send_daily_admin_reports(), _send_daily_user_reports_impl(), send_study_reminders(), send_text_chunks()

### Community 10 - "send_startup_notification"
Cohesion: 0.12
Nodes (10): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), _get_all_admin_recipients_sync(), _get_superadmin_recipients(), send_startup_notification(), main() (+2 more)

### Community 13 - "MockBot"
Cohesion: 0.13
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "main.py"
Cohesion: 0.21
Nodes (5): cmd_test_all_jobs(), midnight_job(), send_daily_user_reports(), _read_startup_states_and_cleanup_sync(), run_startup_catchups()

### Community 17 - "send_weekly_reports"
Cohesion: 0.32
Nodes (4): safe_send_document(), send_database_backup(), send_weekly_reports(), _deliver()

### Community 18 - "admin_handlers.py"
Cohesion: 0.07
Nodes (109): _build_admin_help_text(), _build_global_stats_text_sync(), _cancel_flow(), cb_admin_cancel(), cb_apply_db_cancel(), cb_apply_db_merge(), cb_apply_db_replace(), cb_broadcast_confirm_send() (+101 more)

### Community 21 - "handlers.py"
Cohesion: 0.06
Nodes (65): cb_execute_user_move_league(), _execute_user_add_second_league_impl(), generate_new_profile_id(), get_active_user(), get_or_create_active_cycle(), get_system_state(), get_user_profiles(), set_active_user_id() (+57 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 250 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `cleanse_prestart_activity_and_scores`, `User`, `AbsenceService`, `run_tests.py`, `database.py`, `DateService`, `main.py`, `services.py`, `send_weekly_reports`, `handlers.py`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06937285223367698 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `run_tests.py` to `fine_handlers.py`, `cleanse_prestart_activity_and_scores`, `fine_service.py`, `User`, `AbsenceService`, `database.py`, `DateService`, `safe_send`, `Config`, `send_startup_notification`, `_get_em_terms_keyboard`, `MockBot`, `main.py`, `send_weekly_reports`, `admin_handlers.py`, `AdminStates`, `handlers.py`, `.yesterday_date`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Should `cleanse_prestart_activity_and_scores` be split into smaller, more focused modules?**
  _Cohesion score 0.13043478260869565 - nodes in this community are weakly interconnected._