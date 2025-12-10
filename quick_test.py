#!/usr/bin/env python
"""
Quick test to verify Daily Challenges work.
Run: poetry run python manage.py shell < quick_test.py
"""

from django.contrib.auth.models import User
from website.models import DailyStatusReport, UserDailyChallenge, Points
from website.services.daily_challenge_service import DailyChallengeService
from datetime import date, datetime, time as dt_time

user = User.objects.get(username="test_challenge_user")
today = date.today()

print("=" * 60)
print("QUICK TEST - Daily Challenges")
print("=" * 60)

# Check assigned challenges
challenges = UserDailyChallenge.objects.filter(user=user, challenge_date=today)
print(f"\n1. Assigned challenges: {challenges.count()}")
for c in challenges:
    print(f"   - {c.challenge.title} ({c.challenge.challenge_type}): {c.status}")

if not challenges.exists():
    print("   ⚠️  No challenges assigned. Run: python manage.py generate_daily_challenges")
    exit()

# Test early check-in challenge
print("\n2. Testing Early Check-in Challenge...")
early_challenge = challenges.filter(challenge__challenge_type="early_checkin").first()
if early_challenge:
    checkin = DailyStatusReport.objects.create(
        user=user,
        date=today,
        previous_work="Test work",
        next_plan="Test plan",
        blockers="None",
        current_mood="Good",
        goal_accomplished=True,
    )
    # Set time to 9:30 AM
    checkin.created = datetime.combine(today, dt_time(9, 30))
    checkin.save()
    
    completed = DailyChallengeService.check_and_complete_challenges(user, checkin)
    if completed:
        print(f"   ✅ Challenge completed: {completed}")
        early_challenge.refresh_from_db()
        print(f"   Status: {early_challenge.status}, Points: {early_challenge.points_awarded}")
    else:
        print("   ❌ Challenge not completed")
    
    checkin.delete()
else:
    print("   ℹ️  No early check-in challenge assigned today")

# Test positive mood challenge
print("\n3. Testing Positive Mood Challenge...")
# Regenerate to get positive mood challenge
UserDailyChallenge.objects.filter(user=user, challenge_date=today).delete()
from django.core.management import call_command
from io import StringIO
call_command("generate_daily_challenges", "--date", str(today), "--force", stdout=StringIO())

positive_challenge = UserDailyChallenge.objects.filter(
    user=user,
    challenge_date=today,
    challenge__challenge_type="positive_mood"
).first()

if positive_challenge:
    checkin = DailyStatusReport.objects.create(
        user=user,
        date=today,
        previous_work="Great progress!",
        next_plan="Continue momentum",
        blockers="None",
        current_mood="😊 Happy and excited!",
        goal_accomplished=True,
    )
    
    completed = DailyChallengeService.check_and_complete_challenges(user, checkin)
    if completed:
        print(f"   ✅ Challenge completed: {completed}")
        positive_challenge.refresh_from_db()
        print(f"   Status: {positive_challenge.status}, Points: {positive_challenge.points_awarded}")
    else:
        print("   ❌ Challenge not completed")
    
    checkin.delete()
else:
    print("   ℹ️  No positive mood challenge assigned (random selection)")

# Check points
print("\n4. Points Summary:")
points = Points.objects.filter(user=user, reason__contains="daily challenge")
if points.exists():
    total = sum(p.score for p in points)
    print(f"   Total points from challenges: {total}")
    for p in points:
        print(f"   - {p.score} points: {p.reason[:50]}...")
else:
    print("   No points awarded yet")

print("\n" + "=" * 60)
print("✅ Quick test completed!")
print("=" * 60)

