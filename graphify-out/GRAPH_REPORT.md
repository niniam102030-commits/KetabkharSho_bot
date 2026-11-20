# Graph Report - ربات کتابخوارشو  (2026-11-20)

## Corpus Check
- 16 files · ~89,565 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 735 nodes · 3306 edges · 21 communities (15 shown, 6 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 406 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `acad356c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- send_weekly_reports
- fine_service.py
- AbsenceService
- League
- AdminStates
- database.py
- DateService
- AdminFlowInterruptMiddleware
- User
- deploy.sh
- ReportService
- MockBot
- run_all_tests
- models.py
- set_system_state
- admin_handlers.py
- handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 160 edges
2. `League` - 102 edges
3. `run_all_tests()` - 96 edges
4. `User` - 93 edges
5. `escape_md()` - 87 edges
6. `DateService` - 86 edges
7. `is_user_admin()` - 73 edges
8. `safe_send_message()` - 56 edges
9. `MessageService` - 49 edges
10. `safe_reply()` - 47 edges

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

## Communities (21 total, 6 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (75): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+67 more)

### Community 1 - "send_weekly_reports"
Cohesion: 0.06
Nodes (25): cmd_test_all_jobs(), راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox() (+17 more)

### Community 2 - "fine_service.py"
Cohesion: 0.11
Nodes (21): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance() (+13 more)

### Community 3 - "AbsenceService"
Cohesion: 0.16
Nodes (5): _get_user_past_days(), process_user_new_late(), process_user_new_no_study(), _sync_league_fines_impl(), AbsenceService

### Community 4 - "League"
Cohesion: 0.16
Nodes (12): _build_global_stats_text_sync(), process_al_league_floor(), process_league_new_cycle(), process_user_new_streak(), get_or_create_active_cycle(), _build_league_morning_cards_sync(), _build_morning_cards(), _check_league_morning_mode_sync() (+4 more)

### Community 6 - "database.py"
Cohesion: 0.10
Nodes (8): backup_database(), _backup_postgres(), _ensure_indexes(), run_db(), _run_migrations(), _run_postgres_fine_migrations(), _run_sync_db_callable(), set_sqlite_pragma()

### Community 7 - "DateService"
Cohesion: 0.16
Nodes (4): cmd_datetest(), cmd_export_system_logs(), _prepare_log_snapshot_sync(), DateService

### Community 10 - "User"
Cohesion: 0.15
Nodes (4): _fetch_user_profile_sync(), User, ScoringService, _build_weekly_task_sync()

### Community 12 - "ReportService"
Cohesion: 0.16
Nodes (3): _build_cycle_history_excel_sync(), _collect_league_export_sync(), ReportService

### Community 13 - "MockBot"
Cohesion: 0.15
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "run_all_tests"
Cohesion: 0.19
Nodes (10): process_league_new_date(), init_db(), _build_single_admin_report_sync(), format_league_leaderboard(), _midnight_job_sync(), process_study_pages(), reset_league_members_for_new_start(), user_can_log_late() (+2 more)

### Community 16 - "models.py"
Cohesion: 0.18
Nodes (6): CycleResult, generate_league_id(), GroupAdmin, GroupMessage, GroupTerm, SystemState

### Community 17 - "set_system_state"
Cohesion: 0.14
Nodes (10): generate_new_profile_id(), get_system_state(), is_group_password_unique(), set_system_state(), _sync_postgres_sequences(), _init_daily_admin_reports_sync(), _init_morning_reports_sync(), _pwd_register_failure() (+2 more)

### Community 18 - "admin_handlers.py"
Cohesion: 0.06
Nodes (129): _build_admin_help_text(), _cancel_flow(), cb_admin_cancel(), cb_broadcast_confirm_send(), cb_broadcast_pick_group(), cb_broadcast_pick_league(), cb_broadcast_target_all(), cb_broadcast_target_group() (+121 more)

### Community 21 - "handlers.py"
Cohesion: 0.07
Nodes (45): get_active_user(), get_user_profiles(), set_active_user_id(), _build_study_reminders_outbox_sync(), _base(), _terms(), build_user_main_menu(), cb_confirm_cancel_league() (+37 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 238 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `send_weekly_reports`, `AbsenceService`, `League`, `database.py`, `DateService`, `User`, `ReportService`, `run_all_tests`, `main.py`, `set_system_state`, `handlers.py`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Are the 86 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 86 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06858826004628656 - nodes in this community are weakly interconnected._
- **Why does `League` connect `League` to `fine_handlers.py`, `send_weekly_reports`, `fine_service.py`, `AbsenceService`, `database.py`, `._compute_raw_streak_from_logs`, `User`, `ReportService`, `run_all_tests`, `main.py`, `models.py`, `set_system_state`, `admin_handlers.py`, `handlers.py`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `send_weekly_reports` be split into smaller, more focused modules?**
  _Cohesion score 0.057859703020993344 - nodes in this community are weakly interconnected._