#!/usr/bin/env python
"""
Test script for Daily Challenges feature.
Run this after migrations: python manage.py shell < test_daily_challenges.py
Or: poetry run python manage.py shell -c "exec(open('test_daily_challenges.py').read())"
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website.settings")
django.setup()

from datetime import date, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from website.models import DailyChallenge, UserDailyChallenge, DailyStatusReport, Points, UserProfile
from website.services.daily_challenge_service import DailyChallengeService

print("=" * 60)
print("DAILY CHALLENGES FEATURE - TEST SCRIPT")
print("=" * 60)

# Step 1: Create test user
print("\n1. Creating test user...")
test_user, created = User.objects.get_or_create(
    username="test_challenge_user",
    defaults={
        "email": "test_challenge@example.com",
        "first_name": "Test",
        "last_name": "User",
    }
)
if created:
    test_user.set_password("testpass123")
    test_user.save()
    print(f"   ✅ Created test user: {test_user.username}")
else:
    print(f"   ℹ️  Test user already exists: {test_user.username}")

# Step 2: Create UserProfile if it doesn't exist
print("\n2. Creating UserProfile...")
profile, created = UserProfile.objects.get_or_create(
    user=test_user,
    defaults={"current_streak": 0}
)
if created:
    print(f"   ✅ Created UserProfile for {test_user.username}")
else:
    print(f"   ℹ️  UserProfile already exists")

# Step 3: Create challenge types
print("\n3. Creating challenge types...")
challenges_data = [
    {
        "challenge_type": "early_checkin",
        "title": "Early Bird",
        "description": "Submit your check-in before 10 AM",
        "points_reward": 15,
    },
    {
        "challenge_type": "positive_mood",
        "title": "Stay Positive",
        "description": "Submit a check-in with a positive mood",
        "points_reward": 10,
    },
    {
        "challenge_type": "complete_all_fields",
        "title": "Complete Reporter",
        "description": "Fill all fields in your check-in",
        "points_reward": 20,
    },
    {
        "challenge_type": "streak_milestone",
        "title": "Streak Master",
        "description": "Reach a streak milestone (7, 15, 30 days)",
        "points_reward": 50,
    },
    {
        "challenge_type": "no_blockers",
        "title": "Smooth Sailing",
        "description": "Report no blockers in your check-in",
        "points_reward": 10,
    },
]

created_count = 0
for challenge_data in challenges_data:
    challenge, created = DailyChallenge.objects.get_or_create(
        challenge_type=challenge_data["challenge_type"],
        defaults=challenge_data
    )
    if created:
        created_count += 1
        print(f"   ✅ Created: {challenge.title}")
    else:
        print(f"   ℹ️  Already exists: {challenge.title}")

print(f"\n   Total active challenges: {DailyChallenge.objects.filter(is_active=True).count()}")

# Step 4: Generate challenges for test user
print("\n4. Generating daily challenges...")
from django.core.management import call_command
from io import StringIO

out = StringIO()
call_command("generate_daily_challenges", "--date", str(date.today()), stdout=out)
print(f"   {out.getvalue()}")

# Check if challenge was assigned
user_challenges = UserDailyChallenge.objects.filter(
    user=test_user,
    challenge_date=date.today()
)
if user_challenges.exists():
    challenge = user_challenges.first()
    print(f"   ✅ Challenge assigned: {challenge.challenge.title}")
else:
    print("   ⚠️  No challenge assigned. Run: python manage.py generate_daily_challenges")

# Step 5: Test challenge completion scenarios
print("\n5. Testing challenge completion...")

# Test 1: Early check-in
print("\n   Test 1: Early Check-in Challenge")
if user_challenges.filter(challenge__challenge_type="early_checkin").exists():
    early_challenge = user_challenges.filter(challenge__challenge_type="early_checkin").first()
    # Create a check-in before 10 AM (simulate by setting created time)
    checkin = DailyStatusReport.objects.create(
        user=test_user,
        date=date.today(),
        previous_work="Test work",
        next_plan="Test plan",
        blockers="None",
        current_mood="Good",
        goal_accomplished=True,
    )
    # Manually set created time to before 10 AM
    from datetime import datetime, time as dt_time
    early_time = datetime.combine(date.today(), dt_time(9, 30))
    checkin.created = early_time
    checkin.save()
    
    completed = DailyChallengeService.check_and_complete_challenges(test_user, checkin)
    if completed:
        print(f"   ✅ Early check-in challenge completed: {completed}")
    else:
        print("   ❌ Early check-in challenge not completed")
    checkin.delete()  # Clean up

# Test 2: Positive mood
print("\n   Test 2: Positive Mood Challenge")
if user_challenges.filter(challenge__challenge_type="positive_mood").exists():
    # Regenerate challenge for positive mood
    UserDailyChallenge.objects.filter(
        user=test_user,
        challenge_date=date.today()
    ).delete()
    call_command("generate_daily_challenges", "--date", str(date.today()), "--force", stdout=StringIO())
    
    positive_challenge = UserDailyChallenge.objects.filter(
        user=test_user,
        challenge_date=date.today(),
        challenge__challenge_type="positive_mood"
    ).first()
    
    if positive_challenge:
        checkin = DailyStatusReport.objects.create(
            user=test_user,
            date=date.today(),
            previous_work="Great progress today!",
            next_plan="Continue the momentum",
            blockers="None",
            current_mood="😊 Happy and excited!",
            goal_accomplished=True,
        )
        completed = DailyChallengeService.check_and_complete_challenges(test_user, checkin)
        if completed:
            print(f"   ✅ Positive mood challenge completed: {completed}")
        else:
            print("   ❌ Positive mood challenge not completed")
        checkin.delete()

# Test 3: Complete all fields
print("\n   Test 3: Complete All Fields Challenge")
if user_challenges.filter(challenge__challenge_type="complete_all_fields").exists():
    UserDailyChallenge.objects.filter(
        user=test_user,
        challenge_date=date.today()
    ).delete()
    call_command("generate_daily_challenges", "--date", str(date.today()), "--force", stdout=StringIO())
    
    complete_challenge = UserDailyChallenge.objects.filter(
        user=test_user,
        challenge_date=date.today(),
        challenge__challenge_type="complete_all_fields"
    ).first()
    
    if complete_challenge:
        checkin = DailyStatusReport.objects.create(
            user=test_user,
            date=date.today(),
            previous_work="Completed all tasks",
            next_plan="Start new features",
            blockers="No blockers",
            current_mood="Great!",
            goal_accomplished=True,
        )
        completed = DailyChallengeService.check_and_complete_challenges(test_user, checkin)
        if completed:
            print(f"   ✅ Complete all fields challenge completed: {completed}")
        else:
            print("   ❌ Complete all fields challenge not completed")
        checkin.delete()

# Step 6: Verify points were awarded
print("\n6. Verifying points...")
points = Points.objects.filter(user=test_user, reason__contains="daily challenge")
print(f"   Total points from challenges: {points.count()}")
if points.exists():
    total_points = sum(p.score for p in points)
    print(f"   Total points awarded: {total_points}")
    for p in points:
        print(f"   - {p.score} points: {p.reason}")

# Step 7: Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print(f"Test User: {test_user.username} (ID: {test_user.id})")
print(f"Active Challenges: {DailyChallenge.objects.filter(is_active=True).count()}")
print(f"User Challenges Today: {UserDailyChallenge.objects.filter(user=test_user, challenge_date=date.today()).count()}")
print(f"Completed Challenges: {UserDailyChallenge.objects.filter(user=test_user, status='completed').count()}")
print(f"Points Awarded: {Points.objects.filter(user=test_user, reason__contains='daily challenge').count()}")

print("\n✅ Test script completed!")
print("\nTo clean up test user, run:")
print(f"  User.objects.get(username='test_challenge_user').delete()")

