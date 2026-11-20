# Graph Report - ربات کتابخوارشو  (2026-11-20)

## Corpus Check
- 16 files · ~104,959 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 803 nodes · 3564 edges · 32 communities (23 shown, 9 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 435 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f1209706`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- .league_has_started
- fine_service.py
- _complete_and_rollover_cycle
- AbsenceService
- AdminStates
- database.py
- run_tests.py
- handlers.py
- AdminFlowInterruptMiddleware
- _nav_kb
- deploy.sh
- User
- MockBot
- main.py
- League
- _menu_screen
- DateService
- admin_handlers.py
- send_startup_notification
- run_all_tests
- MessageService
- set_system_state
- format_toman
- BaleAiohttpSession
- راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker)
- _view_fines_sync
- handle_admin_database_upload
- StudyStates
- make_fsm
- FineStates
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 166 edges
2. `run_all_tests()` - 115 edges
3. `League` - 104 edges
4. `User` - 97 edges
5. `escape_md()` - 91 edges
6. `DateService` - 88 edges
7. `is_user_admin()` - 73 edges
8. `safe_send_message()` - 64 edges
9. `safe_reply()` - 52 edges
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
- `_format_user_admin_card()` --uses--> `League`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (32 total, 9 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.22
Nodes (27): _announce_new_manager(), cb_amount_ask(), cb_custom_amount_ask(), cb_debtor_detail(), cb_debtors_list(), cb_fine_admin_menu(), cb_fine_cancel_input(), cb_managed_leagues_list() (+19 more)

### Community 1 - ".league_has_started"
Cohesion: 0.17
Nodes (4): process_league_new_date(), _build_single_admin_report_sync(), _fetch_user_profile_sync(), format_league_leaderboard()

### Community 2 - "fine_service.py"
Cohesion: 0.11
Nodes (21): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance(), get_user_fine_records() (+13 more)

### Community 3 - "_complete_and_rollover_cycle"
Cohesion: 0.15
Nodes (4): _build_cycle_history_excel_sync(), _collect_league_export_sync(), _complete_and_rollover_cycle(), ReportService

### Community 4 - "AbsenceService"
Cohesion: 0.17
Nodes (4): _post_merge_sync(), _sync_league_fines_impl(), _midnight_job_sync(), AbsenceService

### Community 6 - "database.py"
Cohesion: 0.08
Nodes (17): backup_database(), _backup_postgres(), _ensure_indexes(), get_live_sqlite_path(), _get_table_columns_info(), init_db(), _prepare_row_for_destination(), reload_superadmins_from_db() (+9 more)

### Community 7 - "run_tests.py"
Cohesion: 0.11
Nodes (7): demote_super_admin(), CycleResult, generate_league_id(), GroupAdmin, GroupMessage, GroupTerm, SystemState

### Community 8 - "handlers.py"
Cohesion: 0.11
Nodes (18): cmd_test_all_jobs(), BroadcastThrottle, _build_study_reminders_outbox_sync(), _dispatch_cycle_rollover(), dispatch_outbox(), _format_file_size(), _get_database_stats_sync(), _init_daily_admin_reports_sync() (+10 more)

### Community 10 - "_nav_kb"
Cohesion: 0.14
Nodes (21): _btn(), _work(), _work(), _work(), _work(), _work(), _work(), _work() (+13 more)

### Community 12 - "User"
Cohesion: 0.16
Nodes (4): process_study_pages(), User, ScoringService, _build_weekly_task_sync()

### Community 13 - "MockBot"
Cohesion: 0.13
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "main.py"
Cohesion: 0.12
Nodes (6): midnight_job(), _read_startup_states_and_cleanup_sync(), run_startup_catchups(), _run_safe_job(), setup_scheduler(), send_weekly_reports()

### Community 15 - "League"
Cohesion: 0.17
Nodes (9): _build_global_stats_text_sync(), get_all_manager_tg_ids(), _build_league_morning_cards_sync(), _build_morning_cards(), cleanse_prestart_activity_and_scores(), reset_league_members_for_new_start(), user_can_log_late(), ActivityLog (+1 more)

### Community 16 - "_menu_screen"
Cohesion: 0.20
Nodes (14): _auth_menu(), _work(), _work(), _work(), _work(), _work(), _work(), _is_member() (+6 more)

### Community 17 - "DateService"
Cohesion: 0.11
Nodes (7): cmd_datetest(), cmd_export_system_logs(), cmd_global_stats(), _get_user_past_days(), _prepare_log_snapshot_sync(), _check_league_morning_mode_sync(), DateService

### Community 18 - "admin_handlers.py"
Cohesion: 0.05
Nodes (147): _build_admin_help_text(), _cancel_flow(), cb_adm_main_menu(), cb_admin_cancel(), cb_apply_db_cancel(), cb_apply_db_merge(), cb_apply_db_replace(), cb_broadcast_confirm_send() (+139 more)

### Community 19 - "send_startup_notification"
Cohesion: 0.16
Nodes (6): _get_all_admin_recipients_sync(), _get_superadmin_recipients(), send_startup_notification(), main(), on_startup(), SystemService

### Community 20 - "run_all_tests"
Cohesion: 0.21
Nodes (5): process_al_league_floor(), get_or_create_active_cycle(), Cycle, MockDocument, run_all_tests()

### Community 21 - "MessageService"
Cohesion: 0.07
Nodes (45): get_active_user(), get_user_profiles(), set_active_user_id(), _kb(), _base(), _terms(), build_user_main_menu(), cb_confirm_cancel_league() (+37 more)

### Community 22 - "set_system_state"
Cohesion: 0.18
Nodes (7): generate_new_profile_id(), get_system_state(), set_system_state(), _init_morning_reports_sync(), _pwd_is_locked(), _pwd_register_failure(), _state_int()

### Community 23 - "format_toman"
Cohesion: 0.24
Nodes (7): _amounts_line(), _build_fines_text(), _notify_payment(), process_payment_amount(), _work(), format_toman(), parse_amount()

### Community 25 - "راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker)"
Cohesion: 0.40
Nodes (4): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)

### Community 26 - "_view_fines_sync"
Cohesion: 0.40
Nodes (3): _build_refresh_outbox_sync(), _get_league(), _view_fines_sync()

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 259 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `.league_has_started`, `_complete_and_rollover_cycle`, `AbsenceService`, `database.py`, `run_tests.py`, `handlers.py`, `_nav_kb`, `User`, `main.py`, `League`, `_menu_screen`, `DateService`, `run_all_tests`, `MessageService`, `set_system_state`, `format_toman`, `_view_fines_sync`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1073170731707317 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `run_all_tests` to `.league_has_started`, `fine_service.py`, `_complete_and_rollover_cycle`, `AbsenceService`, `AdminStates`, `database.py`, `run_tests.py`, `handlers.py`, `_nav_kb`, `User`, `MockBot`, `main.py`, `League`, `_menu_screen`, `DateService`, `admin_handlers.py`, `send_startup_notification`, `MessageService`, `set_system_state`, `handle_admin_database_upload`, `StudyStates`, `make_fsm`, `Config`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Should `_complete_and_rollover_cycle` be split into smaller, more focused modules?**
  _Cohesion score 0.14624505928853754 - nodes in this community are weakly interconnected._