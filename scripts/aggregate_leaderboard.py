#!/usr/bin/env python3
import json
import sys
from datetime import datetime
from pathlib import Path
import pytz

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "leaderboard" / "runs"
OUT_JSON = ROOT / "leaderboard" / "leaderboard.json"
OUT_MD = ROOT / "leaderboard" / "leaderboard.md"


def load_runs():
    """Expect structure: leaderboard/runs/<team>/<pipeline_id>/{score_report.json, metadata.json}"""
    data = {}
    for team_dir in RUNS_DIR.glob("*"):
        if not team_dir.is_dir():
            continue
        team = team_dir.name
        entries = []
        for run_dir in team_dir.glob("*"):
            sr = run_dir / "score_report.json"
            md = run_dir / "metadata.json"
            if sr.exists() and md.exists():
                try:
                    score = json.loads(sr.read_text())
                    meta = json.loads(md.read_text())
                    ts = meta.get("timestamp_utc")
                    ts_dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ") if ts else None
                    entries.append((ts_dt, score, meta))
                except Exception:
                    pass
        if entries:
            entries.sort(key=lambda x: x[0] or datetime.min, reverse=True)
            data[team] = entries
    return data


def utc_to_cst(utc_timestamp):
    """Convert UTC timestamp string to CST timezone"""
    if not utc_timestamp:
        return None
    try:
        utc_dt = datetime.strptime(utc_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        utc_dt = pytz.utc.localize(utc_dt)
        cst_tz = pytz.timezone('America/Chicago')
        cst_dt = utc_dt.astimezone(cst_tz)
        return cst_dt.strftime("%Y-%m-%d %H:%M:%S CST")
    except Exception:
        return utc_timestamp


def pick_latest_per_team(data):
    latest = {}
    for team, entries in data.items():
        # Sort entries by timestamp to ensure we get the latest one
        sorted_entries = sorted(entries, key=lambda x: x[0] or datetime.min, reverse=True)
        _, score, meta = sorted_entries[0]
        
        # Handle optional real scores
        real_scores = score.get("real")
        if real_scores is not None:
            real_ndcg10 = real_scores["nDCG@10"]
            real_ap20 = real_scores["AP@20"] 
            real_p10 = real_scores["P@10"]
            real_r30 = real_scores["R@30"]
            real_composite = real_scores["composite"]
            queries_scored_real = real_scores["queries_scored"]
        else:
            real_ndcg10 = None
            real_ap20 = None
            real_p10 = None
            real_r30 = None
            real_composite = None
            queries_scored_real = None
        
        # Get synthetic scores
        synth_scores = score["synthetic"]
        synth_ndcg10 = synth_scores["nDCG@10"]
        synth_ap20 = synth_scores["AP@20"]
        synth_p10 = synth_scores["P@10"]
        synth_r30 = synth_scores["R@30"]
        synth_composite = synth_scores["composite"]
        
        latest[team] = {
            "team": team,
            "weighted_final": score["combined"]["weighted_final"],
            "real_nDCG@10": real_ndcg10,
            "real_AP@20": real_ap20,
            "real_P@10": real_p10,
            "real_R@30": real_r30,
            "real_composite": real_composite,
            "synth_nDCG@10": synth_ndcg10,
            "synth_AP@20": synth_ap20,
            "synth_P@10": synth_p10,
            "synth_R@30": synth_r30,
            "synth_composite": synth_composite,
            "queries_scored_real": queries_scored_real,
            "queries_scored_synth": score["synthetic"]["queries_scored"],
            "pipeline_id": meta.get("pipeline_id"),
            "commit_sha": meta.get("commit_sha"),
            "timestamp_utc": meta.get("timestamp_utc"),
            "timestamp_cst": utc_to_cst(meta.get("timestamp_utc")),
        }
    # Sort for display
    rows = list(latest.values())
    rows.sort(key=lambda r: r["weighted_final"], reverse=True)
    return rows


def to_markdown(rows):
    lines = []
    lines.append("# :trophy: TAMU-25 Leaderboard\n")
    lines.append("| Rank | Team | Final | Real nDCG@10 | Real AP@20 | Real P@10 | Real R@30 | Real Composite | Synth nDCG@10 | Synth AP@20 | Synth P@10 | Synth R@30 | Synth Composite | Pipeline | Timestamp (CST) |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
    for i, r in enumerate(rows, start=1):
        # Format real scores
        real_ndcg = f"{r['real_nDCG@10']:.3f}" if r['real_nDCG@10'] is not None else "N/A"
        real_ap = f"{r['real_AP@20']:.3f}" if r['real_AP@20'] is not None else "N/A"
        real_p = f"{r['real_P@10']:.3f}" if r['real_P@10'] is not None else "N/A"
        real_r = f"{r['real_R@30']:.3f}" if r['real_R@30'] is not None else "N/A"
        real_comp = f"{r['real_composite']:.3f}" if r['real_composite'] is not None else "N/A"
        
        # Format synthetic scores
        synth_ndcg = f"{r['synth_nDCG@10']:.3f}"
        synth_ap = f"{r['synth_AP@20']:.3f}"
        synth_p = f"{r['synth_P@10']:.3f}"
        synth_r = f"{r['synth_R@30']:.3f}"
        synth_comp = f"{r['synth_composite']:.3f}"
        
        timestamp_display = r['timestamp_cst'] or r['timestamp_utc'] or "N/A"
        lines.append(
            f"| {i} | {r['team']} | {r['weighted_final']:.3f} | {real_ndcg} | {real_ap} | {real_p} | {real_r} | {real_comp} | {synth_ndcg} | {synth_ap} | {synth_p} | {synth_r} | {synth_comp} | {r['pipeline_id']} | {timestamp_display} |"
        )
    return "\n".join(lines) + "\n"


def main():
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    data = load_runs()
    rows = pick_latest_per_team(data)
    OUT_JSON.write_text(json.dumps({"rows": rows}, indent=2), encoding="utf-8")
    OUT_MD.write_text(to_markdown(rows), encoding="utf-8")
    print(json.dumps({"teams": len(rows)}, indent=2))


if __name__ == "__main__":
    sys.exit(main())
