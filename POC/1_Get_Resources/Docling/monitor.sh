#!/usr/bin/env bash
# monitor.sh — Run convert.py and record process-only CPU (vCPU) and RAM (GiB).
#
# CPU is expressed in vCPU units (1 vCPU = 100% of one core), matching AWS sizing.
# RAM is expressed in GiB, matching AWS instance specs.
# Metrics CSV is written only after the process completes.
#
# Usage:
#   chmod +x monitor.sh
#   ./monitor.sh XS2A-API-as-PSD2-Interface-Implementation-Guidelines-2.4.pdf
#
# Output:
#   metrics.csv  — written on completion: Elapsed(s), vCPU, RAM_GiB, Cumulative_CPU_s
#   Terminal     — live progress + final report

PDF="${1:?Usage: ./monitor.sh <path/to/document.pdf>}"
INTERVAL=2
METRICS="metrics.csv"
CLK_TCK=$(getconf CLK_TCK)

source .venv/bin/activate

# ---------------------------------------------------------------------------
# Helpers — read directly from /proc for process-only accuracy
# ---------------------------------------------------------------------------
cpu_ticks() {
    local f="/proc/$1/stat"
    [[ -f "$f" ]] || { echo 0; return; }
    read -r line < "$f"
    local a=($line)
    echo $(( a[13] + a[14] ))
}

rss_kb() {
    local f="/proc/$1/status"
    [[ -f "$f" ]] || { echo 0; return; }
    awk '/^VmRSS/{print $2}' "$f"
}

# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------
python convert.py "$PDF" &
PID=$!

echo "Started convert.py  (PID: $PID)"
echo "Sampling every ${INTERVAL}s — metrics written to CSV on completion."
echo ""
printf "%-10s %-10s %-12s %-18s\n" "Elapsed(s)" "vCPU" "RAM(GiB)" "Cumul.CPU(s)"
echo "------------------------------------------------------"

START_WALL=$(date +%s)
INIT_TICKS=$(cpu_ticks $PID)
PREV_TICKS=$INIT_TICKS
MAX_RSS_KB=0
LAST_TICKS=$INIT_TICKS

# Collect rows in memory — write to file only after completion.
ROWS=()

while kill -0 "$PID" 2>/dev/null; do
    sleep "$INTERVAL"

    CUR_TICKS=$(cpu_ticks $PID)
    CUR_RSS=$(rss_kb $PID)

    [[ "$CUR_TICKS" -eq 0 && "$CUR_RSS" -eq 0 ]] && continue

    ELAPSED=$(( $(date +%s) - START_WALL ))

    # vCPU: delta ticks / CLK_TCK / interval  (1.0 = one full core = 1 AWS vCPU)
    DELTA=$(( CUR_TICKS - PREV_TICKS ))
    VCPU=$(awk "BEGIN {printf \"%.2f\", ($DELTA / $CLK_TCK / $INTERVAL)}")

    # RAM in GiB (1 GiB = 1048576 KB)
    RAM_GIB=$(awk "BEGIN {printf \"%.3f\", $CUR_RSS/1048576}")

    # Cumulative CPU seconds consumed by this process since start
    CUM_CPU=$(awk "BEGIN {printf \"%.2f\", ($CUR_TICKS - $INIT_TICKS) / $CLK_TCK}")

    ROWS+=("${ELAPSED},${VCPU},${RAM_GIB},${CUM_CPU}")
    printf "%-10s %-10s %-12s %-18s\r" "${ELAPSED}s" "${VCPU}" "${RAM_GIB} GiB" "${CUM_CPU}s"

    (( CUR_RSS > MAX_RSS_KB )) && MAX_RSS_KB=$CUR_RSS
    PREV_TICKS=$CUR_TICKS
    LAST_TICKS=$CUR_TICKS
done

wait "$PID"
EXIT_CODE=$?
WALL=$(( $(date +%s) - START_WALL ))

# ---------------------------------------------------------------------------
# Write CSV only now — after the process has finished
# ---------------------------------------------------------------------------
{
    echo "Elapsed(s),vCPU,RAM_GiB,Cumulative_CPU_s"
    for row in "${ROWS[@]}"; do echo "$row"; done
} > "$METRICS"

# ---------------------------------------------------------------------------
# Final report
# ---------------------------------------------------------------------------
TOTAL_CPU_S=$(awk "BEGIN {printf \"%.2f\", ($LAST_TICKS - $INIT_TICKS) / $CLK_TCK}")
PEAK_RAM_GIB=$(awk "BEGIN {printf \"%.3f\", $MAX_RSS_KB/1048576}")
WALL_MIN=$(awk "BEGIN {printf \"%.1f\", $WALL/60}")

