# Graph Report - ربات کتابخوارشو  (2026-11-24)

## Corpus Check
- 17 files · ~117,104 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 6 file(s) not represented in the graph (top: (none) 4, .example 1, .bat 1)

## Summary
- 854 nodes · 3906 edges · 30 communities (21 shown, 9 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 484 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f1f228f5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- DateService
- League
- ReportService
- get_db
- send_startup_notification
- database.py
- User
- FSMContext
- AdminFlowInterruptMiddleware
- handlers.py
- deploy.sh
- AbsenceService
- MockBot
- main.py
- entrypoint.sh
- run_all_tests
- get_active_user
- _send_group_feature_list
- build_user_main_menu
- cleanse_prestart_activity_and_scores
- MessageService
- AdminStates
- _cancel_flow
- _collect_league_export_sync
- _prepare_log_snapshot_sync
- get_superadmins_list_keyboard
- run_tests.py
- admin_handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 176 edges
2. `run_all_tests()` - 140 edges
3. `League` - 119 edges
4. `User` - 100 edges
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
- `_get_user_past_days()` --uses--> `League`  [INFERRED]
  admin_handlers.py → models.py
- `_get_user_past_days()` --uses--> `User`  [INFERRED]
  admin_handlers.py → models.py
- `_get_user_past_days()` --uses--> `DateService`  [INFERRED]
  admin_handlers.py → services.py

## Import Cycles
- None detected.

## Communities (30 total, 9 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.06
Nodes (81): _amounts_line(), _announce_new_manager(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask(), _work() (+73 more)

### Community 1 - "DateService"
Cohesion: 0.12
Nodes (3): process_league_new_date(), _get_or_create_active_cycle_impl(), DateService

### Community 2 - "League"
Cohesion: 0.10
Nodes (24): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance() (+16 more)

### Community 4 - "get_db"
Cohesion: 0.12
Nodes (38): _build_global_stats_text_sync(), cb_broadcast_pick_group(), cb_broadcast_pick_league(), cb_cancel_delete_league(), cb_cancel_user_delete(), cb_confirm_delete_league(), cb_confirm_user_delete(), cb_delete_league_prompt() (+30 more)

### Community 5 - "send_startup_notification"
Cohesion: 0.08
Nodes (11): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), _get_all_admin_recipients_sync(), _get_superadmin_recipients(), send_startup_notification(), BaleAiohttpSession (+3 more)

### Community 6 - "database.py"
Cohesion: 0.06
Nodes (20): cmd_export_database(), backup_database(), _backup_postgres(), _ensure_indexes(), get_live_sqlite_path(), _get_table_columns_info(), init_db(), _prepare_row_for_destination() (+12 more)

### Community 7 - "User"
Cohesion: 0.15
Nodes (3): User, ScoringService, _build_weekly_task_sync()

### Community 8 - "FSMContext"
Cohesion: 0.11
Nodes (61): cb_adm_main_menu(), cb_admin_cancel(), cb_apply_db_cancel(), cb_apply_db_merge(), cb_apply_db_replace(), cb_broadcast_confirm_send(), cb_broadcast_target_all(), cb_broadcast_target_group() (+53 more)

### Community 10 - "handlers.py"
Cohesion: 0.09
Nodes (13): _pwd_is_locked(), _pwd_register_failure(), _state_int(), StudyStates, get_cancel_league_confirm(), get_cancel_or_back_keyboard(), get_confirm_revoke_sa_keyboard(), get_league_selection() (+5 more)

### Community 12 - "AbsenceService"
Cohesion: 0.16
Nodes (3): _post_merge_sync(), _midnight_job_sync(), AbsenceService

### Community 13 - "MockBot"
Cohesion: 0.13
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "main.py"
Cohesion: 0.10
Nodes (12): cmd_test_all_jobs(), set_system_state(), midnight_job(), send_daily_admin_reports(), send_daily_user_reports(), send_study_reminders(), _read_startup_states_and_cleanup_sync(), run_startup_catchups() (+4 more)

### Community 16 - "run_all_tests"
Cohesion: 0.17
Nodes (16): cb_execute_user_move_league(), get_or_create_active_cycle(), _build_single_admin_report_sync(), _check_league_morning_mode_sync(), _fetch_user_profile_sync(), format_league_leaderboard(), handle_append_study_today(), handle_edit_study_today() (+8 more)

### Community 17 - "get_active_user"
Cohesion: 0.25
Nodes (20): get_active_user(), get_user_profiles(), cmd_cancel_my_league(), cmd_start(), cmd_toggle_peer_notify(), cmd_toggle_reminder(), _dispatch_menu_interruption(), handle_back_to_main_menu() (+12 more)

### Community 18 - "_send_group_feature_list"
Cohesion: 0.09
Nodes (16): _build_group_feature_card(), _build_league_quota_card(), cb_em_reset_term(), cb_league_quota_adjust(), cb_user_move_league(), cmd_toggle_edit_yesterday_menu(), cmd_toggle_optional_pages_menu(), cmd_toggle_peer_notify_menu() (+8 more)

### Community 19 - "build_user_main_menu"
Cohesion: 0.14
Nodes (13): cb_execute_user_add_second_league(), _execute_user_add_second_league_impl(), _get_admin_profile_lock(), _split_league_user_payload(), generate_new_profile_id(), set_active_user_id(), build_user_main_menu(), cb_confirm_cancel_league() (+5 more)

### Community 20 - "cleanse_prestart_activity_and_scores"
Cohesion: 0.27
Nodes (3): _apply_league_quota_change(), cleanse_prestart_activity_and_scores(), reset_league_members_for_new_start()

### Community 21 - "MessageService"
Cohesion: 0.11
Nodes (9): _build_league_morning_cards_sync(), _build_morning_cards(), _build_study_reminders_outbox_sync(), _base(), _terms(), cb_join_new_group_prompt(), _fetch_user_leaderboard_sync(), _get_database_stats_sync() (+1 more)

### Community 23 - "_cancel_flow"
Cohesion: 0.40
Nodes (3): _build_admin_help_text(), _cancel_flow(), global_cancel_message()

### Community 27 - "run_tests.py"
Cohesion: 0.08
Nodes (14): _matches_superadmin_root_id(), demote_super_admin(), get_system_state(), _complete_and_rollover_cycle(), _init_daily_admin_reports_sync(), _init_morning_reports_sync(), ActivityLog, Cycle (+6 more)

### Community 28 - "admin_handlers.py"
Cohesion: 0.09
Nodes (57): _cleanup_expired_db_uploads(), cmd_add_group_admin(), cmd_add_league(), cmd_archive_exclude(), cmd_archive_include(), cmd_broadcast(), cmd_claim_superadmin(), cmd_create_group() (+49 more)

## Knowledge Gaps
- **4 isolated node(s):** `deploy.sh script`, `entrypoint.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 273 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `get_db` to `fine_handlers.py`, `DateService`, `ReportService`, `database.py`, `User`, `FSMContext`, `handlers.py`, `AbsenceService`, `main.py`, `run_all_tests`, `get_active_user`, `_send_group_feature_list`, `build_user_main_menu`, `MessageService`, `_cancel_flow`, `_collect_league_export_sync`, `_prepare_log_snapshot_sync`, `run_tests.py`, `admin_handlers.py`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `entrypoint.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.057133985405992856 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `run_all_tests` to `fine_handlers.py`, `DateService`, `League`, `ReportService`, `get_db`, `send_startup_notification`, `database.py`, `User`, `FSMContext`, `handlers.py`, `AbsenceService`, `MockBot`, `main.py`, `get_active_user`, `_send_group_feature_list`, `build_user_main_menu`, `cleanse_prestart_activity_and_scores`, `MessageService`, `AdminStates`, `_prepare_log_snapshot_sync`, `run_tests.py`, `admin_handlers.py`, `Config`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Are the 101 inferred relationships involving `League` (e.g. with `_apply_league_quota_change()` and `_build_global_stats_text_sync()`) actually correct?**
  _`League` has 101 INFERRED edges - model-reasoned connections that need verification._
- **Should `DateService` be split into smaller, more focused modules?**
  _Cohesion score 0.11954022988505747 - nodes in this community are weakly interconnected._