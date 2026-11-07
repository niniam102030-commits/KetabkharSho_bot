# Graph Report - ketabkharsho-argon  (2026-11-07)

## Corpus Check
- 12 files · ~72,984 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .example 1, .bat 1)

## Summary
- 582 nodes · 2618 edges · 23 communities (15 shown, 8 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 329 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c47b7bf4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- process_study_pages
- set_system_state
- _complete_and_rollover_cycle
- main.py
- run_db
- database.py
- User
- get_db
- AdminFlowInterruptMiddleware
- DateService
- escape_md
- admin_handlers.py
- run_tests.py
- League
- cb_user_add_second_league
- _get_admin_profile_lock
- AdminStates
- FSMContext
- StudyStates
- handlers.py
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 133 edges
2. `run_all_tests()` - 84 edges
3. `User` - 83 edges
4. `DateService` - 79 edges
5. `League` - 78 edges
6. `escape_md()` - 72 edges
7. `is_user_admin()` - 68 edges
8. `safe_send_message()` - 56 edges
9. `MessageService` - 49 edges
10. `safe_reply()` - 47 edges

## Surprising Connections (you probably didn't know these)
- `run_all_tests()` --uses--> `AdminStates`  [INFERRED]
  run_tests.py → admin_handlers.py
- `_get_user_past_days()` --uses--> `User`  [INFERRED]
  admin_handlers.py → models.py
- `_get_user_past_days()` --uses--> `DateService`  [INFERRED]
  admin_handlers.py → services.py
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py
- `_format_user_admin_card()` --uses--> `League`  [INFERRED]
  admin_handlers.py → models.py

## Import Cycles
- None detected.

## Communities (23 total, 8 thin omitted)

### Community 0 - "process_study_pages"
Cohesion: 0.16
Nodes (7): process_league_new_date(), process_user_new_no_study(), _build_morning_cards(), _midnight_job_sync(), process_study_pages(), ActivityLog, AbsenceService

### Community 1 - "set_system_state"
Cohesion: 0.24
Nodes (7): get_system_state(), set_system_state(), _build_study_reminders_outbox_sync(), _base(), _init_daily_admin_reports_sync(), _init_morning_reports_sync(), SystemState

### Community 2 - "_complete_and_rollover_cycle"
Cohesion: 0.14
Nodes (8): _complete_and_rollover_cycle(), _get_all_admin_recipients_sync(), Cycle, CycleResult, generate_league_id(), GroupAdmin, GroupMessage, GroupTerm

### Community 3 - "main.py"
Cohesion: 0.06
Nodes (23): cmd_test_all_jobs(), BroadcastThrottle, _build_league_morning_cards_sync(), _dispatch_cycle_rollover(), dispatch_outbox(), midnight_job(), _rollover_league_cycle_sync(), safe_send() (+15 more)

### Community 6 - "database.py"
Cohesion: 0.12
Nodes (6): backup_database(), _backup_postgres(), _ensure_indexes(), _run_migrations(), set_sqlite_pragma(), _sync_postgres_sequences()

### Community 7 - "User"
Cohesion: 0.10
Nodes (4): User, ReportService, ScoringService, _build_weekly_task_sync()

### Community 8 - "get_db"
Cohesion: 0.13
Nodes (40): _build_global_stats_text_sync(), cmd_add_group_admin(), cmd_add_league(), cmd_archive_exclude(), cmd_archive_include(), cmd_create_group(), cmd_global_stats(), cmd_remove_group_admin() (+32 more)

### Community 10 - "DateService"
Cohesion: 0.09
Nodes (5): cmd_datetest(), cmd_export_system_logs(), _prepare_log_snapshot_sync(), user_can_log_late(), DateService

### Community 11 - "escape_md"
Cohesion: 0.16
Nodes (24): cb_broadcast_pick_league(), cb_confirm_delete_league(), cb_delete_league_prompt(), cb_em_select_group(), cb_make_user_group_admin(), cb_user_delete(), cb_view_leagues_select(), cmd_change_group_name() (+16 more)

### Community 12 - "admin_handlers.py"
Cohesion: 0.11
Nodes (20): _build_admin_help_text(), _build_cycle_history_excel_sync(), _cancel_flow(), cb_em_reset_msg(), cb_menu_excel(), cb_menu_stats(), cmd_broadcast(), cmd_edit_or_delete_leagues() (+12 more)

### Community 13 - "run_tests.py"
Cohesion: 0.10
Nodes (6): make_fsm(), MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 14 - "League"
Cohesion: 0.16
Nodes (11): cb_execute_user_move_league(), cb_view_single_league_table(), _collect_league_export_sync(), _execute_user_add_second_league_impl(), _get_user_past_days(), get_or_create_active_cycle(), init_db(), _build_single_admin_report_sync() (+3 more)

### Community 15 - "cb_user_add_second_league"
Cohesion: 0.15
Nodes (7): cb_em_reset_term(), cb_user_add_second_league(), cb_user_move_league(), _get_em_msgs_keyboard(), _get_em_terms_keyboard(), _get_league_edit_keyboard(), _get_profile_league_ids()

### Community 18 - "FSMContext"
Cohesion: 0.15
Nodes (42): cb_admin_cancel(), cb_broadcast_confirm_send(), cb_broadcast_pick_group(), cb_broadcast_target_all(), cb_broadcast_target_group(), cb_broadcast_target_league(), cb_cancel_delete_league(), cb_cancel_user_delete() (+34 more)

### Community 21 - "handlers.py"
Cohesion: 0.08
Nodes (44): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), _terms(), build_user_main_menu(), cb_confirm_cancel_league(), cb_join_league() (+36 more)

## Knowledge Gaps
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DateService` connect `DateService` to `process_study_pages`, `_complete_and_rollover_cycle`, `main.py`, `services.py`, `database.py`, `User`, `get_db`, `escape_md`, `admin_handlers.py`, `run_tests.py`, `League`, `handlers.py`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Should `_complete_and_rollover_cycle` be split into smaller, more focused modules?**
  _Cohesion score 0.1368421052631579 - nodes in this community are weakly interconnected._
- **Why does `get_db()` connect `get_db` to `process_study_pages`, `set_system_state`, `_complete_and_rollover_cycle`, `main.py`, `run_db`, `database.py`, `User`, `DateService`, `escape_md`, `admin_handlers.py`, `run_tests.py`, `League`, `cb_user_add_second_league`, `_get_admin_profile_lock`, `FSMContext`, `handlers.py`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Are the 57 inferred relationships involving `User` (e.g. with `_build_global_stats_text_sync()` and `cb_broadcast_confirm_send()`) actually correct?**
  _`User` has 57 INFERRED edges - model-reasoned connections that need verification._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06012176560121765 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `get_db` to `process_study_pages`, `_complete_and_rollover_cycle`, `main.py`, `User`, `Config`, `escape_md`, `DateService`, `run_tests.py`, `League`, `AdminStates`, `FSMContext`, `StudyStates`, `.get_term`, `handlers.py`?**
  _High betweenness centrality (0.077) - this node is a cross-community bridge._