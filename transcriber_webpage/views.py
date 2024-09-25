import os
from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from dotenv import load_dotenv
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm, UpdateUserForm, UpdateProfileForm
from .models import JournalEntry, ChatHistory
from groq import Groq
from django.utils import timezone

load_dotenv()

# Create your views here.

def redirect_home(request):
    if request.user.is_authenticated:
        return redirect("/record")
    else:
        return redirect("/login")

def index(request):
    if request.user.is_authenticated:
        username = request.user.username
        email = request.user.email if request.user.email else "No Email"
        greeting = f"Hi {username}, welcome to audiosmith. I am Stella, your personal journalist. I am here to cover and write about the daily life events that make you who you are. So are you ready to start?"
    else:
        username = "Guest"
        email = "No Email"
        greeting = "Hi, welcome to audiosmith. I am Stella, your personal journalist. I am here to cover and write about the daily life events that make you who you are. So are you ready to start?"

    context = {"greeting": greeting, "username": username, "email": email}
    return render(request, "transcriber_webpage/home.html", context)

@login_required
def all_journal_entries(request):
    if request.user.is_authenticated:
        username = request.user.username
        email = request.user.email if request.user.email else "No Email"
        journal_entries = JournalEntry.objects.filter(user=request.user).order_by("-timestamp")
    else:
        username = "Guest"
        email = "No Email"
        journal_entries = []  # No entries for guests

    context = {
        "username": username,
        "email": email,
        "journal_entries": journal_entries,  # Add journal entries to context
    }

    return render(request, "transcriber_webpage/all_entries.html", context)

@csrf_exempt  # Exempting CSRF for this view
def test(request):
    return HttpResponse("Yeah test is working")

@csrf_exempt  # Exempting CSRF for this view
def get_api_key(request):
    api_key = os.getenv("DEEPGRAM_API_KEY")
    return HttpResponse(api_key)

@login_required
@csrf_exempt  # Exempting CSRF for this view
def create_journal_entry(request):
    if request.user.is_authenticated:
        user = request.user
    else:
        return render(request, "transcriber_webpage/error404.html")

    latest_chat = ChatHistory.objects.filter(user=user).order_by("-timestamp").first()

    if not latest_chat:
        return render(request, "transcriber_webpage/error404.html")

    chat_transcript = latest_chat.transcript
    chat_timestamp = latest_chat.timestamp

    message_content = f"{chat_transcript}\n Timestamp: {chat_timestamp}"

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "you are the user and you talk with an ai for he questions to talk about your daily life events everyday to write a journal, here is the chat history between you and ai, convert it into a journal of your life based on the answers you gave. do not mention you talked to an ai. write your journal like you are writing it based on whatever you said in conversation",
            },
            {"role": "user", "content": message_content},
        ],
        temperature=1,
        top_p=1,
        stream=False,
        stop=None,
    )

    groq_response_content = completion.choices[0].message.content

    JournalEntry.objects.create(
        user=user, groq_response=groq_response_content, timestamp=timezone.now()
    )

    return render(request, "transcriber_webpage/thankyou.html")

@login_required
@csrf_exempt  # Exempting CSRF for this view
def edit_journal_entry(request, entry_id):
    username = request.user.username
    email = request.user.email if request.user.email else "No Email"
    journal_entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)

    if request.method == "POST":
        new_content = request.POST.get("journal_content", "")
        journal_entry.groq_response = new_content
        journal_entry.save()
        return redirect("all_entries")

    return render(
        request,
        "transcriber_webpage/edit_entry.html",
        {"username": username, "email": email, "journal_entry": journal_entry},
    )

@csrf_exempt  # Exempting CSRF for this view
def home(request):
    return render(request, "users/home.html")

class RegisterView(View):
    form_class = RegisterForm
    initial = {"key": "value"}
    template_name = "users/register.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(to="/")
        return super(RegisterView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {"form": form})

    @csrf_exempt  # Exempting CSRF for this view
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()

            username = form.cleaned_data.get("username")
            messages.success(request, f"Account created for {username}")

            return redirect(to="login")

        return render(request, self.template_name, {"form": form})

class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get("remember_me")

        if not remember_me:
            self.request.session.set_expiry(0)
            self.request.session.modified = True

        return super(CustomLoginView, self).form_valid(form)

class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = "users/password_reset.html"
    email_template_name = "users/password_reset_email.html"
    subject_template_name = "users/password_reset_subject"
    success_message = (
        "We've emailed you instructions for setting your password, "
        "if an account exists with the email you entered. You should receive them shortly."
        " If you don't receive an email, "
        "please make sure you've entered the address you registered with, and check your spam folder."
    )
    success_url = reverse_lazy("users-home")

class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = "users/change_password.html"
    success_message = "Successfully Changed Your Password"
    success_url = reverse_lazy("users-home")

@login_required
@csrf_exempt  # Exempting CSRF for this view
def profile(request):
    username = request.user.username
    email = request.user.email if request.user.email else "No Email"
    if request.method == "POST":
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile is updated successfully")
            return redirect(to="users-profile")
    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

    return render(
        request,
        "transcriber_webpage/profile.html",
        {"username": username, "email": email, "user_form": user_form, "profile_form": profile_form},
    )
