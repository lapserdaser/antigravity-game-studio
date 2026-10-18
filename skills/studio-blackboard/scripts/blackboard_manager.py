#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Studio Blackboard Engine Manager (blackboard_manager.py)
Zero-token state manager for the Lean Multi-Agent Game Studio.
Enforces structured state, atomic mutations, and schema validation.
"""

import sys
import os
import json
import argparse
from typing import Dict, Any, List

# Ensure safe UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_STATE_FILE = os.path.join(os.getcwd(), "scratch", "session_blackboard.json")

SCHEMA_VERSION = "studio_blackboard_v1"

def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    if not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)

def load_state(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        print(f"[ERROR] State file does not exist: {filepath}", file=sys.stderr)
        sys.exit(1)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to parse state JSON: {e}", file=sys.stderr)
        sys.exit(1)

def save_state(filepath: str, data: Dict[str, Any]) -> None:
    ensure_parent_dir(filepath)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save state JSON: {e}", file=sys.stderr)
        sys.exit(1)

def cmd_init(args) -> None:
    invariants = [inv.strip() for inv in args.invariants.split(";") if inv.strip()] if args.invariants else []
    state = {
        "$schema": SCHEMA_VERSION,
        "request_id": args.request_id or "req-latest",
        "goal": args.goal,
        "tier": args.tier or "Tier 2",
        "invariants": invariants,
        "actors_trace": {
            "current_turn": args.first_turn or "gameplay_dev",
            "history": ["lead_orchestrator"],
            "iteration_count": 0,
            "max_iterations": args.max_iterations or 2
        },
        "task_contract": {
            "assigned_to": args.first_turn or "gameplay_dev",
            "instructions": args.instructions or args.goal,
            "target_files": [f.strip() for f in args.targets.split(",") if f.strip()] if args.targets else []
        },
        "artifacts": {
            "target_file": "",
            "changed_lines": [],
            "diff_summary": ""
        },
        "qa_matrix": {
            "verdict": "PENDING",
            "tests_run": [],
            "edge_cases_checked": [],
            "issues": []
        }
    }
    save_state(args.file, state)
    print(f"[OK] Initialized Blackboard at {args.file} (Turn: {state['actors_trace']['current_turn']})")

def cmd_set_artifact(args) -> None:
    state = load_state(args.file)
    state["artifacts"]["target_file"] = args.target_file
    state["artifacts"]["diff_summary"] = args.diff_summary
    if args.changed_lines:
        try:
            state["artifacts"]["changed_lines"] = [int(x.strip()) for x in args.changed_lines.split(",") if x.strip()]
        except ValueError:
            state["artifacts"]["changed_lines"] = [args.changed_lines]
    
    # Update actor trace
    curr = state["actors_trace"]["current_turn"]
    if curr not in state["actors_trace"]["history"]:
        state["actors_trace"]["history"].append(curr)
    
    # Handover to next turn (usually qa_challenger)
    next_turn = args.next_turn or "qa_challenger"
    state["actors_trace"]["current_turn"] = next_turn
    state["task_contract"]["assigned_to"] = next_turn
    state["task_contract"]["instructions"] = f"Verify changes in {args.target_file}. Diff: {args.diff_summary}"
    
    save_state(args.file, state)
    print(f"[OK] Artifact updated. Handover to -> {next_turn}")

def cmd_set_verdict(args) -> None:
    state = load_state(args.file)
    verdict = args.verdict.upper()
    if verdict not in ["APPROVED", "REJECTED"]:
        print("[ERROR] Verdict must be APPROVED or REJECTED", file=sys.stderr)
        sys.exit(1)
    
    state["qa_matrix"]["verdict"] = verdict
    if args.edge_cases:
        state["qa_matrix"]["edge_cases_checked"] = [ec.strip() for ec in args.edge_cases.split(";") if ec.strip()]
    if args.issues:
        state["qa_matrix"]["issues"] = [iss.strip() for iss in args.issues.split(";") if iss.strip()]
    
    curr = state["actors_trace"]["current_turn"]
    if curr not in state["actors_trace"]["history"]:
        state["actors_trace"]["history"].append(curr)
    
    state["actors_trace"]["iteration_count"] += 1
    
    if verdict == "APPROVED":
        state["actors_trace"]["current_turn"] = "lead_orchestrator"
        print(f"[OK] QA VERDICT: APPROVED. Task ready for final handover to user.")
    else:
        max_iter = state["actors_trace"].get("max_iterations", 2)
        if state["actors_trace"]["iteration_count"] >= max_iter:
            state["actors_trace"]["current_turn"] = "lead_orchestrator"
            print(f"[WARN] QA REJECTED but max iterations ({max_iter}) reached. Escalate to user.")
        else:
            state["actors_trace"]["current_turn"] = "gameplay_dev"
            state["task_contract"]["assigned_to"] = "gameplay_dev"
            state["task_contract"]["instructions"] = f"Fix QA issues: {args.issues}"
            print(f"[WARN] QA REJECTED. Handover back to gameplay_dev (Iteration {state['actors_trace']['iteration_count']}/{max_iter})")
            
    save_state(args.file, state)

def cmd_status(args) -> None:
    state = load_state(args.file)
    print("=" * 60)
    print(f"[GOAL] {state.get('goal')}")
    print(f"[CURRENT TURN] {state['actors_trace'].get('current_turn')}")
    print(f"[INVARIANTS] ({len(state.get('invariants', []))} rules)")
    for inv in state.get("invariants", []):
        print(f"   * {inv}")
    print(f"[TARGET ARTIFACT] {state['artifacts'].get('target_file', 'None')}")
    print(f"[DIFF SUMMARY] {state['artifacts'].get('diff_summary', 'None')}")
    print(f"[QA VERDICT] {state['qa_matrix'].get('verdict', 'PENDING')}")
    if state["qa_matrix"].get("issues"):
        print(f"[QA ISSUES] {state['qa_matrix']['issues']}")
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Studio Blackboard Engine Manager")
    parser.add_argument("--file", default=DEFAULT_STATE_FILE, help="Path to state file")
    
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    
    # init
    p_init = subparsers.add_parser("init")
    p_init.add_argument("--goal", required=True, help="Task goal")
    p_init.add_argument("--invariants", default="", help="Semicolon-separated invariants")
    p_init.add_argument("--targets", default="", help="Comma-separated target files")
    p_init.add_argument("--first-turn", default="gameplay_dev")
    p_init.add_argument("--instructions", default="")
    p_init.add_argument("--tier", default="Tier 2")
    p_init.add_argument("--request-id", default="")
    p_init.add_argument("--max-iterations", type=int, default=2)
    p_init.set_defaults(func=cmd_init)
    
    # set-artifact
    p_art = subparsers.add_parser("set-artifact")
    p_art.add_argument("--target-file", required=True)
    p_art.add_argument("--diff-summary", required=True)
    p_art.add_argument("--changed-lines", default="")
    p_art.add_argument("--next-turn", default="qa_challenger")
    p_art.set_defaults(func=cmd_set_artifact)
    
    # set-verdict
    p_ver = subparsers.add_parser("set-verdict")
    p_ver.add_argument("--verdict", required=True, choices=["APPROVED", "REJECTED", "approved", "rejected"])
    p_ver.add_argument("--edge-cases", default="", help="Semicolon-separated edge cases checked")
    p_ver.add_argument("--issues", default="", help="Semicolon-separated issues found")
    p_ver.set_defaults(func=cmd_set_verdict)
    
    # status
    p_stat = subparsers.add_parser("status")
    p_stat.set_defaults(func=cmd_status)
    
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
