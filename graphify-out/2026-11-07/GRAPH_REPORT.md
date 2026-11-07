# Graph Report - ketabkharsho-argon  (2026-11-07)

## Corpus Check
- 13 files · ~61,387 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .example 1, .bat 1)

## Summary
- 491 nodes · 2250 edges · 22 communities (13 shown, 9 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 267 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `55537e07`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- User
- MockBot
- league_لیگ_ستارگان_c2_d40_20261101_002038_5c848541.md
- escape_md
- _get_admin_profile_lock
- services.py
- database.py
- send_weekly_reports
- _complete_and_rollover_cycle
- run_all_tests
- is_user_admin
- AdminStates
- send_daily_admin_reports
- StudyStates
- cb_em_select_group
- make_fsm
- admin_handlers.py
- _cancel_flow
- handlers.py
- get_db
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 112 edges
2. `run_all_tests()` - 76 edges
3. `User` - 73 edges
4. `DateService` - 70 edges
5. `League` - 67 edges
6. `escape_md()` - 66 edges
7. `is_user_admin()` - 57 edges
8. `MessageService` - 49 edges
9. `safe_send_message()` - 45 edges
10. `safe_reply()` - 45 edges

## Surprising Connections (you probably didn't know these)
- `run_all_tests()` --uses--> `AdminStates`  [INFERRED]
  run_tests.py → admin_handlers.py
- `_get_user_past_days()` --uses--> `User`  [INFERRED]
  admin_handlers.py → models.py
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py
- `_format_user_admin_card()` --uses--> `User`  [INFERRED]
  admin_handlers.py → models.py
- `_get_em_terms_keyboard()` --uses--> `MessageService`  [INFERRED]
  admin_handlers.py → message_service.py

## Import Cycles
- None detected.

## Communities (22 total, 9 thin omitted)

### Community 1 - "MockBot"
Cohesion: 0.15
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

### Community 3 - "escape_md"
Cohesion: 0.27
Nodes (14): cb_em_edit_msg(), cb_em_edit_term(), cb_league_edit_cycle(), cb_league_edit_date(), cb_league_edit_floor(), cb_select_group_for_name(), cb_select_group_for_new_league(), cb_select_group_for_password() (+6 more)

### Community 6 - "services.py"
Cohesion: 0.13
Nodes (5): Cycle, CycleResult, generate_league_id(), GroupMessage, GroupTerm

### Community 7 - "database.py"
Cohesion: 0.18
Nodes (3): backup_database(), _run_migrations(), set_sqlite_pragma()

### Community 8 - "send_weekly_reports"
Cohesion: 0.20
Nodes (5): get_system_state(), set_system_state(), GroupAdmin, SystemState, send_weekly_reports()

### Community 10 - "run_all_tests"
Cohesion: 0.06
Nodes (27): _format_user_admin_card(), _get_user_manage_keyboard(), _get_user_past_days(), process_al_league_floor(), process_league_new_cycle(), process_league_new_date(), process_league_new_floor(), process_user_new_floor() (+19 more)

### Community 11 - "is_user_admin"
Cohesion: 0.16
Nodes (16): cb_user_add_second_league(), cb_user_move_league(), cmd_add_league(), cmd_edit_or_delete_leagues(), cmd_export_excel(), cmd_group_stats(), cmd_manage_users_list(), cmd_test_leaderboard() (+8 more)

### Community 13 - "send_daily_admin_reports"
Cohesion: 0.09
Nodes (11): cmd_test_all_jobs(), safe_send(), send_daily_admin_reports(), send_daily_user_reports(), send_study_reminders(), send_text_chunks(), BaleAiohttpSession, main() (+3 more)

### Community 15 - "cb_em_select_group"
Cohesion: 0.18
Nodes (6): cb_em_reset_term(), cb_em_select_group(), _get_em_main_keyboard(), _get_em_msgs_keyboard(), _get_em_terms_keyboard(), _get_league_edit_keyboard()

### Community 18 - "admin_handlers.py"
Cohesion: 0.18
Nodes (34): cb_admin_cancel(), cb_cancel_delete_league(), cb_confirm_delete_league(), cb_confirm_remove_group_admin(), cb_delete_league_prompt(), cb_em_msgs_menu(), cb_em_reset_msg(), cb_em_terms_menu() (+26 more)

### Community 19 - "_cancel_flow"
Cohesion: 0.40
Nodes (3): _build_admin_help_text(), _cancel_flow(), global_cancel_message()

### Community 21 - "handlers.py"
Cohesion: 0.08
Nodes (41): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), build_user_main_menu(), cb_confirm_cancel_league(), cb_join_league(), _cb_join_league_impl() (+33 more)

### Community 29 - "get_db"
Cohesion: 0.15
Nodes (30): _build_cycle_history_excel_sync(), cmd_add_group_admin(), cmd_archive_exclude(), cmd_archive_include(), cmd_change_group_password(), cmd_datetest(), cmd_edit_messages_and_terms(), cmd_export_cycle_history_excel() (+22 more)

## Knowledge Gaps
- **1 isolated node(s):** `Sheet: چله 2 - روز 40`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 172 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DateService` connect `run_all_tests` to `User`, `run_tests.py`, `services.py`, `database.py`, `send_weekly_reports`, `_complete_and_rollover_cycle`, `is_user_admin`, `send_daily_admin_reports`, `admin_handlers.py`, `handlers.py`, `get_db`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Sheet: چله 2 - روز 40` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `User` be split into smaller, more focused modules?**
  _Cohesion score 0.13230769230769232 - nodes in this community are weakly interconnected._
- **Why does `User` connect `User` to `run_tests.py`, `_get_admin_profile_lock`, `services.py`, `database.py`, `send_weekly_reports`, `_complete_and_rollover_cycle`, `run_all_tests`, `is_user_admin`, `send_daily_admin_reports`, `admin_handlers.py`, `handlers.py`, `get_db`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 48 inferred relationships involving `User` (e.g. with `cb_confirm_delete_league()` and `cb_execute_user_move_league()`) actually correct?**
  _`User` has 48 INFERRED edges - model-reasoned connections that need verification._
- **Should `run_tests.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14333333333333334 - nodes in this community are weakly interconnected._