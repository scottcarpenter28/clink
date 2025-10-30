from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpRequest, HttpResponse

from finance.forms import UserSettingsForm
from finance.models.user_settings import UserSettings


@login_required
def settings_view(request: HttpRequest) -> HttpResponse:
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = UserSettingsForm(request.POST, instance=user_settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Settings updated successfully!")
            return redirect("settings")
    else:
        form = UserSettingsForm(instance=user_settings)

    return render(request, "settings.html", {"form": form})
