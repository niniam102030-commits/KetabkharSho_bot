# Graph Report - ketabkharsho-argon  (2026-11-08)

## Corpus Check
- 16 files · ~87,975 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .example 1, .bat 1)

## Summary
- 729 nodes · 3231 edges · 19 communities (11 shown, 8 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 399 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `afcbf947`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- fine_handlers.py
- send_weekly_reports
- League
- get_or_create_active_cycle
- User
- AdminStates
- database.py
- run_all_tests
- ._compute_raw_streak_from_logs
- AdminFlowInterruptMiddleware
- _build_weekly_task_sync
- deploy.sh
- _complete_and_rollover_cycle
- MockBot
- process_em_new_msg
- make_fsm
- admin_handlers.py
- handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 160 edges
2. `League` - 101 edges
3. `User` - 92 edges
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
- `_get_user_past_days()` --uses--> `DateService`  [INFERRED]
  admin_handlers.py → services.py
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (19 total, 8 thin omitted)

### Community 0 - "fine_handlers.py"
Cohesion: 0.08
Nodes (68): _amounts_line(), _announce_new_manager(), _kb(), _auth_menu(), _btn(), _build_refresh_outbox_sync(), cb_amount_ask(), _work() (+60 more)

### Community 1 - "send_weekly_reports"
Cohesion: 0.06
Nodes (26): cmd_test_all_jobs(), راهنمای استقرار و دیپلوی ربات کتابخوارشو با داکر (Docker), 🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور), 🔄 ۲. بروزرسانی خودکار ربات (پس از هر تغییر در کدهای گیت‌هاب), 💾 ۳. امنیت داده‌ها و دیتابیس (Volumes), BroadcastThrottle, _dispatch_cycle_rollover(), dispatch_outbox() (+18 more)

### Community 2 - "League"
Cohesion: 0.08
Nodes (30): _build_fines_text(), _work(), _work(), _managed_leagues_picker(), _roles(), add_manager(), count_active_fine_kinds(), freeze_user_fines() (+22 more)

### Community 3 - "get_or_create_active_cycle"
Cohesion: 0.15
Nodes (6): process_league_new_date(), get_or_create_active_cycle(), _build_single_admin_report_sync(), format_league_leaderboard(), _midnight_job_sync(), AbsenceService

### Community 4 - "User"
Cohesion: 0.17
Nodes (15): _format_user_admin_card(), _get_user_manage_keyboard(), _get_user_past_days(), process_league_new_cycle(), process_league_new_floor(), process_user_new_floor(), process_user_new_late(), process_user_new_minutes() (+7 more)

### Community 6 - "database.py"
Cohesion: 0.05
Nodes (21): backup_database(), _backup_postgres(), _ensure_indexes(), get_system_state(), init_db(), run_db(), _run_migrations(), _run_postgres_fine_migrations() (+13 more)

### Community 7 - "run_all_tests"
Cohesion: 0.13
Nodes (10): cmd_datetest(), cmd_export_system_logs(), cmd_global_stats(), _prepare_log_snapshot_sync(), process_al_league_floor(), process_cg_password(), process_pg_new_password(), is_group_password_unique() (+2 more)

### Community 12 - "_complete_and_rollover_cycle"
Cohesion: 0.13
Nodes (5): _build_cycle_history_excel_sync(), _collect_league_export_sync(), _complete_and_rollover_cycle(), CycleResult, ReportService

### Community 13 - "MockBot"
Cohesion: 0.15
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 18 - "admin_handlers.py"
Cohesion: 0.07
Nodes (116): _build_admin_help_text(), _build_global_stats_text_sync(), _cancel_flow(), cb_admin_cancel(), cb_broadcast_confirm_send(), cb_broadcast_pick_group(), cb_broadcast_pick_league(), cb_broadcast_target_all() (+108 more)

### Community 21 - "handlers.py"
Cohesion: 0.06
Nodes (53): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), _build_league_morning_cards_sync(), _build_morning_cards(), _build_study_reminders_outbox_sync(), _base() (+45 more)

## Knowledge Gaps
- **3 isolated node(s):** `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 235 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `admin_handlers.py` to `fine_handlers.py`, `send_weekly_reports`, `League`, `get_or_create_active_cycle`, `User`, `database.py`, `run_all_tests`, `._compute_raw_streak_from_logs`, `_build_weekly_task_sync`, `_complete_and_rollover_cycle`, `process_em_new_msg`, `handlers.py`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Are the 86 inferred relationships involving `League` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`League` has 86 INFERRED edges - model-reasoned connections that need verification._
- **What connects `deploy.sh script`, `🛠️ ۱. راه‌اندازی اولیه روی سرور (توسط مسئول سرور)`, `💾 ۳. امنیت داده‌ها و دیتابیس (Volumes)` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_handlers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07863113897596656 - nodes in this community are weakly interconnected._
- **Why does `League` connect `League` to `fine_handlers.py`, `send_weekly_reports`, `get_or_create_active_cycle`, `User`, `database.py`, `run_all_tests`, `._compute_raw_streak_from_logs`, `_build_weekly_task_sync`, `_complete_and_rollover_cycle`, `admin_handlers.py`, `handlers.py`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Are the 64 inferred relationships involving `User` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`User` has 64 INFERRED edges - model-reasoned connections that need verification._
- **Should `send_weekly_reports` be split into smaller, more focused modules?**
  _Cohesion score 0.055288461538461536 - nodes in this community are weakly interconnected._