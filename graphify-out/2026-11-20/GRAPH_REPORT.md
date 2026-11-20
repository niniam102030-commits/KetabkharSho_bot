# Graph Report - ربات کتابخوارشو  (2026-11-20)

## Corpus Check
- 16 files · ~91,570 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 751 nodes · 3365 edges · 23 communities (14 shown, 9 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 419 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1734b9fc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- _get_admin_profile_lock
- fine_service.py
- League
- .normalize_digits
- run_tests.py
- database.py
- DateService
- send_weekly_reports
- AdminFlowInterruptMiddleware
- send_startup_notification
- deploy.sh
- راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker)
- MockBot
- services.py
- models.py
- AdminStates
- admin_handlers.py
- StudyStates
- make_fsm
- handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 160 edges
2. `League` - 104 edges
3. `run_all_tests()` - 102 edges
4. `User` - 95 edges
5. `escape_md()` - 88 edges
6. `DateService` - 88 edges
7. `is_user_admin()` - 73 edges
8. `safe_send_message()` - 57 edges
9. `MessageService` - 49 edges
10. `safe_reply()` - 48 edges

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

## Communities (23 total, 9 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (74): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+66 more)

### Community 2 - "fine_service.py"
Cohesion: 0.10
Nodes (23): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance() (+15 more)

### Community 3 - "League"
Cohesion: 0.05
Nodes (32): _build_cycle_history_excel_sync(), _build_global_stats_text_sync(), cb_execute_user_move_league(), _collect_league_export_sync(), process_league_new_date(), get_or_create_active_cycle(), set_system_state(), _build_league_morning_cards_sync() (+24 more)

### Community 4 - ".normalize_digits"
Cohesion: 0.20
Nodes (10): _format_user_admin_card(), _get_user_manage_keyboard(), _get_user_past_days(), process_user_new_floor(), process_user_new_late(), process_user_new_minutes(), process_user_new_no_study(), process_user_new_pages() (+2 more)

### Community 5 - "run_tests.py"
Cohesion: 0.17
Nodes (18): cmd_create_group(), cmd_export_cycle_history_excel(), cmd_export_database(), cmd_global_stats(), cmd_test_startup_notification(), process_al_league_floor(), process_al_league_name(), process_broadcast_text() (+10 more)

### Community 6 - "database.py"
Cohesion: 0.09
Nodes (9): backup_database(), _backup_postgres(), _ensure_indexes(), run_db(), _run_migrations(), _run_postgres_fine_migrations(), _run_sync_db_callable(), set_sqlite_pragma() (+1 more)

### Community 7 - "DateService"
Cohesion: 0.12
Nodes (5): cmd_datetest(), cmd_export_system_logs(), _prepare_log_snapshot_sync(), init_db(), DateService

### Community 8 - "send_weekly_reports"
Cohesion: 0.06
Nodes (21): cmd_test_all_jobs(), BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox(), _format_file_size(), midnight_job(), safe_send(), safe_send_document() (+13 more)

### Community 10 - "send_startup_notification"
Cohesion: 0.40
Nodes (3): send_startup_notification(), main(), on_startup()

### Community 12 - "راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker)"
Cohesion: 0.40
Nodes (4): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)

### Community 13 - "MockBot"
Cohesion: 0.15
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 16 - "models.py"
Cohesion: 0.17
Nodes (6): CycleResult, generate_league_id(), GroupAdmin, GroupMessage, GroupTerm, SystemState

### Community 18 - "admin_handlers.py"
Cohesion: 0.07
Nodes (109): _build_admin_help_text(), _cancel_flow(), cb_admin_cancel(), cb_broadcast_confirm_send(), cb_broadcast_pick_group(), cb_broadcast_pick_league(), cb_broadcast_target_all(), cb_broadcast_target_group() (+101 more)

### Community 21 - "handlers.py"
Cohesion: 0.07
Nodes (46): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), _base(), _terms(), build_user_main_menu(), cb_confirm_cancel_league() (+38 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 245 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `_get_admin_profile_lock`, `League`, `.normalize_digits`, `run_tests.py`, `database.py`, `DateService`, `send_weekly_reports`, `services.py`, `handlers.py`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Are the 88 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 88 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0706140350877193 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `run_tests.py` to `fine_handlers.py`, `League`, `.normalize_digits`, `DateService`, `send_weekly_reports`, `Config`, `send_startup_notification`, `MockBot`, `models.py`, `AdminStates`, `admin_handlers.py`, `StudyStates`, `make_fsm`, `handlers.py`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Should `fine_service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09797979797979799 - nodes in this community are weakly interconnected._