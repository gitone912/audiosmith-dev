from django.db import models
from django.contrib.auth.models import User
from PIL import Image

# Extending User Model Using a One-To-One Link
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='default.jpg', upload_to='profile_images')
    bio = models.TextField()

    def __str__(self):
        return self.user.username

    # resizing images
    def save(self, *args, **kwargs):
        super().save()

        img = Image.open(self.avatar.path)

        if img.height > 100 or img.width > 100:
            new_img = (100, 100)
            img.thumbnail(new_img)
            img.save(self.avatar.path)

# Model for storing user and Groq's chat history as JSON
class ChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transcript = models.JSONField()  # Store the chat session as JSON
    timestamp = models.DateTimeField(auto_now_add=True)  # When the chat happened

    def __str__(self):
        return f"Chat by {self.user.username} on {self.timestamp}"

class JournalEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    groq_response = models.TextField()  # Store Groq's response here
    timestamp = models.DateTimeField(auto_now_add=True)  # When the journal entry was created

    def __str__(self):
        return f"Journal Entry for {self.user.username} on {self.timestamp}"