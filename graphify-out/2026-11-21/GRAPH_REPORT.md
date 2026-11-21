# Graph Report - ربات کتابخوارشو  (2026-11-21)

## Corpus Check
- 16 files · ~107,670 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 806 nodes · 3569 edges · 38 communities (26 shown, 12 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 438 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `74dbaf68`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- DateService
- League
- User
- get_or_create_active_cycle
- AdminStates
- database.py
- run_tests.py
- send_database_backup
- AdminFlowInterruptMiddleware
- _nav_kb
- deploy.sh
- _build_weekly_task_sync
- MockBot
- main.py
- get_db
- _menu_screen
- .today_shamsi
- FSMContext
- send_startup_notification
- run_all_tests
- handlers.py
- _guard_manager
- run_startup_catchups
- راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker)
- _view_fines_sync
- handle_admin_database_upload
- admin_handlers.py
- _cancel_flow
- FineStates
- cb_em_select_group
- cb_execute_user_move_league
- setup_scheduler
- _send_weekly_reports_impl
- _get_superadmins_metadata
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 161 edges
2. `run_all_tests()` - 115 edges
3. `League` - 107 edges
4. `User` - 97 edges
5. `escape_md()` - 93 edges
6. `DateService` - 88 edges
7. `is_user_admin()` - 68 edges
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
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (38 total, 12 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.23
Nodes (26): _announce_new_manager(), cb_amount_ask(), cb_custom_amount_ask(), cb_debtor_detail(), cb_debtors_list(), cb_fine_admin_menu(), cb_fine_cancel_input(), cb_managed_leagues_list() (+18 more)

### Community 1 - "DateService"
Cohesion: 0.21
Nodes (7): _get_user_past_days(), process_league_new_date(), _build_single_admin_report_sync(), _check_league_morning_mode_sync(), _fetch_user_profile_sync(), format_league_leaderboard(), DateService

### Community 2 - "League"
Cohesion: 0.10
Nodes (25): _roles(), add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids() (+17 more)

### Community 3 - "User"
Cohesion: 0.14
Nodes (3): _build_cycle_history_excel_sync(), _collect_league_export_sync(), User

### Community 4 - "get_or_create_active_cycle"
Cohesion: 0.11
Nodes (15): _post_merge_sync(), get_or_create_active_cycle(), set_system_state(), _build_league_morning_cards_sync(), _build_morning_cards(), _build_study_reminders_outbox_sync(), cleanse_prestart_activity_and_scores(), _complete_and_rollover_cycle() (+7 more)

### Community 6 - "database.py"
Cohesion: 0.08
Nodes (17): backup_database(), _backup_postgres(), _ensure_indexes(), get_live_sqlite_path(), _get_table_columns_info(), init_db(), _prepare_row_for_destination(), reload_superadmins_from_db() (+9 more)

### Community 7 - "run_tests.py"
Cohesion: 0.11
Nodes (7): demote_super_admin(), CycleResult, generate_league_id(), GroupAdmin, GroupMessage, GroupTerm, SystemState

### Community 8 - "send_database_backup"
Cohesion: 0.23
Nodes (6): BroadcastThrottle, _dispatch_cycle_rollover(), safe_send_document(), send_daily_admin_reports(), send_database_backup(), send_text_chunks()

### Community 10 - "_nav_kb"
Cohesion: 0.19
Nodes (15): _amounts_line(), _btn(), _build_fines_text(), _work(), _cycle_numbers(), _debtors_screen(), _detail_screen(), _fines_view_kb() (+7 more)

### Community 13 - "MockBot"
Cohesion: 0.13
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "main.py"
Cohesion: 0.15
Nodes (3): send_study_reminders(), _read_startup_states_and_cleanup_sync(), ReportService

### Community 15 - "get_db"
Cohesion: 0.13
Nodes (34): _build_global_stats_text_sync(), cb_broadcast_pick_group(), cb_broadcast_pick_league(), cb_confirm_delete_league(), cb_confirm_user_delete(), cb_delete_league_prompt(), cb_em_reset_msg(), cb_menu_excel() (+26 more)

### Community 16 - "_menu_screen"
Cohesion: 0.22
Nodes (13): _auth_menu(), _work(), _work(), _work(), _work(), _work(), _work(), _is_member() (+5 more)

### Community 18 - "FSMContext"
Cohesion: 0.13
Nodes (49): cb_adm_main_menu(), cb_admin_cancel(), cb_apply_db_cancel(), cb_apply_db_merge(), cb_apply_db_replace(), cb_broadcast_confirm_send(), cb_broadcast_target_all(), cb_broadcast_target_group() (+41 more)

### Community 19 - "send_startup_notification"
Cohesion: 0.18
Nodes (5): _get_all_admin_recipients_sync(), _get_superadmin_recipients(), send_startup_notification(), main(), on_startup()

### Community 21 - "run_all_tests"
Cohesion: 0.07
Nodes (47): process_em_new_msg(), get_active_user(), get_user_profiles(), set_active_user_id(), _kb(), _base(), _terms(), build_user_main_menu() (+39 more)

### Community 22 - "handlers.py"
Cohesion: 0.09
Nodes (14): generate_new_profile_id(), get_system_state(), dispatch_outbox(), _init_daily_admin_reports_sync(), _init_morning_reports_sync(), _pwd_is_locked(), _pwd_register_failure(), _send_daily_user_reports_impl() (+6 more)

### Community 23 - "_guard_manager"
Cohesion: 0.14
Nodes (14): _work(), _work(), _work(), _work(), _work(), _work(), _work(), _get_ledger_user() (+6 more)

### Community 25 - "راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker)"
Cohesion: 0.40
Nodes (4): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)

