# Graph Report - ربات کتابخوارشو  (2026-11-21)

## Corpus Check
- 16 files · ~112,360 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .example 1, .bat 1)

## Summary
- 813 nodes · 3660 edges · 32 communities (19 shown, 13 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 445 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dc2d7b3c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- run_all_tests
- fine_service.py
- ReportService
- run_tests.py
- keyboards.py
- database.py
- League
- safe_send
- AdminFlowInterruptMiddleware
- .get_terms
- deploy.sh
- User
- MockBot
- main.py
- services.py
- _get_user_lock
- _prepare_log_snapshot_sync
- Session
- send_startup_notification
- send_database_backup
- handlers.py
- handle_admin_database_upload
- راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker)
- BaleAiohttpSession
- AdminStates
- set_sqlite_pragma
- StudyStates
- admin_handlers.py
- make_fsm
- _send_weekly_reports_impl
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 161 edges
2. `run_all_tests()` - 123 edges
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

## Communities (32 total, 13 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (74): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+66 more)

### Community 1 - "run_all_tests"
Cohesion: 0.09
Nodes (15): cb_execute_user_move_league(), _collect_league_export_sync(), _execute_user_add_second_league_impl(), _get_user_past_days(), process_league_new_date(), get_or_create_active_cycle(), _sync_league_fines_impl(), _build_single_admin_report_sync() (+7 more)

### Community 2 - "fine_service.py"
Cohesion: 0.10
Nodes (22): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance() (+14 more)

### Community 4 - "run_tests.py"
Cohesion: 0.12
Nodes (7): demote_super_admin(), CycleResult, generate_league_id(), GroupAdmin, GroupMessage, GroupTerm, MockDocument

### Community 5 - "keyboards.py"
Cohesion: 0.15
Nodes (6): get_cancel_league_confirm(), get_confirm_revoke_sa_keyboard(), get_main_menu(), get_study_edit_menu(), get_superadmin_alert_keyboard(), get_superadmins_list_keyboard()

### Community 6 - "database.py"
Cohesion: 0.07
Nodes (17): _post_merge_sync(), backup_database(), _backup_postgres(), _ensure_indexes(), get_live_sqlite_path(), _get_table_columns_info(), init_db(), _prepare_row_for_destination() (+9 more)

### Community 7 - "League"
Cohesion: 0.20
Nodes (10): _build_global_stats_text_sync(), _build_league_morning_cards_sync(), _build_morning_cards(), _build_study_reminders_outbox_sync(), _base(), _fetch_user_profile_sync(), _get_database_stats_sync(), ActivityLog (+2 more)

### Community 8 - "safe_send"
Cohesion: 0.22
Nodes (6): BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox(), safe_send(), _send_daily_user_reports_impl(), send_text_chunks()

### Community 12 - "User"
Cohesion: 0.09
Nodes (9): set_system_state(), _complete_and_rollover_cycle(), format_league_leaderboard(), _midnight_job_sync(), process_study_pages(), User, AbsenceService, ScoringService (+1 more)

### Community 13 - "MockBot"
Cohesion: 0.13
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "main.py"
Cohesion: 0.11
Nodes (11): cmd_test_all_jobs(), _init_daily_admin_reports_sync(), midnight_job(), send_daily_admin_reports(), send_daily_user_reports(), send_study_reminders(), _read_startup_states_and_cleanup_sync(), run_startup_catchups() (+3 more)

### Community 15 - "services.py"
Cohesion: 0.20
Nodes (3): get_system_state(), _init_morning_reports_sync(), SystemState

### Community 18 - "Session"
Cohesion: 0.47
Nodes (3): _pwd_is_locked(), _pwd_register_failure(), _state_int()

### Community 19 - "send_startup_notification"
Cohesion: 0.18
Nodes (5): _get_all_admin_recipients_sync(), _get_superadmin_recipients(), send_startup_notification(), main(), on_startup()

### Community 21 - "handlers.py"
Cohesion: 0.14
Nodes (36): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), build_user_main_menu(), cb_confirm_cancel_league(), cb_join_league(), _cb_join_league_impl() (+28 more)

### Community 22 - "handle_admin_database_upload"
Cohesion: 0.50
Nodes (3): _cleanup_expired_db_uploads(), handle_admin_database_upload(), _format_file_size()

### Community 23 - "راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker)"
Cohesion: 0.40
Nodes (4): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)

### Community 28 - "admin_handlers.py"
Cohesion: 0.05
Nodes (150): _build_admin_help_text(), _cancel_flow(), cb_adm_main_menu(), cb_admin_cancel(), cb_apply_db_cancel(), cb_apply_db_merge(), cb_apply_db_replace(), cb_broadcast_confirm_send() (+142 more)

### Community 34 - "_send_weekly_reports_impl"
Cohesion: 0.40
Nodes (3): safe_send_document(), _send_weekly_reports_impl(), _deliver()

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 263 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `run_all_tests`, `_send_weekly_reports_impl`, `ReportService`, `run_tests.py`, `database.py`, `League`, `User`, `main.py`, `services.py`, `_get_user_lock`, `_prepare_log_snapshot_sync`, `handlers.py`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06958762886597938 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `run_all_tests` to `fine_handlers.py`, `fine_service.py`, `ReportService`, `run_tests.py`, `database.py`, `League`, `.get_terms`, `User`, `MockBot`, `main.py`, `services.py`, `_prepare_log_snapshot_sync`, `send_startup_notification`, `send_database_backup`, `handlers.py`, `handle_admin_database_upload`, `AdminStates`, `StudyStates`, `admin_handlers.py`, `make_fsm`, `Config`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 91 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 91 INFERRED edges - model-reasoned connections that need verification._
- **Should `run_all_tests` be split into smaller, more focused modules?**
  _Cohesion score 0.09134906231094979 - nodes in this community are weakly interconnected._