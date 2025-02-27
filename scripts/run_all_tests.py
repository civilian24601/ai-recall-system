#!/usr/bin/env python3
"""
run_all_tests.py

A small script that:
1) Runs pytest to discover & execute all tests in /tests/
2) Outputs a JUnit XML file for post-analysis
3) Stores a summary of results in Chroma under a "test_runs" collection (optional)
"""

import os
import subprocess
import datetime
import xml.etree.ElementTree as ET
import chromadb

def run_pytest_and_store_results():
    # 1) Ensure "results" dir for the xml, or store it in /logs/test_results
    results_dir = os.path.join("results")
    os.makedirs(results_dir, exist_ok=True)
    
    junit_xml_path = os.path.join(results_dir, "junit_report.xml")

    # 2) Run pytest with JUnit XML output
    #    We pass --junitxml=... to produce a JUnit-style XML
    print("Running Pytest on /tests/ folder...")
    cmd = [
        "pytest",
        "tests/",           # your tests folder
        "-v",               # verbose
        f"--junitxml={junit_xml_path}",
        "--maxfail=1"       # optional, to stop on first fail
    ]
    
    # run the test process
    completed = subprocess.run(cmd, capture_output=True, text=True)
    # We'll print the standard output in real time or afterwards
    print(completed.stdout)
    # If an error occurred, we want to see it
    if completed.returncode != 0:
        print("Some tests FAILED. Return code:", completed.returncode)
    else:
        print("All tests PASSED successfully!")
    
    # 3) Parse the JUnit XML to get some summary data
    if not os.path.exists(junit_xml_path):
        print("No JUnit XML found. Possibly Pytest never ran or a path issue.")
        return

    tree = ET.parse(junit_xml_path)
    root = tree.getroot()

    # Typically, root = <testsuites> with <testsuite> children in JUnit XML
    # We'll gather some high-level stats
    total_tests = 0
    total_failures = 0
    total_errors = 0
    total_skipped = 0
    
    for testsuite in root.findall("testsuite"):
        total_tests += int(testsuite.get("tests", 0))
        total_failures += int(testsuite.get("failures", 0))
        total_errors += int(testsuite.get("errors", 0))
        total_skipped += int(testsuite.get("skipped", 0))

    # Just for a quick summary
    print(f"JUnit Summary: tests={total_tests}, failures={total_failures}, errors={total_errors}, skipped={total_skipped}")

    # 4) Optionally store the summary in Chroma "test_runs" collection
    #    We'll embed or store the entire XML or just the stats + log
    client = chromadb.PersistentClient(path="/mnt/f/projects/ai-recall-system/chroma_db/")
    test_runs_collection = client.get_or_create_collection("test_runs")  # rename as you like

    # We'll create a doc id with a timestamp for uniqueness
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    doc_id = f"test_run_{timestamp_str}"

    # Minimal JSON to store
    test_run_data = {
        "timestamp": timestamp_str,
        "tests": total_tests,
        "failures": total_failures,
        "errors": total_errors,
        "skipped": total_skipped,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        # You can also embed the full JUnit XML as a string if desired:
        # "junit_xml": open(junit_xml_path, "r").read(),
    }

    try:
        test_runs_collection.add(
            ids=[doc_id],
            documents=[str(test_run_data)],  # store JSON as string
            metadatas=[test_run_data]        # partial duplication, or pick a subset
        )
        print(f"Stored test run results in Chroma under doc_id={doc_id}")
    except Exception as e:
        print("Failed to store test results in Chroma:", e)

def main():
    run_pytest_and_store_results()

if __name__ == "__main__":
    main()
