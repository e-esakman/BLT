#!/usr/bin/env python
"""
Quick setup script for testing Daily Challenges.
Run: poetry run python manage.py shell < setup_test_data.py
"""

from django.contrib.auth.models import User
from website.models import DailyChallenge, UserProfile

# Create test user
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
    print(f"✅ Created test user: {test_user.username} (password: testpass123)")
else:
    print(f"ℹ️  Test user already exists: {test_user.username}")

# Create UserProfile
UserProfile.objects.get_or_create(user=test_user, defaults={"current_streak": 0})

# Create challenge types
challenges = [
    {"challenge_type": "early_checkin", "title": "Early Bird", "description": "Submit your check-in before 10 AM", "points_reward": 15},
    {"challenge_type": "positive_mood", "title": "Stay Positive", "description": "Submit a check-in with a positive mood", "points_reward": 10},
    {"challenge_type": "complete_all_fields", "title": "Complete Reporter", "description": "Fill all fields in your check-in", "points_reward": 20},
    {"challenge_type": "streak_milestone", "title": "Streak Master", "description": "Reach a streak milestone (7, 15, 30 days)", "points_reward": 50},
    {"challenge_type": "no_blockers", "title": "Smooth Sailing", "description": "Report no blockers in your check-in", "points_reward": 10},
]

for data in challenges:
    challenge, created = DailyChallenge.objects.get_or_create(
        challenge_type=data["challenge_type"],
        defaults=data
    )
    if created:
        print(f"✅ Created challenge: {challenge.title}")
    else:
        print(f"ℹ️  Challenge exists: {challenge.title}")

print(f"\n✅ Setup complete! Active challenges: {DailyChallenge.objects.filter(is_active=True).count()}")

