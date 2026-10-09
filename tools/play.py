#!/usr/bin/env python3
"""Google Play from the command line: releases, notes, promotion, listing art, vitals.

Replaces EAS submit and most Console clicking. Any app works once three variables are
set, e.g. in the project's .envrc:

    PLAY_PACKAGE=com.example.app
    PLAY_TRACK="Example Beta"        # the closed testing track's display name, not its id
    PLAY_ACCOUNT=play-api@example.iam.gserviceaccount.com

Auth goes through gcloud rather than the key file directly: signing our own JWT
means writing the private key to disk, and the key stays sealed this way. Once per
machine, and the service account needs access in Play Console > Users and permissions:

    gcloud auth activate-service-account --key-file=<service-account.json>

    ./play.py tracks
    ./play.py testers
    ./play.py vitals --days 14
    ./play.py errors --days 14
    ./play.py installs ~/Downloads/installs_com.example.app_202609_overview.csv
    ./play.py notes 22 release-notes.txt
    ./play.py upload app.aab
    ./play.py apk 41 app.apk
    ./play.py release app.aab release-notes.txt
    ./play.py release 41 release-notes.txt
    ./play.py promote 42
    ./play.py promote 42 --rollout 20
    ./play.py icon docs/brand/lockups/play-icon.png
    ./play.py art --feature docs/brand/store/png/feature.png docs/brand/store/png/phone-*.png
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

PACKAGE = os.environ.get("PLAY_PACKAGE", "")
PRODUCTION = "production"
TESTING = os.environ.get("PLAY_TRACK", "")
ACCOUNT = os.environ.get("PLAY_ACCOUNT", "")
PUBLISHER = "https://androidpublisher.googleapis.com/androidpublisher/v3"
UPLOAD = "https://androidpublisher.googleapis.com/upload/androidpublisher/v3"
REPORTING = "https://playdeveloperreporting.googleapis.com/v1beta1"

# Vitals timestamps are anchored to this zone, not ours.
REPORT_TZ = "America/Los_Angeles"


def token(scope):
    out = subprocess.run(
        ["gcloud", "auth", "print-access-token", f"--account={ACCOUNT}", f"--scopes={scope}"],
        capture_output=True,
        text=True,
    )
    if out.returncode:
        sys.exit(f"gcloud: {out.stderr.strip().splitlines()[-1]}")
    return out.stdout.strip()


def call(url, scope, body=None, method=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        method=method or ("POST" if body is not None else "GET"),
        headers={"Authorization": f"Bearer {token(scope)}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or "{}")


def publisher(path, **kw):
    return call(f"{PUBLISHER}/applications/{PACKAGE}{path}", "https://www.googleapis.com/auth/androidpublisher", **kw)


def reporting(path, **kw):
    return call(f"{REPORTING}/apps/{PACKAGE}{path}", "https://www.googleapis.com/auth/playdeveloperreporting", **kw)


def commit(edit_id):
    """Commits an edit. While the app has a rejected update, Play refuses to send
    changes for review on its own; they are committed anyway and wait for
    "Send changes for review" in the Console."""
    res = publisher(f"/edits/{edit_id}:commit", body={})
    if "changesNotSentForReview" in res.get("error", {}).get("message", ""):
        res = publisher(f"/edits/{edit_id}:commit?changesNotSentForReview=true", body={})
        if "error" not in res:
            print("committed; send it for review from Publishing overview in the Console")
    return res


def with_edit(fn):
    """Publisher reads need a throwaway edit, and leaving them open blocks later ones."""
    edit = publisher("/edits", body={})
    if "id" not in edit:
        sys.exit(json.dumps(edit.get("error", edit), indent=2))
    try:
        return fn(edit["id"])
    finally:
        publisher(f"/edits/{edit['id']}", method="DELETE")


def day(d):
    return {"year": d.year, "month": d.month, "day": d.day, "timeZone": {"id": REPORT_TZ}}


def window(days):
    # Vitals lag a day; asking past freshness is a 400, not an empty result.
    end = date.today() - timedelta(days=1)
    return day(end - timedelta(days=days)), day(end)


def cmd_tracks(args):
    def show(edit_id):
        for t in publisher(f"/edits/{edit_id}/tracks").get("tracks", []):
            for r in t.get("releases", []):
                notes = "notes" if r.get("releaseNotes") else "NO NOTES"
                share = f" {r['userFraction']:.0%}" if "userFraction" in r else ""
                print(f"{t['track']:<20} {r.get('status'):<10} vc{','.join(r.get('versionCodes', []))} {r.get('name','')} [{notes}]{share}")

    with_edit(show)


def cmd_testers(args):
    def show(edit_id):
        for t in publisher(f"/edits/{edit_id}/tracks").get("tracks", []):
            groups = publisher(f"/edits/{edit_id}/testers/{t['track'].replace(' ', '%20')}").get("googleGroups", [])
            print(f"{t['track']:<20} {', '.join(groups) if groups else 'no group attached'}")

    with_edit(show)


def cmd_vitals(args):
    start, end = window(args.days)
    for name, metrics in (
        ("crashRateMetricSet", ["crashRate", "distinctUsers"]),
        ("anrRateMetricSet", ["anrRate", "distinctUsers"]),
    ):
        res = reporting(
            f"/{name}:query",
            body={
                "timelineSpec": {"aggregationPeriod": "DAILY", "startTime": start, "endTime": end},
                "metrics": metrics,
                "pageSize": 100,
            },
        )
        if "error" in res:
            print(f"{name}: {res['error'].get('message','')[:120]}")
            continue
        rows = res.get("rows", [])
        print(f"\n{name}  ({len(rows)} days with data)")
        for row in rows:
            s = row["startTime"]
            vals = {m["metric"]: m.get("decimalValue", {}).get("value") for m in row.get("metrics", [])}
            print(f"  {s['year']}-{s['month']:02d}-{s['day']:02d}  " + "  ".join(f"{k}={v}" for k, v in vals.items()))
        if not rows:
            # Vitals only sees devices where the user turned on Usage and diagnostics
            # sharing. With a dozen testers, a few opting out suppresses everything, so
            # empty here is not evidence that nobody opened the app. Installs and active
            # devices in the bulk report bucket are not gated that way; use those.
            print("  no data. vitals only counts testers who share usage and diagnostics,")
            print("  so this can be empty while the app is in daily use.")


def cmd_errors(args):
    start, end = window(args.days)
    res = reporting(
        "/errorCountMetricSet:query",
        body={
            "timelineSpec": {"aggregationPeriod": "DAILY", "startTime": start, "endTime": end},
            "dimensions": ["reportType"],
            "metrics": ["errorReportCount", "distinctUsers"],
            "pageSize": 100,
        },
    )
    if "error" in res:
        sys.exit(res["error"].get("message", ""))
    rows = res.get("rows", [])
    print(f"error reports over {args.days} days: {len(rows)} rows")
    for row in rows:
        s = row["startTime"]
        kind = next((d.get("stringValue") for d in row.get("dimensions", [])), "?")
        vals = {m["metric"]: m.get("decimalValue", {}).get("value") for m in row.get("metrics", [])}
        print(f"  {s['year']}-{s['month']:02d}-{s['day']:02d}  {kind}  {vals}")


def read_notes(path):
    text = open(path).read().strip()
    if len(text) > 500:
        sys.exit(f"Play caps release notes at 500 characters; this is {len(text)}")
    return text


def cmd_notes(args):
    # eas submit cannot set "What's new". Every track holding the build gets the
    # same text, so testers and users never read two versions of one release.
    text = read_notes(args.file)

    edit = publisher("/edits", body={})
    if "id" not in edit:
        sys.exit(json.dumps(edit.get("error", edit), indent=2))
    edit_id = edit["id"]
    try:
        lang = publisher(f"/edits/{edit_id}/details").get("defaultLanguage", "en-US")
        updated = []
        for name in (PRODUCTION, TESTING):
            path = f"/edits/{edit_id}/tracks/{urllib.parse.quote(name)}"
            track = publisher(path)
            release = next(
                (r for r in track.get("releases", []) if args.version_code in r.get("versionCodes", [])),
                None,
            )
            if not release:
                continue
            release["releaseNotes"] = [{"language": lang, "text": text}]
            res = publisher(path, body=track, method="PUT")
            if "error" in res:
                sys.exit(res["error"].get("message", ""))
            updated.append(name)
        if not updated:
            sys.exit(f"vc{args.version_code} is on neither {PRODUCTION} nor {TESTING}")

        res = commit(edit_id)
        if "error" in res:
            sys.exit(res["error"].get("message", ""))
        edit_id = None
        print(f"vc{args.version_code} on {', '.join(updated)}: {len(text)} characters of {lang} notes committed")
    finally:
        # A committed edit no longer exists; only an abandoned one needs closing.
        if edit_id:
            publisher(f"/edits/{edit_id}", method="DELETE")


def upload_bundle(edit_id, aab):
    with open(aab, "rb") as f:
        req = urllib.request.Request(
            f"{UPLOAD}/applications/{PACKAGE}/edits/{edit_id}/bundles?uploadType=media",
            data=f.read(),
            method="POST",
            headers={
                "Authorization": f"Bearer {token('https://www.googleapis.com/auth/androidpublisher')}",
                "Content-Type": "application/octet-stream",
            },
        )
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            vc = str(json.loads(r.read())["versionCode"])
    except urllib.error.HTTPError as e:
        sys.exit(json.loads(e.read() or "{}").get("error", {}).get("message", str(e)))
    print(f"uploaded vc{vc}")
    return vc


def cmd_upload(args):
    # Into the bundle library and no further: no tester sees it until `release`
    # puts its version code on the testing track. Lets `apk` fetch the build Play
    # will actually ship before anyone gets it.
    edit = publisher("/edits", body={})
    if "id" not in edit:
        sys.exit(json.dumps(edit.get("error", edit), indent=2))
    edit_id = edit["id"]
    try:
        upload_bundle(edit_id, args.aab)
        res = commit(edit_id)
        if "error" in res:
            sys.exit(res["error"].get("message", ""))
        edit_id = None
    finally:
        if edit_id:
            publisher(f"/edits/{edit_id}", method="DELETE")


def cmd_apk(args):
    # Signed with the Play app signing key, so it installs over a Play copy as an
    # update and native Google sign-in accepts it. A locally signed APK has the
    # upload key, which forces an uninstall first.
    listing = call(f"{PUBLISHER}/applications/{PACKAGE}/generatedApks/{args.version_code}",
                   "https://www.googleapis.com/auth/androidpublisher")
    if "error" in listing:
        sys.exit(listing["error"].get("message", ""))
    universal = next((g["generatedUniversalApk"] for g in listing.get("generatedApks", [])
                      if "generatedUniversalApk" in g), None)
    if not universal:
        sys.exit(f"Play has no universal APK for vc{args.version_code} yet; it takes a minute after upload")
    req = urllib.request.Request(
        f"{PUBLISHER}/applications/{PACKAGE}/generatedApks/{args.version_code}"
        f"/downloads/{urllib.parse.quote(universal['downloadId'])}:download?alt=media",
        headers={"Authorization": f"Bearer {token('https://www.googleapis.com/auth/androidpublisher')}"},
    )
    with urllib.request.urlopen(req, timeout=600) as r, open(args.out, "wb") as f:
        f.write(r.read())
    print(f"vc{args.version_code} universal APK saved to {args.out}")


def cmd_release(args):
    # For bundles built locally (eas build --local), which never pass through
    # eas submit. Upload, track and notes go in one edit, so testers never see
    # the build without its "What's new". Production users get it only after `promote`.
    text = read_notes(args.notes)
    edit = publisher("/edits", body={})
    if "id" not in edit:
        sys.exit(json.dumps(edit.get("error", edit), indent=2))
    edit_id = edit["id"]
    try:
        # A version code means the bundle went up earlier with `upload`.
        vc = args.aab if args.aab.isdigit() else upload_bundle(edit_id, args.aab)

        lang = publisher(f"/edits/{edit_id}/details").get("defaultLanguage", "en-US")
        path = f"/edits/{edit_id}/tracks/{urllib.parse.quote(TESTING)}"
        track = {
            "track": TESTING,
            "releases": [{
                "versionCodes": [vc],
                "status": "completed",
                "releaseNotes": [{"language": lang, "text": text}],
            }],
        }
        for step in (lambda: publisher(path, body=track, method="PUT"),
                     lambda: commit(edit_id)):
            res = step()
            if "error" in res:
                sys.exit(res["error"].get("message", ""))
        edit_id = None
        print(f"vc{vc} released on {TESTING} with {len(text)} characters of {lang} notes")
    finally:
        if edit_id:
            publisher(f"/edits/{edit_id}", method="DELETE")


def cmd_promote(args):
    # Production gets the exact build and notes already tested from the
    # testing track. With managed publishing off, the commit goes straight to
    # review and then to every user in the production countries.
    if not 1 <= args.rollout <= 100:
        sys.exit("--rollout is a percentage from 1 to 100")
    edit = publisher("/edits", body={})
    if "id" not in edit:
        sys.exit(json.dumps(edit.get("error", edit), indent=2))
    edit_id = edit["id"]
    try:
        # Production is searched first so a staged rollout can still be widened
        # after the next build has replaced it on Beta.
        source = None
        for name in (PRODUCTION, TESTING):
            track = publisher(f"/edits/{edit_id}/tracks/{urllib.parse.quote(name)}")
            source = next(
                (r for r in track.get("releases", [])
                 if args.version_code in r.get("versionCodes", [])),
                None,
            )
            if source:
                break
        if not source:
            sys.exit(f"vc{args.version_code} is not on {TESTING}; ship it there with `release` first")
        release = {
            "name": source.get("name", ""),
            "versionCodes": [args.version_code],
            "status": "completed",
            "releaseNotes": source.get("releaseNotes", []),
        }
        # A staged release keeps everyone else on the previous production build,
        # so a crash on budget phones reaches a slice of users, not all of them.
        if args.rollout < 100:
            release |= {"status": "inProgress", "userFraction": args.rollout / 100}

        track = {"track": args.track, "releases": [release]}
        res = publisher(f"/edits/{edit_id}/tracks/{args.track}", body=track, method="PUT")
        if "error" in res:
            sys.exit(res["error"].get("message", ""))
        res = commit(edit_id)
        if "error" in res:
            sys.exit(res["error"].get("message", ""))
        edit_id = None
        print(f"vc{args.version_code} committed to {args.track} at {args.rollout}%")
    finally:
        if edit_id:
            publisher(f"/edits/{edit_id}", method="DELETE")


def upload_image(edit_id, lang, kind, png):
    with open(png, "rb") as f:
        req = urllib.request.Request(
            f"{UPLOAD}/applications/{PACKAGE}/edits/{edit_id}/listings/{lang}/{kind}?uploadType=media",
            data=f.read(),
            method="POST",
            headers={
                "Authorization": f"Bearer {token('https://www.googleapis.com/auth/androidpublisher')}",
                "Content-Type": "image/png",
            },
        )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read()).get("image", {})
    except urllib.error.HTTPError as e:
        sys.exit(f"{png}: " + json.loads(e.read() or "{}").get("error", {}).get("message", str(e)))


def cmd_icon(args):
    # The listing icon is a store asset, not part of the bundle, so a new app
    # icon does not reach the Play listing on its own.
    edit = publisher("/edits", body={})
    if "id" not in edit:
        sys.exit(json.dumps(edit.get("error", edit), indent=2))
    edit_id = edit["id"]
    try:
        lang = publisher(f"/edits/{edit_id}/details").get("defaultLanguage", "en-US")
        # The icon slot holds one image; emptying it first means the upload never
        # depends on whether Play replaces or refuses a second one.
        publisher(f"/edits/{edit_id}/listings/{lang}/icon", method="DELETE")
        image = upload_image(edit_id, lang, "icon", args.png)

        res = commit(edit_id)
        if "error" in res:
            sys.exit(res["error"].get("message", ""))
        edit_id = None
        print(f"{lang} listing icon replaced: {image.get('sha256', '')[:12]}")
    finally:
        if edit_id:
            publisher(f"/edits/{edit_id}", method="DELETE")


def cmd_art(args):
    # Replaces the whole set in one edit. A failed upload abandons the edit, so the
    # listing never shows half old screenshots and half new.
    edit = publisher("/edits", body={})
    if "id" not in edit:
        sys.exit(json.dumps(edit.get("error", edit), indent=2))
    edit_id = edit["id"]
    try:
        lang = publisher(f"/edits/{edit_id}/details").get("defaultLanguage", "en-US")
        # Play shows phone screenshots in upload order.
        publisher(f"/edits/{edit_id}/listings/{lang}/phoneScreenshots", method="DELETE")
        for png in args.phone:
            upload_image(edit_id, lang, "phoneScreenshots", png)
        if args.feature:
            publisher(f"/edits/{edit_id}/listings/{lang}/featureGraphic", method="DELETE")
            upload_image(edit_id, lang, "featureGraphic", args.feature)

        res = commit(edit_id)
        if "error" in res:
            sys.exit(res["error"].get("message", ""))
        edit_id = None
        print(f"{lang} listing: {len(args.phone)} phone screenshots"
              + (", feature graphic" if args.feature else "") + " replaced")
    finally:
        if edit_id:
            publisher(f"/edits/{edit_id}", method="DELETE")


def cmd_installs(args):
    # Bulk reports come out of the Play bucket as UTF-16 with a BOM, so the
    # default utf-8 read gives you nul bytes between every character.
    with open(args.csv, encoding="utf-16") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("empty report")

    def col(*want):
        return next((c for c in rows[0] if all(w in c.lower() for w in want)), None)

    date = col("date")
    active = col("active", "device")
    installs = col("daily", "device", "install")
    for row in rows:
        parts = [row[date]]
        if installs:
            parts.append(f"+{row[installs]}")
        if active:
            parts.append(f"active={row[active]}")
        print("  ".join(parts))

    if active:
        peak = max(rows, key=lambda r: int(r[active] or 0))
        print(f"\npeak active devices: {peak[active]} on {peak[date]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tracks").set_defaults(fn=cmd_tracks)
    sub.add_parser("testers").set_defaults(fn=cmd_testers)
    for name, fn in (("vitals", cmd_vitals), ("errors", cmd_errors)):
        p = sub.add_parser(name)
        p.add_argument("--days", type=int, default=14)
        p.set_defaults(fn=fn)
    p = sub.add_parser("notes")
    p.add_argument("version_code")
    p.add_argument("file", help="plain text, 500 characters at most")
    p.set_defaults(fn=cmd_notes)
    p = sub.add_parser("release")
    p.add_argument("aab", help="the bundle from eas build --local, or the version code of one already uploaded")
    p.add_argument("notes", help="plain text, 500 characters at most")
    p.set_defaults(fn=cmd_release)
    p = sub.add_parser("promote")
    p.add_argument("version_code", help="already on the testing track and tested from Play")
    p.add_argument("--rollout", type=int, default=100, help="percent of production users, 1 to 100")
    # beta is Play's open testing track, which keeps serving an old build to its users
    # after production moves on unless it is promoted too.
    p.add_argument("--track", default=PRODUCTION, help="production, or beta for open testing")
    p.set_defaults(fn=cmd_promote)
    p = sub.add_parser("upload")
    p.add_argument("aab", help="the bundle from eas build --local")
    p.set_defaults(fn=cmd_upload)
    p = sub.add_parser("apk")
    p.add_argument("version_code")
    p.add_argument("out", help="where to write the universal APK")
    p.set_defaults(fn=cmd_apk)
    p = sub.add_parser("icon")
    p.add_argument("png", help="512x512 PNG, no transparency")
    p.set_defaults(fn=cmd_icon)
    p = sub.add_parser("art")
    p.add_argument("phone", nargs="+", help="2 to 8 PNGs, 9:16, in listing order")
    p.add_argument("--feature", help="1024x500 PNG, no transparency")
    p.set_defaults(fn=cmd_art)
    p = sub.add_parser("installs")
    p.add_argument("csv", help="a report downloaded from Play Console > Download reports")
    p.set_defaults(fn=cmd_installs)
    args = parser.parse_args()
    # installs only reads a downloaded CSV.
    missing = [name for name, value in (("PLAY_PACKAGE", PACKAGE), ("PLAY_TRACK", TESTING),
                                        ("PLAY_ACCOUNT", ACCOUNT)) if not value]
    if missing and args.cmd != "installs":
        sys.exit(f"set {', '.join(missing)}; see the top of {sys.argv[0]}")
    args.fn(args)
