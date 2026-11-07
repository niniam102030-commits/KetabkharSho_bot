# Graph Report - ketabkharsho-argon  (2026-11-05)

## Corpus Check
- 13 files · ~57,631 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 2, .example 1)

## Summary
- 473 nodes · 2169 edges · 19 communities (10 shown, 9 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 260 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `84c1540a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ReportService
- league_لیگ_ستارگان_c2_d40_20261101_002038_5c848541.md
- midnight_job
- main.py
- _get_em_terms_keyboard
- database.py
- models.py
- StudyStates
- run_tests.py
- AdminStates
- make_fsm
- User
- admin_handlers.py
- handlers.py
- get_db
- MockBot
- BaleAiohttpSession
- Config

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 111 edges
2. `run_all_tests()` - 76 edges
3. `User` - 70 edges
4. `DateService` - 68 edges
5. `League` - 65 edges
6. `escape_md()` - 65 edges
7. `is_user_admin()` - 56 edges
8. `MessageService` - 48 edges
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

## Communities (19 total, 9 thin omitted)

### Community 3 - "midnight_job"
Cohesion: 0.24
Nodes (7): cmd_test_all_jobs(), get_system_state(), set_system_state(), midnight_job(), send_daily_admin_reports(), send_study_reminders(), run_startup_catchups()

### Community 4 - "main.py"
Cohesion: 0.13
Nodes (3): main(), _run_safe_job(), setup_scheduler()

### Community 6 - "database.py"
Cohesion: 0.16
Nodes (4): backup_database(), init_db(), _run_migrations(), set_sqlite_pragma()

### Community 7 - "models.py"
Cohesion: 0.15
Nodes (7): ActivityLog, Cycle, CycleResult, generate_league_id(), GroupMessage, GroupTerm, SystemState

### Community 9 - "run_tests.py"
Cohesion: 0.18
Nodes (3): get_or_create_active_cycle(), GroupAdmin, send_weekly_reports()

### Community 17 - "User"
Cohesion: 0.06
Nodes (9): cmd_test_leaderboard(), _complete_and_rollover_cycle(), format_league_leaderboard(), safe_send(), send_daily_user_reports(), send_text_chunks(), User, AbsenceService (+1 more)

### Community 18 - "admin_handlers.py"
Cohesion: 0.10
Nodes (73): _build_admin_help_text(), _cancel_flow(), cb_admin_cancel(), cb_cancel_delete_league(), cb_confirm_delete_league(), cb_confirm_remove_group_admin(), cb_delete_league_prompt(), cb_em_edit_msg() (+65 more)

### Community 21 - "handlers.py"
Cohesion: 0.10
Nodes (40): generate_new_profile_id(), get_active_user(), get_user_profiles(), set_active_user_id(), build_user_main_menu(), cb_confirm_cancel_league(), cb_join_league(), cb_join_new_group_prompt() (+32 more)

### Community 29 - "get_db"
Cohesion: 0.10
Nodes (42): cmd_add_group_admin(), cmd_archive_exclude(), cmd_archive_include(), cmd_create_group(), cmd_datetest(), cmd_export_cycle_history_excel(), cmd_global_stats(), cmd_remove_group_admin() (+34 more)

### Community 58 - "MockBot"
Cohesion: 0.15
Nodes (5): MockBot, MockCallbackQuery, MockChat, MockMessage, MockUser

## Knowledge Gaps
- **1 isolated node(s):** `Sheet: چله 2 - روز 40`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 164 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DateService` connect `get_db` to `services.py`, `ReportService`, `midnight_job`, `main.py`, `database.py`, `run_tests.py`, `User`, `admin_handlers.py`, `handlers.py`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 12 inferred relationships involving `run_all_tests()` (e.g. with `AdminStates` and `StudyStates`) actually correct?**
  _`run_all_tests()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Sheet: چله 2 - روز 40` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12631578947368421 - nodes in this community are weakly interconnected._
- **Why does `run_all_tests()` connect `get_db` to `ReportService`, `midnight_job`, `_get_em_terms_keyboard`, `database.py`, `models.py`, `StudyStates`, `run_tests.py`, `AdminStates`, `make_fsm`, `User`, `admin_handlers.py`, `handlers.py`, `MockBot`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `User` (e.g. with `cb_confirm_delete_league()` and `cb_execute_user_add_second_league()`) actually correct?**
  _`User` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Should `_get_em_terms_keyboard` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._