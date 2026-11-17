from urllib.parse import urlencode

from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import CustomUserCreationForm


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            next_url = request.POST.get('next')
            if next_url:
                return redirect(f"{reverse('login')}?{urlencode({'next': next_url})}")
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    next_url = request.POST.get('next') or request.GET.get('next', '')
    return render(request, 'signup.html', {'form': form, 'next': next_url})
