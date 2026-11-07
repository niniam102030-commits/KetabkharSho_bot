# Graph Report - ketabkharsho-argon  (2026-11-08)

## Corpus Check
- 16 files · ~87,511 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 725 nodes · 3217 edges · 23 communities (16 shown, 7 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 400 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `afcbf947`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- .today_str
- fine_service.py
- get_or_create_active_cycle
- League
- AdminStates
- database.py
- os
- DateService
- AdminFlowInterruptMiddleware
- User
- deploy.sh
- ReportService
- MockBot
- services.py
- midnight_job
- send_startup_notification
- admin_handlers.py
- BaleAiohttpSession
- send_weekly_reports
- handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 160 edges
2. `League` - 101 edges
3. `User` - 96 edges
4. `run_all_tests()` - 88 edges
5. `escape_md()` - 87 edges
6. `DateService` - 81 edges
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
- `_format_user_admin_card()` --uses--> `League`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (23 total, 7 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.07
Nodes (73): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_fines_text(), _build_refresh_outbox_sync(), cb_amount_ask() (+65 more)

### Community 1 - ".today_str"
Cohesion: 0.16
Nodes (8): BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox(), safe_send_document(), send_daily_admin_reports(), _send_daily_user_reports_impl(), send_study_reminders(), send_text_chunks()

### Community 2 - "fine_service.py"
Cohesion: 0.06
Nodes (26): add_manager(), count_active_fine_kinds(), get_all_manager_tg_ids(), get_debtors(), get_managed_leagues(), get_manager_ids(), get_user_balance(), get_user_fine_records() (+18 more)

### Community 3 - "get_or_create_active_cycle"
Cohesion: 0.16
Nodes (5): get_or_create_active_cycle(), _build_single_admin_report_sync(), format_league_leaderboard(), _midnight_job_sync(), AbsenceService

### Community 4 - "League"
Cohesion: 0.17
Nodes (11): process_user_new_streak(), get_system_state(), set_system_state(), _build_league_morning_cards_sync(), _build_morning_cards(), _build_study_reminders_outbox_sync(), _complete_and_rollover_cycle(), _init_daily_admin_reports_sync() (+3 more)

### Community 6 - "database.py"
Cohesion: 0.09
Nodes (12): backup_database(), _backup_postgres(), _ensure_indexes(), init_db(), run_db(), _run_migrations(), _run_postgres_fine_migrations(), _run_sync_db_callable() (+4 more)

### Community 8 - "DateService"
Cohesion: 0.09
Nodes (5): _get_user_past_days(), process_league_new_date(), _check_league_morning_mode_sync(), user_can_log_late(), DateService

### Community 10 - "User"
Cohesion: 0.16
Nodes (5): _fetch_user_profile_sync(), process_study_pages(), User, ScoringService, _build_weekly_task_sync()

### Community 12 - "ReportService"
Cohesion: 0.16
Nodes (3): _collect_league_export_sync(), _read_startup_states_and_cleanup_sync(), ReportService

### Community 13 - "MockBot"
Cohesion: 0.15
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 15 - "services.py"
Cohesion: 0.18
Nodes (4): _build_global_stats_text_sync(), ActivityLog, Cycle, SystemState

### Community 16 - "midnight_job"
Cohesion: 0.19
Nodes (6): cmd_test_all_jobs(), midnight_job(), send_daily_user_reports(), run_startup_catchups(), _run_safe_job(), setup_scheduler()

### Community 17 - "send_startup_notification"
Cohesion: 0.20
Nodes (6): راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), send_startup_notification(), main()

### Community 18 - "admin_handlers.py"
Cohesion: 0.06
Nodes (137): _build_admin_help_text(), _build_cycle_history_excel_sync(), _cancel_flow(), cb_admin_cancel(), cb_broadcast_confirm_send(), cb_broadcast_pick_group(), cb_broadcast_pick_league(), cb_broadcast_target_all() (+129 more)

### Community 20 - "send_weekly_reports"
Cohesion: 0.40
Nodes (3): safe_send(), send_weekly_reports(), _deliver()

### Community 21 - "handlers.py"
Cohesion: 0.07
Nodes (47): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), _base(), build_user_main_menu(), cb_confirm_cancel_league(), cb_join_league() (+39 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 233 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `get_or_create_active_cycle`, `League`, `database.py`, `os`, `DateService`, `User`, `ReportService`, `main.py`, `services.py`, `midnight_job`, `send_weekly_reports`, `handlers.py`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 86 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 86 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0720658888126287 - nodes in this community are weakly interconnected._
- **Why does `User` connect `User` to `fine_handlers.py`, `fine_service.py`, `get_or_create_active_cycle`, `League`, `database.py`, `DateService`, `ReportService`, `main.py`, `services.py`, `admin_handlers.py`, `handlers.py`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Are the 68 inferred relationships involving `User` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`User` has 68 INFERRED edges - model-reasoned connections that need verification._
- **Should `fine_service.py` be split into smaller, more focused modules?**
  _Cohesion score 0.056189640035118525 - nodes in this community are weakly interconnected._