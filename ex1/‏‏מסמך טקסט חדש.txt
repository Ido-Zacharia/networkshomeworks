#!/bin/bash

# =========================================================
# EX1 tester script
# Usage: ./test_ex1.sh [user_file] [port]
# =========================================================

USER_FILE="${1:-./user_file.txt}"
PORT="${2:-1336}"

SERVER_CMD="python3 ./ex1_server.py \"$USER_FILE\" \"$PORT\""
CLIENT_CMD="python3 ./ex1_client.py localhost $PORT"

# -------- ANSI colors --------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # reset

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo "Using user file: $USER_FILE"
echo "Using port:      $PORT"
echo

# ----------------- start server -----------------
echo -e "${CYAN}Starting server:${NC} $SERVER_CMD"
eval $SERVER_CMD &
SERVER_PID=$!

sleep 1

if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo -e "${RED}ERROR:${NC} server failed to start (PID $SERVER_PID not running)."
    exit 1
fi

echo "Server running on port $PORT"
echo "Server started with PID: $SERVER_PID"
echo
echo -e "${BOLD}==================== RUNNING TESTS ====================${NC}"
echo

# ----------------- helper: run one test -----------------
run_test() {
    local name="$1"
    local input="$2"
    shift 2
    local patterns=("$@")

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "${CYAN}=== $name ===${NC}"
    echo "Input:"
    printf '%b\n' "$input"
    echo "---------------- Output ----------------"

    out=$(printf '%b' "$input" | eval "$CLIENT_CMD" 2>&1)
    echo "$out"
    echo "---------------- Result ----------------"

    local ok=1
    for p in "${patterns[@]}"; do
        echo "$out" | grep -F "$p" >/dev/null
        if [ $? -ne 0 ]; then
            echo -e "${RED}MISSING:${NC} $p"
            ok=0
        fi
    done

    if [ $ok -eq 1 ]; then
        echo -e "${GREEN}[OK]   $name${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}[FAIL] $name${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo
}

# =========================================================
#  TESTS
# =========================================================

# 1) Valid login + Caesar + quit
run_test "Valid login + Caesar + quit" \
"User: Bob
Password: simplepass
caesar: hello 2
quit
" \
"Welcome! Please log in." \
"Hi Bob, good to see you." \
"the ciphertext is: jgnnq"

# 2) Valid login + invalid Caesar input (should NOT disconnect) + valid Caesar
run_test "Invalid Caesar input then valid Caesar (no disconnect)" \
"User: Bob
Password: simplepass
caesar: Hello! 2
caesar: hello 2
quit
" \
"Hi Bob, good to see you." \
"error: invalid input" \
"the ciphertext is: jgnnq"

# 3) Valid login + invalid LCM then valid LCM (no disconnect)
run_test "Invalid LCM then valid LCM (no disconnect)" \
"User: Bob
Password: simplepass
lcm: 5 x
lcm: 6 21
quit
" \
"Hi Bob, good to see you." \
"error: invalid input" \
"the lcm is: 42"

# 4) Valid login + invalid parentheses then valid parentheses (no disconnect)
run_test "Invalid parentheses then valid (no disconnect)" \
"User: Bob
Password: simplepass
parentheses: (a())
parentheses: ((()))()(())
quit
" \
"Hi Bob, good to see you." \
"error: invalid input" \
"the parentheses are balanced: yes"

# 5) Valid login + invalid command (not one of the 4) → disconnect
# Expected:
# "invalid command, disconnecting..., A client disconnected."
run_test "Invalid command (should disconnect)" \
"User: Bob
Password: simplepass
foo: 123
" \
"Hi Bob, good to see you." \
"invalid command, disconnecting..." \
"A client disconnected."

# 6) Wrong login format → disconnect
# EXACT REQUIRED MESSAGE:
# "need to send User: {your username} and in new line Password: {your password}, A client disconnected."
run_test "Wrong login format (Password first)" \
"Password: simplepass
User: Bob
" \
"error: invalid input"

run_test "Missing 'User:' prefix" \
"Bob
Password: simplepass
" \
"error: invalid input"

run_test "Missing 'Password:' prefix" \
"User: Bob
simplepass
" \
"error: invalid input"

# 7) Second client full valid flow
run_test "Second client: valid full flow" \
"User: Alice
Password: BetT3RpAas
parentheses: ((()))()(())
lcm: 8 12
caesar: hello 5
quit
" \
"Welcome! Please log in." \
"Hi Alice, good to see you." \
"the parentheses are balanced: yes" \
"the lcm is: 24" \
"the ciphertext is: mjqqt"

# =========================================================
#  EXTRA TESTS
# =========================================================

# 8) Wrong password, then correct password, then quit
run_test "Wrong password then correct" \
"User: Bob
Password: wrongpass
User: Bob
Password: simplepass
quit
" \
"Welcome! Please log in." \
"Failed to login" \
"Hi Bob, good to see you."


# 9) Caesar with large shift (mod 26 behavior)
run_test "Caesar with large shift (28 → 2)" \
"User: Bob
Password: simplepass
caesar: hello 28
quit
" \
"Hi Bob, good to see you." \
"the ciphertext is: jgnnq"

# 10) LCM with equal numbers
run_test "LCM of equal numbers" \
"User: Bob
Password: simplepass
lcm: 7 7
quit
" \
"Hi Bob, good to see you." \
"the lcm is: 7"

# 11) LCM with missing argument (should be invalid input)
run_test "LCM with missing argument (invalid)" \
"User: Bob
Password: simplepass
lcm: 5
quit
" \
"Hi Bob, good to see you." \
"error: invalid input"

# ----------------- cleanup -----------------
echo "Stopping server (PID $SERVER_PID)..."
kill "$SERVER_PID" 2>/dev/null
wait "$SERVER_PID" 2>/dev/null

echo
echo -e "${BOLD}==================== TESTS FINISHED ====================${NC}"
echo
echo -e "${BOLD}==================== SUMMARY ====================${NC}"
echo -e "Total tests:  ${BOLD}$TOTAL_TESTS${NC}"
echo -e "${GREEN}Passed:       $PASSED_TESTS${NC}"
if [ "$FAILED_TESTS" -gt 0 ]; then
    echo -e "${RED}Failed:       $FAILED_TESTS${NC}"
else
    echo -e "${GREEN}Failed:       0${NC}"
fi
echo
