# Graph Report - ربات کتابخوارشو  (2026-11-20)

## Corpus Check
- 16 files · ~90,465 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 745 nodes · 3322 edges · 23 communities (16 shown, 7 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 412 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b4200fa6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- send_weekly_reports
- fine_service.py
- run_all_tests
- AbsenceService
- run_tests.py
- init_db
- DateService
- safe_send
- AdminFlowInterruptMiddleware
- User
- deploy.sh
- ReportService
- MockBot
- League
- database.py
- Cycle
- admin_handlers.py
- set_sqlite_pragma
- run_db
- handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 159 edges
2. `League` - 103 edges
3. `run_all_tests()` - 98 edges
4. `User` - 94 edges
5. `escape_md()` - 87 edges
6. `DateService` - 87 edges
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
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (23 total, 7 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (74): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+66 more)

### Community 1 - "send_weekly_reports"
Cohesion: 0.11
Nodes (14): cmd_test_all_jobs(), get_system_state(), set_system_state(), _init_daily_admin_reports_sync(), _init_morning_reports_sync(), midnight_job(), send_daily_admin_reports(), send_daily_user_reports() (+6 more)

### Community 2 - "fine_service.py"
Cohesion: 0.11
Nodes (20): add_manager(), count_active_fine_kinds(), freeze_user_fines(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance() (+12 more)

### Community 3 - "run_all_tests"
Cohesion: 0.16
Nodes (4): _check_league_morning_mode_sync(), process_study_pages(), user_can_log_late(), run_all_tests()

### Community 4 - "AbsenceService"
Cohesion: 0.12
Nodes (4): process_league_new_date(), cleanse_prestart_activity_and_scores(), _midnight_job_sync(), AbsenceService

### Community 5 - "run_tests.py"
Cohesion: 0.12
Nodes (3): AdminStates, StudyStates, make_fsm()

### Community 6 - "init_db"
Cohesion: 0.20
Nodes (5): _ensure_indexes(), init_db(), _run_migrations(), _run_postgres_fine_migrations(), _sync_postgres_sequences()

### Community 7 - "DateService"
Cohesion: 0.08
Nodes (35): _build_admin_help_text(), _build_cycle_history_excel_sync(), cmd_create_group(), cmd_datetest(), cmd_export_cycle_history_excel(), cmd_export_system_logs(), cmd_global_stats(), cmd_test_archive() (+27 more)

### Community 8 - "safe_send"
Cohesion: 0.06
Nodes (19): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), BroadcastThrottle, _build_league_morning_cards_sync(), _dispatch_cycle_rollover(), dispatch_outbox() (+11 more)

### Community 10 - "User"
Cohesion: 0.17
Nodes (4): _complete_and_rollover_cycle(), _fetch_user_profile_sync(), User, ScoringService

### Community 13 - "MockBot"
Cohesion: 0.15
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "League"
Cohesion: 0.15
Nodes (9): _collect_league_export_sync(), get_or_create_active_cycle(), sync_all_enabled_leagues(), sync_league_fines(), _sync_league_fines_impl(), _build_single_admin_report_sync(), format_league_leaderboard(), League (+1 more)

### Community 16 - "database.py"
Cohesion: 0.11
Nodes (8): backup_database(), _backup_postgres(), CycleResult, generate_league_id(), GroupAdmin, GroupMessage, GroupTerm, SystemState

### Community 17 - "Cycle"
Cohesion: 0.27
Nodes (5): _build_global_stats_text_sync(), _build_morning_cards(), reset_league_members_for_new_start(), ActivityLog, Cycle

### Community 18 - "admin_handlers.py"
Cohesion: 0.07
Nodes (105): _cancel_flow(), cb_admin_cancel(), cb_broadcast_confirm_send(), cb_broadcast_pick_group(), cb_broadcast_pick_league(), cb_broadcast_target_all(), cb_broadcast_target_group(), cb_broadcast_target_league() (+97 more)

### Community 21 - "handlers.py"
Cohesion: 0.06
Nodes (49): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), _build_study_reminders_outbox_sync(), _base(), _terms(), build_user_main_menu() (+41 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 244 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `send_weekly_reports`, `run_all_tests`, `AbsenceService`, `run_tests.py`, `init_db`, `DateService`, `safe_send`, `User`, `League`, `services.py`, `database.py`, `Cycle`, `run_db`, `handlers.py`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Are the 87 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 87 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0706140350877193 - nodes in this community are weakly interconnected._
- **Why does `League` connect `League` to `fine_handlers.py`, `send_weekly_reports`, `fine_service.py`, `run_all_tests`, `AbsenceService`, `run_tests.py`, `init_db`, `DateService`, `safe_send`, `User`, `ReportService`, `services.py`, `database.py`, `Cycle`, `admin_handlers.py`, `handlers.py`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `send_weekly_reports` be split into smaller, more focused modules?**
  _Cohesion score 0.11083743842364532 - nodes in this community are weakly interconnected._