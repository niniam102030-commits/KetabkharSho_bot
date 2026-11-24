# Graph Report - ربات کتابخوارشو  (2026-11-23)

## Corpus Check
- 16 files · ~112,928 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .example 1, .bat 1)

## Summary
- 814 nodes · 3684 edges · 26 communities (16 shown, 10 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 448 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c004b3a5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- cleanse_prestart_activity_and_scores
- fine_service.py
- User
- Cycle
- keyboards.py
- database.py
- League
- send_database_backup
- AdminFlowInterruptMiddleware
- MessageService
- deploy.sh
- _midnight_job_sync
- MockBot
- services.py
- AbsenceService
- _cb_join_league_impl
- DateService
- handlers.py
- _get_admin_profile_lock
- _get_user_past_days
- build_user_main_menu
- StudyStates
- admin_handlers.py
- make_fsm
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
- `_get_user_past_days()` --uses--> `League`  [INFERRED]
  admin_handlers.py → models.py
- `_get_user_past_days()` --uses--> `User`  [INFERRED]
  admin_handlers.py → models.py
- `_get_user_past_days()` --uses--> `DateService`  [INFERRED]
  admin_handlers.py → services.py
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (26 total, 10 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (75): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+67 more)

### Community 2 - "fine_service.py"
Cohesion: 0.11
Nodes (21): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance() (+13 more)

### Community 3 - "User"
Cohesion: 0.12
Nodes (4): _collect_league_export_sync(), _read_startup_states_and_cleanup_sync(), User, ReportService

### Community 4 - "Cycle"
Cohesion: 0.20
Nodes (5): demote_super_admin(), Cycle, CycleResult, GroupAdmin, SystemState

### Community 5 - "keyboards.py"
Cohesion: 0.14
Nodes (7): get_cancel_league_confirm(), get_confirm_revoke_sa_keyboard(), get_league_selection(), get_main_menu(), get_profile_switch_keyboard(), get_study_edit_menu(), get_superadmin_alert_keyboard()

### Community 6 - "database.py"
Cohesion: 0.07
Nodes (17): backup_database(), _backup_postgres(), _ensure_indexes(), get_live_sqlite_path(), _get_table_columns_info(), init_db(), _prepare_row_for_destination(), restore_database_merge() (+9 more)

### Community 7 - "League"
Cohesion: 0.12
Nodes (19): cb_execute_user_move_league(), _execute_user_add_second_league_impl(), _split_league_user_payload(), get_or_create_active_cycle(), _build_league_morning_cards_sync(), _build_morning_cards(), _build_single_admin_report_sync(), _check_league_morning_mode_sync() (+11 more)

### Community 8 - "send_database_backup"
Cohesion: 0.05
Nodes (25): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox(), _get_all_admin_recipients_sync() (+17 more)

### Community 10 - "MessageService"
Cohesion: 0.13
Nodes (5): _build_study_reminders_outbox_sync(), _base(), _terms(), start_registration_or_new_group(), MessageService

### Community 13 - "MockBot"
Cohesion: 0.13
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 15 - "AbsenceService"
Cohesion: 0.20
Nodes (12): _format_user_admin_card(), _get_user_manage_keyboard(), _is_ascii_digits(), process_user_new_floor(), process_user_new_late(), process_user_new_minutes(), process_user_new_no_study(), process_user_new_pages() (+4 more)

### Community 16 - "_cb_join_league_impl"
Cohesion: 0.18
Nodes (9): generate_new_profile_id(), _get_or_create_active_cycle_impl(), set_active_user_id(), cb_confirm_cancel_league(), cb_join_league(), _cb_join_league_impl(), cb_join_new_group_prompt(), cb_switch_profile() (+1 more)

### Community 17 - "DateService"
Cohesion: 0.14
Nodes (5): cmd_datetest(), cmd_export_system_logs(), _prepare_log_snapshot_sync(), midnight_job(), DateService

### Community 18 - "handlers.py"
Cohesion: 0.16
Nodes (10): get_system_state(), set_system_state(), _init_daily_admin_reports_sync(), _init_morning_reports_sync(), _pwd_is_locked(), _pwd_register_failure(), reset_league_members_for_new_start(), _send_daily_user_reports_impl() (+2 more)

### Community 21 - "build_user_main_menu"
Cohesion: 0.21
Nodes (24): get_active_user(), get_user_profiles(), build_user_main_menu(), cmd_cancel_my_league(), cmd_start(), cmd_toggle_reminder(), _dispatch_menu_interruption(), handle_append_study_today() (+16 more)

### Community 28 - "admin_handlers.py"
Cohesion: 0.05
Nodes (151): AdminStates, _build_admin_help_text(), _build_cycle_history_excel_sync(), _build_global_stats_text_sync(), _cancel_flow(), cb_adm_main_menu(), cb_admin_cancel(), cb_apply_db_cancel() (+143 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 262 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `cleanse_prestart_activity_and_scores`, `User`, `Cycle`, `database.py`, `League`, `send_database_backup`, `MessageService`, `_midnight_job_sync`, `services.py`, `AbsenceService`, `_cb_join_league_impl`, `DateService`, `handlers.py`, `_get_admin_profile_lock`, `build_user_main_menu`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06782106782106782 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `admin_handlers.py` to `fine_handlers.py`, `cleanse_prestart_activity_and_scores`, `fine_service.py`, `User`, `Cycle`, `database.py`, `League`, `send_database_backup`, `MessageService`, `_midnight_job_sync`, `MockBot`, `services.py`, `AbsenceService`, `_cb_join_league_impl`, `DateService`, `handlers.py`, `build_user_main_menu`, `StudyStates`, `make_fsm`, `Config`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 92 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 92 INFERRED edges - model-reasoned connections that need verification._
- **Should `fine_service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11025641025641025 - nodes in this community are weakly interconnected._