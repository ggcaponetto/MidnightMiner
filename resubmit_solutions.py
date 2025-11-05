#!/usr/bin/env python3
"""
Standalone script to resubmit failed solutions from solutions.csv
"""
import requests
import sys
import os

API_BASE = "https://scavenger.prod.gd.midnighttge.io"
SOLUTIONS_FILE = "solutions.csv"

def submit_solution(address, challenge_id, nonce):
    """Submit a solution to the API"""
    url = f"{API_BASE}/solution/{address}/{challenge_id}/{nonce}"

    try:
        response = requests.post(url, json={}, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("crypto_receipt") is not None:
            return ("success", "Solution accepted")
        else:
            return ("rejected", "No crypto receipt in response")

    except requests.exceptions.HTTPError as e:
        error_detail = e.response.text
        if "Solution already exists" in error_detail:
            return ("already_exists", "Solution already exists")
        else:
            return ("error", f"HTTP {e.response.status_code}: {error_detail}")

    except requests.exceptions.Timeout:
        return ("error", "Request timed out")

    except Exception as e:
        return ("error", str(e))


def main():
    if not os.path.exists(SOLUTIONS_FILE):
        print(f"Error: {SOLUTIONS_FILE} not found")
        return 1

    # Read all solutions
    with open(SOLUTIONS_FILE, 'r') as f:
        lines = f.readlines()

    if not lines:
        print(f"{SOLUTIONS_FILE} is empty")
        return 0

    print(f"Found {len(lines)} solution(s) to resubmit")
    print("="*70)

    results = {
        "success": 0,
        "already_exists": 0,
        "rejected": 0,
        "error": 0
    }

    failed_solutions = []

    for i, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        try:
            parts = line.split(',')
            if len(parts) != 3:
                print(f"[{i}] SKIP: Invalid format: {line}")
                failed_solutions.append(line)
                continue

            address, challenge_id, nonce = parts

            print(f"[{i}/{len(lines)}] Submitting: {address[:20]}... / {challenge_id[:20]}...", end=" ")

            status, message = submit_solution(address, challenge_id, nonce)

            if status == "success":
                print(f"✓ SUCCESS")
                results["success"] += 1
            elif status == "already_exists":
                print(f"✓ ALREADY EXISTS")
                results["already_exists"] += 1
            elif status == "rejected":
                print(f"✗ REJECTED: {message}")
                results["rejected"] += 1
                failed_solutions.append(line)
            else:
                print(f"✗ ERROR: {message}")
                results["error"] += 1
                failed_solutions.append(line)

        except Exception as e:
            print(f"[{i}] ERROR: {e}")
            failed_solutions.append(line)
            results["error"] += 1

    print()
    print("="*70)
    print("SUMMARY:")
    print(f"  Successful submissions:  {results['success']}")
    print(f"  Already existed:         {results['already_exists']}")
    print(f"  Rejected:                {results['rejected']}")
    print(f"  Errors:                  {results['error']}")
    print(f"  Total:                   {len(lines)}")
    print("="*70)

    # Automatically rewrite solutions.csv with only failed submissions
    if failed_solutions:
        with open(SOLUTIONS_FILE, 'w') as f:
            for solution in failed_solutions:
                f.write(solution + '\n')
        print(f"\n✓ Updated {SOLUTIONS_FILE} - kept {len(failed_solutions)} failed solution(s)")
        print(f"  Removed {results['success'] + results['already_exists']} successful/existing solution(s)")
    else:
        print(f"\n✓ All solutions submitted successfully - wiped {SOLUTIONS_FILE}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