# Recommended AWS instance: vCPU = ceil(peak vCPU), RAM = ceil(peak GiB) * 1.25 headroom
REC_VCPU=$(awk "BEGIN {
    v=0
    while ((getline line < \"$METRICS\") > 0) {
        split(line,a,\",\")
        if (a[2]+0 > v) v=a[2]+0
    }
    printf \"%d\", int(v)+1
}")
REC_RAM=$(awk "BEGIN {printf \"%.1f\", $PEAK_RAM_GIB * 1.25}")

echo ""
echo ""
echo "========================================="
echo " Resource Report  (process-only)"
echo "========================================="
printf "  %-22s %s\n"    "PDF:"              "$PDF"
printf "  %-22s %s\n"    "Exit code:"        "$EXIT_CODE"
printf "  %-22s %ss (%s min)\n" "Wall time:" "$WALL" "$WALL_MIN"
printf "  %-22s %ss\n"   "Total CPU time:"   "$TOTAL_CPU_S"
printf "  %-22s %s GiB\n" "Peak RAM:"        "$PEAK_RAM_GIB"
printf "  %-22s %s\n"    "Samples:"          "${#ROWS[@]}"
printf "  %-22s %s\n"    "Metrics CSV:"      "$METRICS"
echo "-----------------------------------------"
echo " AWS Sizing Recommendation"
echo "-----------------------------------------"
printf "  %-22s %s vCPU\n"  "Min vCPU:"  "$REC_VCPU"
printf "  %-22s %s GiB\n"   "Min RAM:"   "$REC_RAM"
echo "  (peak + 25%% headroom — check ec2instances.info)"
echo "========================================="

PDF="${1:?Usage: ./monitor.sh <path/to/document.pdf>}"
INTERVAL=2
METRICS="metrics.csv"
CLK_TCK=$(getconf CLK_TCK)   # clock ticks per second (usually 100)

source .venv/bin/activate

# ---------------------------------------------------------------------------
# Helpers — read directly from /proc for process-only accuracy
# ---------------------------------------------------------------------------
cpu_ticks() {
    # utime + stime from /proc/<pid>/stat (fields 14 and 15, 1-indexed)
    local f="/proc/$1/stat"
    [[ -f "$f" ]] || { echo 0; return; }
    read -r line < "$f"
    local a=($line)
    echo $(( a[13] + a[14] ))
}

rss_kb() {
    # VmRSS from /proc/<pid>/status — resident RAM, this process only
    local f="/proc/$1/status"
    [[ -f "$f" ]] || { echo 0; return; }
    awk '/^VmRSS/{print $2}' "$f"
}

# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------
python convert.py "$PDF" &
PID=$!

echo "Started convert.py  (PID: $PID)"
echo "Sampling every ${INTERVAL}s — process-only metrics from /proc/$PID"
echo ""
printf "%-10s %-10s %-12s %-18s\n" "Elapsed(s)" "CPU%" "RAM(MB)" "Cumul.CPU(s)"
echo "------------------------------------------------------"

echo "Elapsed(s),CPU%,RAM_MB,Cumulative_CPU_s" > "$METRICS"

START_WALL=$(date +%s)
INIT_TICKS=$(cpu_ticks $PID)
PREV_TICKS=$INIT_TICKS
MAX_RSS_KB=0
SAMPLES=0
LAST_TICKS=$INIT_TICKS   # fallback after process exits

while kill -0 "$PID" 2>/dev/null; do
    sleep "$INTERVAL"

    CUR_TICKS=$(cpu_ticks $PID)
    CUR_RSS=$(rss_kb $PID)

    [[ "$CUR_TICKS" -eq 0 && "$CUR_RSS" -eq 0 ]] && continue

    ELAPSED=$(( $(date +%s) - START_WALL ))
    RAM_MB=$(awk "BEGIN {printf \"%.0f\", $CUR_RSS/1024}")

    # Instantaneous CPU%: delta ticks in this interval / ticks per second / interval * 100
    DELTA=$(( CUR_TICKS - PREV_TICKS ))
    CPU_PCT=$(awk "BEGIN {printf \"%.1f\", ($DELTA / $CLK_TCK / $INTERVAL) * 100}")

    # Cumulative CPU seconds consumed by this process since start
    CUM_CPU=$(awk "BEGIN {printf \"%.2f\", ($CUR_TICKS - $INIT_TICKS) / $CLK_TCK}")

    echo "${ELAPSED},${CPU_PCT},${RAM_MB},${CUM_CPU}" >> "$METRICS"
    printf "%-10s %-10s %-12s %-18s\r" "${ELAPSED}s" "${CPU_PCT}%" "${RAM_MB} MB" "${CUM_CPU}s"

    (( CUR_RSS > MAX_RSS_KB )) && MAX_RSS_KB=$CUR_RSS
    PREV_TICKS=$CUR_TICKS
    LAST_TICKS=$CUR_TICKS
    (( SAMPLES++ ))
done

wait "$PID"
EXIT_CODE=$?
WALL=$(( $(date +%s) - START_WALL ))

# Total CPU time = all ticks accumulated by the process / CLK_TCK
TOTAL_CPU_S=$(awk "BEGIN {printf \"%.2f\", ($LAST_TICKS - $INIT_TICKS) / $CLK_TCK}")
PEAK_RAM_MB=$(awk "BEGIN {printf \"%.0f\", $MAX_RSS_KB/1024}")
WALL_MIN=$(awk "BEGIN {printf \"%.1f\", $WALL/60}")

echo ""
echo ""
echo "========================================="
echo " Resource Report  (process-only)"
echo "========================================="
printf "  %-20s %s\n" "PDF:"            "$PDF"
printf "  %-20s %s\n" "Exit code:"      "$EXIT_CODE"
printf "  %-20s %ss  (%s min)\n"        "Wall time:"    "$WALL" "$WALL_MIN"
printf "  %-20s %ss\n"                  "Total CPU time:" "$TOTAL_CPU_S"
printf "  %-20s %s MB\n"               "Peak RAM:"      "$PEAK_RAM_MB"
printf "  %-20s %s\n"                   "Samples:"       "$SAMPLES"
printf "  %-20s %s\n"                   "Metrics CSV:"   "$METRICS"
echo "========================================="
