# Graph Report - ketabkharsho-argon  (2026-11-06)

## Corpus Check
- 13 files · ~60,714 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .example 1, .bat 1)

## Summary
- 483 nodes · 2217 edges · 20 communities (14 shown, 6 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 263 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `84c1540a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_tests.py
- User
- league_لیگ_ستارگان_c2_d40_20261101_002038_5c848541.md
- handlers.py
- main.py
- _get_admin_profile_lock
- database.py
- set_sqlite_pragma
- DateService
- escape_md
- AdminStates
- _complete_and_rollover_cycle
- cb_em_select_group
- FSMContext
- _cancel_flow
- run_all_tests
- admin_handlers.py
- MockBot
- BaleAiohttpSession
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 112 edges
2. `run_all_tests()` - 76 edges
3. `User` - 72 edges
4. `DateService` - 69 edges
5. `League` - 66 edges
6. `escape_md()` - 65 edges
7. `is_user_admin()` - 57 edges
8. `MessageService` - 49 edges
9. `safe_send_message()` - 45 edges
10. `safe_reply()` - 45 edges

## Surprising Connections (you probably didn't know these)
- `run_all_tests()` --uses--> `AdminStates`  [INFERRED]
  run_tests.py → admin_handlers.py
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py
- `_format_user_admin_card()` --uses--> `League`  [INFERRED]
  admin_handlers.py → models.py
- `_format_user_admin_card()` --uses--> `User`  [INFERRED]
  admin_handlers.py → models.py
- `_format_user_admin_card()` --uses--> `AbsenceService`  [INFERRED]
  admin_handlers.py → services.py

## Import Cycles
- None detected.

## Communities (20 total, 6 thin omitted)

### Community 0 - "run_tests.py"
Cohesion: 0.10
Nodes (3): StudyStates, ActivityLog, CycleResult

### Community 1 - "User"
Cohesion: 0.09
Nodes (7): _build_cycle_history_excel_sync(), cmd_export_excel(), _send_active_leagues_excel(), format_league_leaderboard(), User, ReportService, ScoringService

### Community 3 - "handlers.py"
Cohesion: 0.17
Nodes (4): get_cancel_league_confirm(), get_main_menu(), get_profile_switch_keyboard(), get_study_edit_menu()

### Community 4 - "main.py"
Cohesion: 0.12
Nodes (4): send_startup_notification(), main(), _run_safe_job(), setup_scheduler()

### Community 6 - "database.py"
Cohesion: 0.11
Nodes (9): backup_database(), init_db(), _run_migrations(), Cycle, generate_league_id(), GroupAdmin, GroupMessage, GroupTerm (+1 more)

### Community 10 - "DateService"
Cohesion: 0.07
Nodes (6): cmd_datetest(), process_league_new_date(), get_or_create_active_cycle(), _send_daily_user_reports_impl(), AbsenceService, DateService

### Community 11 - "escape_md"
Cohesion: 0.14
Nodes (25): cb_confirm_delete_league(), cb_execute_user_move_league(), cb_menu_stats(), cb_user_add_second_league(), cb_user_move_league(), cb_view_leagues_select(), cmd_add_league(), cmd_change_group_name() (+17 more)

### Community 13 - "_complete_and_rollover_cycle"
Cohesion: 0.14
Nodes (12): cmd_test_all_jobs(), get_system_state(), set_system_state(), _complete_and_rollover_cycle(), midnight_job(), safe_send(), send_daily_admin_reports(), send_daily_user_reports() (+4 more)

### Community 15 - "cb_em_select_group"
Cohesion: 0.17
Nodes (6): cb_em_reset_term(), cb_em_select_group(), _get_em_main_keyboard(), _get_em_msgs_keyboard(), _get_em_terms_keyboard(), _get_league_edit_keyboard()

### Community 18 - "FSMContext"
Cohesion: 0.15
Nodes (39): cb_admin_cancel(), cb_cancel_delete_league(), cb_confirm_remove_group_admin(), cb_delete_league_prompt(), cb_em_edit_msg(), cb_em_edit_term(), cb_em_msgs_menu(), cb_em_reset_msg() (+31 more)

### Community 19 - "_cancel_flow"
Cohesion: 0.29
Nodes (5): _build_admin_help_text(), _cancel_flow(), global_cancel_message(), show_admin_panel(), get_admin_main_inline_menu()

### Community 21 - "run_all_tests"
Cohesion: 0.10
Nodes (38): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), build_user_main_menu(), cb_confirm_cancel_league(), cb_join_league(), _cb_join_league_impl() (+30 more)

### Community 29 - "admin_handlers.py"
Cohesion: 0.16
Nodes (37): cmd_add_group_admin(), cmd_archive_exclude(), cmd_archive_include(), cmd_create_group(), cmd_export_cycle_history_excel(), cmd_global_stats(), cmd_manage_users_list(), cmd_remove_group_admin() (+29 more)

### Community 58 - "MockBot"
Cohesion: 0.15
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

## Knowledge Gaps
- **1 isolated node(s):** `Sheet: چله 2 - روز 40`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 169 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DateService` connect `DateService` to `run_tests.py`, `User`, `handlers.py`, `main.py`, `database.py`, `escape_md`, `_complete_and_rollover_cycle`, `FSMContext`, `run_all_tests`, `admin_handlers.py`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Sheet: چله 2 - روز 40` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `run_tests.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10333333333333333 - nodes in this community are weakly interconnected._
- **Why does `User` connect `User` to `run_tests.py`, `handlers.py`, `_get_admin_profile_lock`, `database.py`, `DateService`, `escape_md`, `_complete_and_rollover_cycle`, `FSMContext`, `run_all_tests`, `admin_handlers.py`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `User` (e.g. with `cb_confirm_delete_league()` and `cb_execute_user_move_league()`) actually correct?**
  _`User` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Should `User` be split into smaller, more focused modules?**
  _Cohesion score 0.0858974358974359 - nodes in this community are weakly interconnected._