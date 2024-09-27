import os
from django.shortcuts import render, HttpResponse
from dotenv import load_dotenv
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
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
        greeting = f"Hi {username}, welcome to audiosmith. I am Laura, your personal journalist. I am here to cover and write about the daily life events of Yours. So are you ready to start?"
    else:
        username = "Guest"
        email = "No Email"
        greeting = "Hi, welcome to audiosmith. I am Laura, your personal journalist. I am here to cover and write about the daily life events of Yours. So are you ready to start?"

    context = {"greeting": greeting, "username": username, "email": email}
    return render(request, "transcriber_webpage/home.html", context)


from django.shortcuts import render
from .models import JournalEntry

@login_required
def all_journal_entries(request):
    if request.user.is_authenticated:
        username = request.user.username
        email = request.user.email if request.user.email else "No Email"
        # Fetch the journal entries for the authenticated user, ordered by newest first
        journal_entries = JournalEntry.objects.filter(user=request.user).order_by(
            "-timestamp"
        )
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


def test(request):
    return HttpResponse("Yeah test is working")


def get_api_key(request):
    api_key = os.getenv("DEEPGRAM_API_KEY")
    return HttpResponse(api_key)


from django.contrib.auth.decorators import login_required


def create_journal_entry(request):
    if request.user.is_authenticated:
        user = request.user
    else:
        return render(request, "transcriber_webpage/error404.html")

    # Fetch the latest ChatHistory entry for the user
    latest_chat = ChatHistory.objects.filter(user=user).order_by("-timestamp").first()

    if not latest_chat:
        return render(request, "transcriber_webpage/error404.html")

    chat_transcript = latest_chat.transcript
    chat_timestamp = latest_chat.timestamp

    # Prepare the message content to include the transcript and timestamp
    message_content = f"{chat_transcript}\n Timestamp: {chat_timestamp}"

    # Pass the latest chat transcript to Groq for processing
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": '''You are the AI in conversation with a user who answers your questions about their daily life, experiences, and thoughts. Your task is to take the responses given by the user during the conversation and convert them into a cohesive, well-written journal entry. The journal should be written from the user's perspective, as if they are writing it themselves.The journal entry should not mention the AI or the conversation itself. Instead, focus on translating the user's answers into a natural narrative that reflects their day, emotions, observations, and reflections. The tone should be personal, introspective, and authentic, as though the user is recording their thoughts for their own private journal.''',
            },
            {"role": "user", "content": message_content},
        ],
        temperature=1,
        top_p=1,
        stream=False,
        stop=None,
    )

    groq_response_content = completion.choices[
        0
    ].message.content  # Extract the Groq response

    # Save the response as a new JournalEntry for the user
    JournalEntry.objects.create(
        user=user, groq_response=groq_response_content, timestamp=timezone.now()
    )

    # Render a "Thank you" HTML page
    return render(request, "transcriber_webpage/thankyou.html")


@login_required
def edit_journal_entry(request, entry_id):
    username = request.user.username
    email = request.user.email if request.user.email else "No Email"
    journal_entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)

    if request.method == "POST":
        new_content = request.POST.get("journal_content", "")
        journal_entry.groq_response = new_content
        journal_entry.save()
        return redirect(
            "all_entries"
        )  # Redirect to the page listing all entries after saving

    return render(
        request,
        "transcriber_webpage/edit_entry.html",
        {"username": username, "email": email, "journal_entry": journal_entry},
    )


def home(request):
    return render(request, "users/home.html")


class RegisterView(View):
    form_class = RegisterForm
    initial = {"key": "value"}
    template_name = "users/register.html"

    def dispatch(self, request, *args, **kwargs):
        # will redirect to the home page if a user tries to access the register page while logged in
        if request.user.is_authenticated:
            return redirect(to="/")

        # else process dispatch as it otherwise normally would
        return super(RegisterView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()

            username = form.cleaned_data.get("username")
            messages.success(request, f"Account created for {username}")

            return redirect(to="login")

        return render(request, self.template_name, {"form": form})


# Class based view that extends from the built in login view to add a remember me functionality
class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get("remember_me")

        if not remember_me:
            # set session expiry to 0 seconds. So it will automatically close the session after the browser is closed.
            self.request.session.set_expiry(0)

            # Set session as modified to force data updates/cookie to be saved.
            self.request.session.modified = True

        # else browser session will be as long as the session cookie time "SESSION_COOKIE_AGE" defined in settings.py
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
def profile(request):
    username = request.user.username
    email = request.user.email if request.user.email else "No Email"
    if request.method == "POST":
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(
            request.POST, request.FILES, instance=request.user.profile
        )

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
        {"username": username, "email": email,"user_form": user_form, "profile_form": profile_form},
    )
