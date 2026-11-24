# Graph Report - ربات کتابخوارشو  (2026-11-24)

## Corpus Check
- 17 files · ~117,872 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .example 1, .bat 1)

## Summary
- 858 nodes · 3927 edges · 30 communities (19 shown, 11 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 491 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e6fe76a0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- League
- fine_service.py
- get_system_state
- Group
- ReportService
- database.py
- _build_weekly_task_sync
- get_db
- AdminFlowInterruptMiddleware
- keyboards.py
- deploy.sh
- _get_user_lock
- MockBot
- run_tests.py
- entrypoint.sh
- set_system_state
- handlers.py
- _send_leagues_management_list
- _cb_join_league_impl
- make_fsm
- .get_terms
- AdminStates
- _cancel_flow
- run_all_tests
- StudyStates
- models.py
- admin_handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 176 edges
2. `run_all_tests()` - 141 edges
3. `League` - 120 edges
4. `User` - 101 edges
5. `escape_md()` - 97 edges
6. `is_user_admin()` - 94 edges
7. `DateService` - 93 edges
8. `safe_send_message()` - 69 edges
9. `Group` - 53 edges
10. `safe_reply()` - 52 edges

## Surprising Connections (you probably didn't know these)
- `🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب)` --references--> `main()`  [INFERRED]
  docker/README.md → main.py
- `run_all_tests()` --uses--> `AdminStates`  [INFERRED]
  run_tests.py → admin_handlers.py
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py
- `_format_user_admin_card()` --uses--> `League`  [INFERRED]
  admin_handlers.py → models.py
- `_format_user_admin_card()` --uses--> `User`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (30 total, 11 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (76): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+68 more)

### Community 1 - "League"
Cohesion: 0.06
Nodes (27): _apply_league_quota_change(), _post_merge_sync(), cb_execute_user_move_league(), _execute_user_add_second_league_impl(), _get_user_past_days(), process_league_new_date(), _split_league_user_payload(), get_or_create_active_cycle() (+19 more)

### Community 2 - "fine_service.py"
Cohesion: 0.12
Nodes (20): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_managed_leagues(), get_manager_ids(), get_user_balance(), get_user_fine_records() (+12 more)

### Community 3 - "get_system_state"
Cohesion: 0.14
Nodes (11): get_system_state(), _build_league_morning_cards_sync(), _build_morning_cards(), _build_study_reminders_outbox_sync(), _base(), _get_database_stats_sync(), _init_daily_admin_reports_sync(), _init_morning_reports_sync() (+3 more)

### Community 4 - "Group"
Cohesion: 0.11
Nodes (23): cb_broadcast_pick_group(), cb_menu_broadcast(), cb_menu_excel(), cb_menu_new_league(), cb_menu_stats(), cb_menu_users_list(), cmd_add_league(), cmd_broadcast() (+15 more)

### Community 5 - "ReportService"
Cohesion: 0.05
Nodes (15): _build_cycle_history_excel_sync(), _collect_league_export_sync(), راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), _get_all_admin_recipients_sync(), _get_superadmin_recipients() (+7 more)

### Community 6 - "database.py"
Cohesion: 0.07
Nodes (17): backup_database(), _backup_postgres(), _ensure_indexes(), get_live_sqlite_path(), _get_table_columns_info(), init_db(), _prepare_row_for_destination(), reload_superadmins_from_db() (+9 more)

### Community 8 - "get_db"
Cohesion: 0.13
Nodes (65): cb_adm_main_menu(), cb_admin_cancel(), cb_apply_db_cancel(), cb_apply_db_merge(), cb_apply_db_replace(), cb_broadcast_confirm_send(), cb_broadcast_pick_league(), cb_broadcast_target_all() (+57 more)

### Community 10 - "keyboards.py"
Cohesion: 0.14
Nodes (7): get_cancel_league_confirm(), get_main_menu(), get_optional_pages_keyboard(), get_profile_switch_keyboard(), get_study_edit_menu(), get_study_minutes_keyboard(), get_superadmin_alert_keyboard()