### Community 26 - "_view_fines_sync"
Cohesion: 0.40
Nodes (3): _build_refresh_outbox_sync(), _get_league(), _view_fines_sync()

### Community 27 - "handle_admin_database_upload"
Cohesion: 0.50
Nodes (3): _cleanup_expired_db_uploads(), handle_admin_database_upload(), _format_file_size()

### Community 28 - "admin_handlers.py"
Cohesion: 0.09
Nodes (49): cmd_add_group_admin(), cmd_add_league(), cmd_archive_exclude(), cmd_archive_include(), cmd_broadcast(), cmd_create_group(), cmd_datetest(), cmd_edit_or_delete_leagues() (+41 more)

### Community 29 - "_cancel_flow"
Cohesion: 0.12
Nodes (10): _build_admin_help_text(), _cancel_flow(), cb_revoke_sa_prompt(), cmd_claim_superadmin(), global_cancel_message(), show_admin_panel(), get_admin_main_inline_menu(), get_confirm_revoke_sa_keyboard() (+2 more)

### Community 31 - "cb_em_select_group"
Cohesion: 0.17
Nodes (6): cb_em_reset_term(), cb_em_select_group(), _get_em_main_keyboard(), _get_em_msgs_keyboard(), _get_em_terms_keyboard(), _get_league_edit_keyboard()

### Community 33 - "cb_execute_user_move_league"
Cohesion: 0.22
Nodes (6): cb_execute_user_add_second_league(), cb_execute_user_move_league(), cb_user_move_league(), _execute_user_add_second_league_impl(), _get_admin_profile_lock(), _get_profile_league_ids()

### Community 35 - "_send_weekly_reports_impl"
Cohesion: 0.40
Nodes (3): send_weekly_reports(), _send_weekly_reports_impl(), _deliver()

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 259 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `get_db` to `fine_handlers.py`, `DateService`, `User`, `get_or_create_active_cycle`, `database.py`, `run_tests.py`, `_nav_kb`, `_build_weekly_task_sync`, `main.py`, `_menu_screen`, `.today_shamsi`, `FSMContext`, `run_all_tests`, `handlers.py`, `_guard_manager`, `_view_fines_sync`, `admin_handlers.py`, `_cancel_flow`, `cb_em_select_group`, `cb_execute_user_move_league`, `_send_weekly_reports_impl`, `_get_superadmins_metadata`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `League` be split into smaller, more focused modules?**
  _Cohesion score 0.0975177304964539 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `run_all_tests` to `DateService`, `League`, `User`, `get_or_create_active_cycle`, `AdminStates`, `database.py`, `run_tests.py`, `send_database_backup`, `_nav_kb`, `MockBot`, `main.py`, `get_db`, `_menu_screen`, `.today_shamsi`, `FSMContext`, `send_startup_notification`, `.shamsi_to_date`, `handlers.py`, `handle_admin_database_upload`, `admin_handlers.py`, `_cancel_flow`, `._compute_raw_streak_from_logs`, `cb_execute_user_move_league`, `_send_weekly_reports_impl`, `Config`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Are the 91 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 91 INFERRED edges - model-reasoned connections that need verification._
- **Should `User` be split into smaller, more focused modules?**
  _Cohesion score 0.1380952380952381 - nodes in this community are weakly interconnected._