# Graph Report - ketabkharsho-argon  (2026-11-07)

## Corpus Check
- 15 files · ~60,923 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .example 1, .bat 1)

## Summary
- 487 nodes · 2220 edges · 22 communities (14 shown, 8 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 263 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `84c1540a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- run_all_tests
- league_لیگ_ستارگان_c2_d40_20261101_002038_5c848541.md
- process_em_new_term
- _get_admin_profile_lock
- services.py
- database.py
- setup_scheduler
- Group
- User
- get_db
- league_Ndnd_c1_d1_20261107_032036_da85e3_46c94cb6.md
- get_or_create_active_cycle
- league_Test_1_c1_d1_20261107_032035_1285eb_60a9f32b.md
- cb_em_select_group
- FSMContext
- _cancel_flow
- handlers.py
- admin_handlers.py
- BaleAiohttpSession
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 112 edges
2. `run_all_tests()` - 76 edges
3. `User` - 72 edges
4. `DateService` - 69 edges
5. `League` - 66 edges
6. `escape_md()` - 66 edges
7. `is_user_admin()` - 57 edges
8. `MessageService` - 49 edges
9. `safe_send_message()` - 45 edges
10. `safe_reply()` - 45 edges

## Surprising Connections (you probably didn't know these)
- `_format_user_admin_card()` --uses--> `Group`  [INFERRED]
  admin_handlers.py → models.py
- `_format_user_admin_card()` --uses--> `League`  [INFERRED]
  admin_handlers.py → models.py
- `_format_user_admin_card()` --uses--> `User`  [INFERRED]
  admin_handlers.py → models.py
- `_format_user_admin_card()` --uses--> `AbsenceService`  [INFERRED]
  admin_handlers.py → services.py
- `_get_em_terms_keyboard()` --uses--> `MessageService`  [INFERRED]
  admin_handlers.py → message_service.py

## Import Cycles
- None detected.

## Communities (22 total, 8 thin omitted)

### Community 1 - "run_all_tests"
Cohesion: 0.07
Nodes (11): AdminStates, _build_cycle_history_excel_sync(), StudyStates, make_fsm(), MockBot, MockCallbackQuery, MockChat, MockMessage (+3 more)

### Community 3 - "process_em_new_term"
Cohesion: 0.12
Nodes (3): _get_em_terms_keyboard(), _get_profile_league_ids(), process_em_new_term()

### Community 6 - "services.py"
Cohesion: 0.11
Nodes (7): ActivityLog, Cycle, CycleResult, generate_league_id(), GroupMessage, GroupTerm, SystemState

### Community 7 - "database.py"
Cohesion: 0.16
Nodes (5): backup_database(), init_db(), _run_migrations(), set_sqlite_pragma(), GroupAdmin

### Community 8 - "setup_scheduler"
Cohesion: 0.25
Nodes (3): main(), _run_safe_job(), setup_scheduler()

### Community 9 - "Group"
Cohesion: 0.47
Nodes (4): process_cg_password(), process_pg_new_password(), is_group_password_unique(), Group

### Community 10 - "User"
Cohesion: 0.06
Nodes (7): process_league_new_date(), _complete_and_rollover_cycle(), format_league_leaderboard(), User, AbsenceService, DateService, ScoringService

### Community 11 - "get_db"
Cohesion: 0.17
Nodes (28): cb_confirm_delete_league(), cb_delete_league_prompt(), cb_em_reset_msg(), cb_em_reset_term(), cb_user_add_second_league(), cb_user_delete(), cb_user_move_league(), cb_view_leagues_select() (+20 more)

### Community 13 - "get_or_create_active_cycle"
Cohesion: 0.13
Nodes (13): cmd_test_all_jobs(), get_or_create_active_cycle(), get_system_state(), set_system_state(), midnight_job(), safe_send(), send_daily_admin_reports(), send_daily_user_reports() (+5 more)

### Community 15 - "cb_em_select_group"
Cohesion: 0.25
Nodes (4): cb_em_select_group(), _get_em_main_keyboard(), _get_em_msgs_keyboard(), _get_league_edit_keyboard()

### Community 18 - "FSMContext"
Cohesion: 0.17
Nodes (35): cb_admin_cancel(), cb_cancel_delete_league(), cb_confirm_remove_group_admin(), cb_em_edit_msg(), cb_em_edit_term(), cb_em_msgs_menu(), cb_em_terms_menu(), cb_execute_user_add_second_league() (+27 more)

### Community 19 - "_cancel_flow"
Cohesion: 0.33
Nodes (4): _build_admin_help_text(), _cancel_flow(), global_cancel_message(), show_admin_panel()

### Community 21 - "handlers.py"
Cohesion: 0.10
Nodes (43): cb_execute_user_move_league(), generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), build_user_main_menu(), cb_confirm_cancel_league(), cb_join_league() (+35 more)

### Community 29 - "admin_handlers.py"
Cohesion: 0.13
Nodes (35): cmd_add_group_admin(), cmd_add_league(), cmd_create_group(), cmd_datetest(), cmd_edit_or_delete_leagues(), cmd_export_excel(), cmd_global_stats(), cmd_group_stats() (+27 more)

## Knowledge Gaps
- **3 isolated node(s):** `Sheet: چله 1 - روز 1`, `Sheet: چله 1 - روز 1`, `Sheet: چله 2 - روز 40`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 173 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DateService` connect `User` to `run_tests.py`, `run_all_tests`, `main.py`, `services.py`, `database.py`, `Group`, `get_db`, `get_or_create_active_cycle`, `handlers.py`, `admin_handlers.py`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Sheet: چله 1 - روز 1`, `Sheet: چله 1 - روز 1`, `Sheet: چله 2 - روز 40` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `run_all_tests` be split into smaller, more focused modules?**
  _Cohesion score 0.06570048309178744 - nodes in this community are weakly interconnected._
- **Why does `User` connect `User` to `run_tests.py`, `run_all_tests`, `process_em_new_term`, `main.py`, `_get_admin_profile_lock`, `services.py`, `database.py`, `get_db`, `get_or_create_active_cycle`, `FSMContext`, `handlers.py`, `admin_handlers.py`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `User` (e.g. with `cb_confirm_delete_league()` and `cb_execute_user_move_league()`) actually correct?**
  _`User` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Should `process_em_new_term` be split into smaller, more focused modules?**
  _Cohesion score 0.11695906432748537 - nodes in this community are weakly interconnected._