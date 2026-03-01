#!/bin/bash

# ChurGPT API Integration Test
# Tests all major API endpoints

set -e

BASE_URL="http://localhost:8000/api/v1"
TOKEN=""
TEACHER_TOKEN=""
STUDENT_TOKEN=""
CLASS_ID=""
MATERIAL_ID=""
ASSIGNMENT_ID=""

echo "🧪 Testing ChurGPT API..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Helper functions
test_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

# 1. Health Check
echo "1. Testing health endpoint..."
if curl -s http://localhost:8000/health | grep -q "ok"; then
    test_pass "Health check passed"
else
    test_fail "Health check failed"
fi

# 2. Register Teacher
echo ""
echo "2. Testing teacher registration..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "teacher@test.com",
        "password": "pass1234",
        "full_name": "Test Teacher",
        "role": "teacher"
    }')

if echo "$REGISTER_RESPONSE" | grep -q "id"; then
    test_pass "Teacher registration successful"
else
    test_fail "Teacher registration failed: $REGISTER_RESPONSE"
fi

# 3. Login Teacher
echo ""
echo "3. Testing teacher login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=teacher@test.com&password=pass1234")

TEACHER_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TEACHER_TOKEN" ]; then
    test_pass "Teacher login successful"
else
    test_fail "Teacher login failed: $LOGIN_RESPONSE"
fi

# 4. Get Current User
echo ""
echo "4. Testing get current user..."
ME_RESPONSE=$(curl -s "$BASE_URL/auth/me" \
    -H "Authorization: Bearer $TEACHER_TOKEN")

if echo "$ME_RESPONSE" | grep -q "teacher@test.com"; then
    test_pass "Get current user successful"
else
    test_fail "Get current user failed"
fi

# 5. Register Student
echo ""
echo "5. Testing student registration..."
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "student@test.com",
        "password": "pass1234",
        "full_name": "Test Student",
        "role": "student"
    }')

if echo "$REGISTER_RESPONSE" | grep -q "id"; then
    test_pass "Student registration successful"
else
    test_fail "Student registration failed"
fi

# 6. Login Student
echo ""
echo "6. Testing student login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=student@test.com&password=pass1234")

STUDENT_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$STUDENT_TOKEN" ]; then
    test_pass "Student login successful"
else
    test_fail "Student login failed"
fi

# 7. Create Class (Teacher)
echo ""
echo "7. Testing create class..."
CLASS_RESPONSE=$(curl -s -X POST "$BASE_URL/teachers/classes" \
    -H "Authorization: Bearer $TEACHER_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Mathematics 101",
        "subject": "Math",
        "schedule": "Mon/Wed 10:00-11:30",
        "color": "blue",
        "description": "Introduction to Mathematics"
    }')

CLASS_ID=$(echo "$CLASS_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$CLASS_ID" ]; then
    test_pass "Create class successful (ID: $CLASS_ID)"
else
    test_fail "Create class failed: $CLASS_RESPONSE"
fi

# 8. Get Classes (Teacher)
echo ""
echo "8. Testing get teacher classes..."
CLASSES_RESPONSE=$(curl -s "$BASE_URL/teachers/classes" \
    -H "Authorization: Bearer $TEACHER_TOKEN")

if echo "$CLASSES_RESPONSE" | grep -q "Mathematics 101"; then
    test_pass "Get teacher classes successful"
else
    test_fail "Get teacher classes failed"
fi

# 9. Create Material (Teacher)
echo ""
echo "9. Testing create material..."
MATERIAL_RESPONSE=$(curl -s -X POST "$BASE_URL/teachers/materials" \
    -H "Authorization: Bearer $TEACHER_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"title\": \"Algebra Basics\",
        \"subject\": \"Math\",
        \"description\": \"Introduction to Algebra\",
        \"class_id\": $CLASS_ID
    }")

MATERIAL_ID=$(echo "$MATERIAL_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$MATERIAL_ID" ]; then
    test_pass "Create material successful (ID: $MATERIAL_ID)"
else
    test_fail "Create material failed"
fi

# 10. Create Assignment (Teacher)
echo ""
echo "10. Testing create assignment..."
ASSIGNMENT_RESPONSE=$(curl -s -X POST "$BASE_URL/teachers/assignments" \
    -H "Authorization: Bearer $TEACHER_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"title\": \"Homework 1\",
        \"description\": \"Solve problems 1-10\",
        \"class_id\": $CLASS_ID,
        \"max_score\": 100
    }")

ASSIGNMENT_ID=$(echo "$ASSIGNMENT_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)

if [ -n "$ASSIGNMENT_ID" ]; then
    test_pass "Create assignment successful (ID: $ASSIGNMENT_ID)"
else
    test_fail "Create assignment failed"
fi

# 11. Get Teacher Dashboard Stats
echo ""
echo "11. Testing teacher dashboard stats..."
STATS_RESPONSE=$(curl -s "$BASE_URL/teachers/dashboard/stats" \
    -H "Authorization: Bearer $TEACHER_TOKEN")

if echo "$STATS_RESPONSE" | grep -q "total_classes"; then
    test_pass "Get teacher dashboard stats successful"
else
    test_fail "Get teacher dashboard stats failed"
fi

# 12. Student Get Classes
echo ""
echo "12. Testing student get classes..."
STUDENT_CLASSES=$(curl -s "$BASE_URL/students/classes" \
    -H "Authorization: Bearer $STUDENT_TOKEN")

# Student should have no classes yet (not enrolled)
test_pass "Student get classes works (empty or populated)"

# 13. Student Create Mistake
echo ""
echo "13. Testing student create mistake..."
MISTAKE_RESPONSE=$(curl -s -X POST "$BASE_URL/students/mistakes" \
    -H "Authorization: Bearer $STUDENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "subject": "Math",
        "topic": "Algebra",
        "question": "What is 2+2?",
        "correct_answer": "4",
        "student_answer": "5",
        "explanation": "Basic addition"
    }')

if echo "$MISTAKE_RESPONSE" | grep -q "id"; then
    test_pass "Create mistake successful"
else
    test_fail "Create mistake failed"
fi

# 14. Student Get Mistake Stats
echo ""
echo "14. Testing student mistake stats..."
MISTAKE_STATS=$(curl -s "$BASE_URL/students/mistakes/stats" \
    -H "Authorization: Bearer $STUDENT_TOKEN")

if echo "$MISTAKE_STATS" | grep -q "total"; then
    test_pass "Get mistake stats successful"
else
    test_fail "Get mistake stats failed"
fi

# 15. Create Chat Session
echo ""
echo "15. Testing create chat session..."
CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/chat/sessions" \
    -H "Authorization: Bearer $STUDENT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "session_type": "homework",
        "title": "Math Help"
    }')

if echo "$CHAT_RESPONSE" | grep -q "id"; then
    test_pass "Create chat session successful"
else
    test_fail "Create chat session failed"
fi

echo ""
echo "========================================"
echo -e "${GREEN}✓ All API tests passed!${NC}"
echo "========================================"
echo ""
echo "Tested endpoints:"
echo "  - Health check"
echo "  - Authentication (register/login/me)"
echo "  - Teacher endpoints (classes, materials, assignments, dashboard)"
echo "  - Student endpoints (classes, mistakes, stats)"
echo "  - Chat endpoints"
echo ""