### Community 13 - "MockBot"
Cohesion: 0.13
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "run_tests.py"
Cohesion: 0.09
Nodes (6): cmd_test_all_jobs(), send_daily_user_reports(), MockDocument, _run_safe_job(), setup_scheduler(), send_weekly_reports()

### Community 16 - "set_system_state"
Cohesion: 0.11
Nodes (16): set_system_state(), BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox(), midnight_job(), safe_send(), safe_send_document(), send_daily_admin_reports() (+8 more)

### Community 17 - "handlers.py"
Cohesion: 0.18
Nodes (33): get_active_user(), get_user_profiles(), _build_minutes_quick_options(), build_user_main_menu(), cb_join_new_group_prompt(), cmd_cancel_my_league(), cmd_start(), cmd_toggle_peer_notify() (+25 more)

### Community 18 - "_send_leagues_management_list"
Cohesion: 0.09
Nodes (15): _build_group_feature_card(), _build_league_quota_card(), cb_menu_league_quotas(), cb_menu_leagues(), cmd_edit_or_delete_leagues(), cmd_league_quotas(), _get_em_main_keyboard(), _get_em_msgs_keyboard() (+7 more)

### Community 19 - "_cb_join_league_impl"
Cohesion: 0.29
Nodes (6): generate_new_profile_id(), set_active_user_id(), cb_confirm_cancel_league(), cb_join_league(), _cb_join_league_impl(), cb_switch_profile()

### Community 23 - "_cancel_flow"
Cohesion: 0.22
Nodes (7): _build_admin_help_text(), _cancel_flow(), cmd_claim_superadmin(), global_cancel_callback(), global_cancel_message(), show_admin_panel(), get_admin_main_inline_menu()

### Community 24 - "run_all_tests"
Cohesion: 0.11
Nodes (19): cb_menu_backup_db(), cb_menu_edit_yesterday(), cb_menu_manage_superadmins(), cb_menu_optional_pages(), cb_menu_peer_notify(), cb_revoke_sa_confirm(), cb_revoke_sa_prompt(), cb_toggle_edit_yesterday() (+11 more)

### Community 27 - "models.py"
Cohesion: 0.13
Nodes (7): demote_super_admin(), CycleResult, generate_league_id(), GroupAdmin, GroupMessage, GroupTerm, SystemState

### Community 28 - "admin_handlers.py"
Cohesion: 0.09
Nodes (52): _build_global_stats_text_sync(), _cleanup_expired_db_uploads(), cmd_add_group_admin(), cmd_archive_exclude(), cmd_archive_include(), cmd_create_group(), cmd_datetest(), cmd_export_cycle_history_excel() (+44 more)

## Knowledge Gaps
- **4 isolated node(s):** `deploy.sh script`, `entrypoint.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 275 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `get_db` to `fine_handlers.py`, `League`, `get_system_state`, `Group`, `ReportService`, `database.py`, `_build_weekly_task_sync`, `_get_user_lock`, `run_tests.py`, `set_system_state`, `handlers.py`, `_send_leagues_management_list`, `_cb_join_league_impl`, `_cancel_flow`, `run_all_tests`, `models.py`, `admin_handlers.py`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `entrypoint.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06594059405940594 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `run_all_tests` to `fine_handlers.py`, `League`, `fine_service.py`, `get_system_state`, `Group`, `ReportService`, `database.py`, `get_db`, `MockBot`, `run_tests.py`, `set_system_state`, `handlers.py`, `_send_leagues_management_list`, `_cb_join_league_impl`, `make_fsm`, `.get_terms`, `AdminStates`, `_cancel_flow`, `StudyStates`, `models.py`, `admin_handlers.py`, `Config`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Are the 102 inferred relationships involving `League` (e.g. with `_apply_league_quota_change()` and `_build_global_stats_text_sync()`) actually correct?**
  _`League` has 102 INFERRED edges - model-reasoned connections that need verification._
- **Should `League` be split into smaller, more focused modules?**
  _Cohesion score 0.06328592042877758 - nodes in this community are weakly interconnected._