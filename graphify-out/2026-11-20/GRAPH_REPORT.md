# Graph Report - ربات کتابخوارشو  (2026-11-20)

## Corpus Check
- 16 files · ~103,704 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 782 nodes · 3492 edges · 21 communities (15 shown, 6 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 431 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `3525415d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- DateService
- fine_service.py
- _complete_and_rollover_cycle
- User
- run_tests.py
- database.py
- models.py
- send_weekly_reports
- AdminFlowInterruptMiddleware
- run_db
- deploy.sh
- _build_weekly_task_sync
- MockBot
- services.py
- _get_admin_profile_lock
- .today_shamsi
- admin_handlers.py
- run_all_tests
- handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 163 edges
2. `run_all_tests()` - 111 edges
3. `League` - 104 edges
4. `User` - 95 edges
5. `escape_md()` - 91 edges
6. `DateService` - 88 edges
7. `is_user_admin()` - 73 edges
8. `safe_send_message()` - 60 edges
9. `safe_reply()` - 51 edges
10. `MessageService` - 49 edges

## Surprising Connections (you probably didn't know these)
- `🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب)` --references--> `main()`  [INFERRED]
  docker/README.md → main.py
- `run_all_tests()` --uses--> `AdminStates`  [INFERRED]
  run_tests.py → admin_handlers.py
- `_get_user_past_days()` --uses--> `League`  [INFERRED]
  admin_handlers.py → models.py
- `_get_user_past_days()` --uses--> `DateService`  [INFERRED]
  admin_handlers.py → services.py
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (21 total, 6 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (74): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+66 more)

### Community 1 - "DateService"
Cohesion: 0.13
Nodes (3): process_league_new_date(), cleanse_prestart_activity_and_scores(), DateService

### Community 2 - "fine_service.py"
Cohesion: 0.10
Nodes (23): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance() (+15 more)

### Community 3 - "_complete_and_rollover_cycle"
Cohesion: 0.15
Nodes (4): _build_cycle_history_excel_sync(), _collect_league_export_sync(), _complete_and_rollover_cycle(), ReportService

### Community 4 - "User"
Cohesion: 0.12
Nodes (8): _post_merge_sync(), _format_user_admin_card(), _get_user_past_days(), process_user_new_late(), process_user_new_no_study(), _midnight_job_sync(), User, AbsenceService

### Community 5 - "run_tests.py"
Cohesion: 0.11
Nodes (4): AdminStates, StudyStates, make_fsm(), MockDocument

### Community 6 - "database.py"
Cohesion: 0.09
Nodes (13): backup_database(), _backup_postgres(), _ensure_indexes(), get_live_sqlite_path(), init_db(), reload_superadmins_from_db(), restore_database_merge(), restore_database_replace() (+5 more)

### Community 7 - "models.py"
Cohesion: 0.14
Nodes (9): _build_global_stats_text_sync(), ActivityLog, Cycle, CycleResult, generate_league_id(), GroupAdmin, GroupMessage, GroupTerm (+1 more)

### Community 8 - "send_weekly_reports"
Cohesion: 0.05
Nodes (28): cmd_test_all_jobs(), راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox() (+20 more)

### Community 10 - "run_db"
Cohesion: 0.32
Nodes (4): _get_table_columns_info(), _prepare_row_for_destination(), run_db(), _run_sync_db_callable()

### Community 13 - "MockBot"
Cohesion: 0.13
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 17 - ".today_shamsi"
Cohesion: 0.24
Nodes (3): cmd_datetest(), cmd_export_system_logs(), _prepare_log_snapshot_sync()

### Community 18 - "admin_handlers.py"
Cohesion: 0.06
Nodes (137): _build_admin_help_text(), _cancel_flow(), cb_admin_cancel(), cb_apply_db_cancel(), cb_apply_db_merge(), cb_apply_db_replace(), cb_broadcast_confirm_send(), cb_broadcast_pick_group() (+129 more)

### Community 20 - "run_all_tests"
Cohesion: 0.26
Nodes (3): cmd_global_stats(), midnight_job(), run_all_tests()

### Community 21 - "handlers.py"
Cohesion: 0.06
Nodes (64): cb_execute_user_move_league(), _execute_user_add_second_league_impl(), generate_new_profile_id(), get_active_user(), get_or_create_active_cycle(), get_user_profiles(), set_active_user_id(), set_system_state() (+56 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 252 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `DateService`, `_complete_and_rollover_cycle`, `User`, `run_tests.py`, `database.py`, `models.py`, `send_weekly_reports`, `run_db`, `_build_weekly_task_sync`, `services.py`, `_get_admin_profile_lock`, `.today_shamsi`, `run_all_tests`, `handlers.py`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0706140350877193 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `run_all_tests` to `fine_handlers.py`, `DateService`, `fine_service.py`, `_complete_and_rollover_cycle`, `User`, `run_tests.py`, `database.py`, `models.py`, `send_weekly_reports`, `Config`, `MockBot`, `services.py`, `_get_admin_profile_lock`, `.today_shamsi`, `admin_handlers.py`, `handlers.py`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 88 INFERRED edges - model-reasoned connections that need verification._
- **Should `DateService` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._