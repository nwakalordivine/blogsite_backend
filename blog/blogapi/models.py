from django.db import models
from cloudinary.models import CloudinaryField
from django.contrib.auth.models import User, AbstractUser

class BlogPost(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = CloudinaryField('image', blank=True, null=True)
    video = CloudinaryField('video', blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    tags = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    bookmarked_by = models.ManyToManyField(User, related_name='bookmarked_posts', blank=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    likes_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey('BlogPost', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    liked_by = models.ManyToManyField(User, related_name='liked_comments', blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', default=1)

    def __str__(self):
        return f"{self.author.username} on {self.post.title}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=[('Guest', 'Guest'), ('Author', 'Author')], default='Guest')
    avatar = CloudinaryField('image', blank=True, null=True)
    bio = models.TextField(default="This user has not written a bio yet.")

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message[:20]

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE)

    def __str__(self):
        return f"Like by {self.user} on {self.blog_post}"


class CustomUser(AbstractUser):
    # Add unique related_name attributes to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  # Unique related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',  # Unique related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )