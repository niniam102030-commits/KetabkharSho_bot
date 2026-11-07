# Graph Report - ketabkharsho-argon  (2026-11-07)

## Corpus Check
- 13 files · ~63,540 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .example 1, .bat 1)

## Summary
- 529 nodes · 2344 edges · 19 communities (12 shown, 7 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 283 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `55537e07`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ReportService
- run_tests.py
- league_لیگ_ستارگان_c2_d40_20261101_002038_5c848541.md
- scheduler.py
- main.py
- _get_admin_profile_lock
- services.py
- database.py
- send_weekly_reports
- User
- escape_md
- midnight_job
- cb_em_select_group
- FSMContext
- admin_handlers.py
- handlers.py
- get_db
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 114 edges
2. `run_all_tests()` - 76 edges
3. `User` - 74 edges
4. `DateService` - 72 edges
5. `League` - 70 edges
6. `escape_md()` - 66 edges
7. `is_user_admin()` - 57 edges
8. `MessageService` - 49 edges
9. `safe_send_message()` - 45 edges
10. `safe_reply()` - 45 edges

## Surprising Connections (you probably didn't know these)
- `run_all_tests()` --uses--> `AdminStates`  [INFERRED]
  run_tests.py → admin_handlers.py
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py
- `_get_em_terms_keyboard()` --uses--> `MessageService`  [INFERRED]
  admin_handlers.py → message_service.py
- `process_cg_password()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py
- `process_cg_password()` --uses--> `DateService`  [INFERRED]
  admin_handlers.py → services.py

## Import Cycles
- None detected.

## Communities (19 total, 7 thin omitted)

### Community 1 - "run_tests.py"
Cohesion: 0.07
Nodes (9): AdminStates, StudyStates, CycleResult, make_fsm(), MockBot, MockCallbackQuery, MockChat, MockMessage (+1 more)

### Community 6 - "services.py"
Cohesion: 0.15
Nodes (3): generate_league_id(), GroupMessage, GroupTerm

### Community 7 - "database.py"
Cohesion: 0.12
Nodes (6): backup_database(), _backup_postgres(), _ensure_indexes(), _run_migrations(), set_sqlite_pragma(), _sync_postgres_sequences()

### Community 8 - "send_weekly_reports"
Cohesion: 0.27
Nodes (4): BroadcastThrottle, safe_send_document(), send_weekly_reports(), _deliver()

### Community 10 - "User"
Cohesion: 0.05
Nodes (29): _collect_league_export_sync(), _format_user_admin_card(), _get_user_manage_keyboard(), _get_user_past_days(), process_league_new_date(), process_user_new_floor(), process_user_new_late(), process_user_new_minutes() (+21 more)

### Community 11 - "escape_md"
Cohesion: 0.16
Nodes (22): cb_execute_user_move_league(), cb_make_user_group_admin(), cb_menu_stats(), cb_user_add_second_league(), cb_user_move_league(), cb_view_leagues_select(), cmd_change_group_name(), cmd_change_group_password() (+14 more)

### Community 13 - "midnight_job"
Cohesion: 0.15
Nodes (11): cmd_test_all_jobs(), get_system_state(), set_system_state(), dispatch_outbox(), midnight_job(), send_daily_admin_reports(), send_daily_user_reports(), send_study_reminders() (+3 more)

### Community 15 - "cb_em_select_group"
Cohesion: 0.17
Nodes (6): cb_em_reset_term(), cb_em_select_group(), _get_em_main_keyboard(), _get_em_msgs_keyboard(), _get_em_terms_keyboard(), _get_league_edit_keyboard()

### Community 18 - "FSMContext"
Cohesion: 0.19
Nodes (33): cb_admin_cancel(), cb_cancel_delete_league(), cb_confirm_delete_league(), cb_confirm_remove_group_admin(), cb_delete_league_prompt(), cb_em_edit_msg(), cb_em_edit_term(), cb_em_msgs_menu() (+25 more)

### Community 19 - "admin_handlers.py"
Cohesion: 0.16
Nodes (15): _build_admin_help_text(), _cancel_flow(), cb_em_reset_msg(), cb_execute_user_add_second_league(), cb_menu_excel(), cb_view_single_league_table(), cmd_edit_or_delete_leagues(), cmd_export_excel() (+7 more)

### Community 21 - "handlers.py"
Cohesion: 0.07
Nodes (44): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), build_user_main_menu(), cb_confirm_cancel_league(), cb_join_league(), _cb_join_league_impl() (+36 more)

### Community 29 - "get_db"
Cohesion: 0.13
Nodes (34): _build_cycle_history_excel_sync(), cmd_add_group_admin(), cmd_add_league(), cmd_archive_exclude(), cmd_archive_include(), cmd_create_group(), cmd_datetest(), cmd_export_cycle_history_excel() (+26 more)

## Knowledge Gaps
- **1 isolated node(s):** `Sheet: چله 2 - روز 40`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 189 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DateService` connect `User` to `ReportService`, `run_tests.py`, `main.py`, `services.py`, `database.py`, `send_weekly_reports`, `escape_md`, `midnight_job`, `admin_handlers.py`, `handlers.py`, `get_db`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Sheet: چله 2 - روز 40` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `run_tests.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06890756302521009 - nodes in this community are weakly interconnected._
- **Why does `User` connect `User` to `ReportService`, `run_tests.py`, `_get_admin_profile_lock`, `services.py`, `database.py`, `escape_md`, `midnight_job`, `FSMContext`, `admin_handlers.py`, `handlers.py`, `get_db`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `User` (e.g. with `cb_confirm_delete_league()` and `cb_execute_user_move_league()`) actually correct?**
  _`User` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Should `database.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12105263157894737 - nodes in this community are weakly interconnected._