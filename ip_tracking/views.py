from django.shortcuts import render
from django.http import HttpResponse
from ratelimit.decorators import ratelimit


# Anonymous users: 5 requests/minute
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
# Authenticated users: 10 requests/minute
@ratelimit(key='user_or_ip', rate='10/m', method='POST', block=True)
def login_view(request):
    if request.method == 'POST':
        # Example login logic
        username = request.POST.get('username')
        password = request.POST.get('password')

        # In a real app, authenticate user here...
        return HttpResponse(f"Login attempt for {username}")
    return render(request, 'login.html')
