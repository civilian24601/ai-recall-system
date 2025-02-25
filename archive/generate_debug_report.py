def generate_debug_report(hours=24):
    """Uses Continue.dev to generate a debugging report."""
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = "logs/debug_report.md"

    # Query Continue.dev for error logs & debugging summaries
    continue_command = f'continue @codebase errors --last {hours}h'
    debug_result = subprocess.run(continue_command, shell=True, capture_output=True, text=True)

    with open(log_file, "a") as f:
        f.write(f"\n### Debugging Report - {today} (Last {hours} Hours)\n")
        f.write(debug_result.stdout)
        f.write("\n---\n")

    print(f"✅ Debugging report generated ({hours} hours) in {log_file}")

# Example usage
generate_debug_report(5)  # Generate debugging report for last 5 hours
