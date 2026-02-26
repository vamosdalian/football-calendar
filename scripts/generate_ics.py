#!/usr/bin/env python3
"""Generate per-team .ics calendar files from league-level JSON data."""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "calendar"

MATCH_DURATION = timedelta(hours=2)

VTIMEZONE_CST = (
    "BEGIN:VTIMEZONE\r\n"
    "TZID:Asia/Shanghai\r\n"
    "BEGIN:STANDARD\r\n"
    "DTSTART:19700101T000000\r\n"
    "TZOFFSETFROM:+0800\r\n"
    "TZOFFSETTO:+0800\r\n"
    "TZNAME:CST\r\n"
    "END:STANDARD\r\n"
    "END:VTIMEZONE\r\n"
)


def build_event(league_id: str, team_id: str, season: int, match: dict, timezone: str) -> str:
    rnd = match["round"]
    dt_start = datetime.strptime(f'{match["date"]} {match["time"]}', "%Y-%m-%d %H:%M")
    dt_end = dt_start + MATCH_DURATION

    summary = f'{match["home"]} vs {match["away"]}'
    description = f'{season}中超联赛 第{rnd}轮'
    if match.get("note"):
        description += f'（{match["note"]}）'

    lines = [
        "BEGIN:VEVENT",
        f"UID:{league_id}-{season}-{team_id}-r{rnd:02d}@csl-calendar",
        f"DTSTART;TZID={timezone}:{dt_start:%Y%m%dT%H%M%S}",
        f"DTEND;TZID={timezone}:{dt_end:%Y%m%dT%H%M%S}",
        f"SUMMARY:{summary}",
        f"LOCATION:{match.get('venue', '')}",
        f"DESCRIPTION:{description}",
        "STATUS:CONFIRMED",
        "END:VEVENT",
    ]
    return "\r\n".join(lines) + "\r\n"


def generate_team_ics(team: str, team_id: str, season: int, league: str, league_id: str, matches: list, timezone: str) -> str:
    header = (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//CSL Calendar//CN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:PUBLISH\r\n"
        f"X-WR-CALNAME:{team} {season}赛程\r\n"
        f"X-WR-TIMEZONE:{timezone}\r\n"
    )

    events = ""
    for m in sorted(matches, key=lambda x: (x["date"], x["time"])):
        events += build_event(league_id, team_id, season, m, timezone)

    return header + VTIMEZONE_CST + events + "END:VCALENDAR\r\n"


def process_league(json_path: Path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    league = data["league"]
    league_id = data["leagueId"]
    season = data["season"]
    timezone = data.get("timezone", "Asia/Shanghai")
    teams = data.get("teams", {})

    team_matches = defaultdict(list)
    for m in data["matches"]:
        team_matches[m["home"]].append(m)
        team_matches[m["away"]].append(m)

    out_dir = OUTPUT_DIR / league_id
    out_dir.mkdir(parents=True, exist_ok=True)

    for team, matches in sorted(team_matches.items()):
        team_id = teams.get(team, team)
        ics = generate_team_ics(team, team_id, season, league, league_id, matches, timezone)
        ics_path = out_dir / f"{team}.ics"
        with open(ics_path, "w", encoding="utf-8", newline="") as f:
            f.write(ics)
        print(f"  {ics_path.relative_to(PROJECT_ROOT)}")


def main():
    for json_path in sorted(DATA_DIR.rglob("*.json")):
        print(f"Processing {json_path.relative_to(PROJECT_ROOT)}")
        process_league(json_path)


if __name__ == "__main__":
    main()
