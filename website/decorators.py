from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse, JsonResponse

from website.utils import get_client_ip


def ratelimit(key="user", rate="20/m", method="POST"):
    """
    Rate limit decorator using Django's cache framework.
    Follows BLT's existing cache-based rate limiting pattern.

    Args:
        key: Rate limit per 'user' or 'ip'
        rate: Format 'count/period' e.g., '20/m' (20 per minute), '100/h' (100 per hour)
        method: HTTP method to rate limit (default 'POST', use 'ALL' for all methods)

    Example:
        @ratelimit(key='user', rate='20/m', method='POST')
        @require_POST
        @login_required
        def like_issue(request, issue_pk):
            ...
    """
    # Parse rate limit once (e.g., '10/m' -> count=10, window=60)
    try:
        count, period = rate.split("/")
        count = int(count)
        window = {"s": 1, "m": 60, "h": 3600, "d": 86400}[period]
    except (ValueError, KeyError):
        raise ValueError(f"Invalid rate format: {rate}. Use format like '20/m'")

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Check if method matches
            if method != "ALL" and request.method != method:
                return view_func(request, *args, **kwargs)

            # `count` / `window` pre-parsed above
            # Generate cache key
            if key == "user":
                if not request.user.is_authenticated:
                    # Allow unauthenticated users (they'll hit login_required anyway)
                    return view_func(request, *args, **kwargs)
                identifier = f"user_{request.user.id}"
            elif key == "ip":
                identifier = f"ip_{get_client_ip(request)}"
            else:
                identifier = f"custom_{key}"

            view_id = f"{view_func.__module__}.{view_func.__qualname__}"
            cache_key = f"ratelimit_{view_id}_{identifier}"

            # Atomic rate limit check (same pattern as is_csv_rate_limited)
            added = cache.add(cache_key, 1, window)
            if added:
                return view_func(request, *args, **kwargs)  # First request in window

            # Key exists, increment
            try:
                current_count = cache.incr(cache_key)
            except ValueError:
                # Rare: key expired between add() and incr()
                cache.set(cache_key, 1, window)
                return view_func(request, *args, **kwargs)

            # Check if limit exceeded
            if current_count > count:
                # Return error response based on request type
                if request.headers.get("HX-Request"):
                    # HTMX request - return JSON for automatic error display
                    return JsonResponse(
                        {"error": "Rate limit exceeded. Please try again later."},
                        status=429,
                    )
                elif "application/json" in request.headers.get("Accept", ""):
                    # API request
                    return JsonResponse(
                        {"error": "Rate limit exceeded. Please try again later."},
                        status=429,
                    )
                else:
                    # Regular request
                    return HttpResponse("Rate limit exceeded. Please try again later.", status=429)

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
