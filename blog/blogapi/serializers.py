from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import BlogPost, Comment, UserProfile, Notification, Like
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# ================= AUTH =================
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        username_or_email = attrs.get("username")
        password = attrs.get("password")

        user = User.objects.filter(email=username_or_email).first()
        if user:
            username = user.username
        else:
            username = username_or_email

        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid credentials")

        data = super().validate({"username": username, "password": password})
        data['user'] = {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
        return data

# ================= BLOG POSTS =================
class BlogPostSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    video = serializers.FileField(required=False)
    likes_count = serializers.SerializerMethodField()
    liked_by_user = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = BlogPost
        fields = '__all__'
        read_only_fields = ['author', 'created_at']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_liked_by_user(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and user in obj.likes.all()

    def get_is_bookmarked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.bookmarked_by.filter(id=user.id).exists()
        return False

# ================= COMMENTS =================
class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    like_count = serializers.SerializerMethodField()
    liked_by_user = serializers.SerializerMethodField()
    author = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'author', 'content', 'created_at', 'like_count', 'liked_by_user']

    def get_like_count(self, obj):
        return obj.liked_by.count()

    def get_liked_by_user(self, obj):
        user = self.context['request'].user
        return user.is_authenticated and user in obj.liked_by.all()

# ================= USER PROFILES =================
class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', read_only=True)
    avatar = serializers.ImageField(required=False)
    posts = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    role = serializers.CharField(required=False)

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'avatar', 'bio', 'role', 'posts', 'comments']

    def get_posts(self, obj):
        return BlogPost.objects.filter(author=obj.user).values()

    def get_comments(self, obj):
        return Comment.objects.filter(author=obj.user).values()

class PublicBlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'content', 'created_at']

class PublicCommentSerializer(serializers.ModelSerializer):
    post_title = serializers.CharField(source='post.title', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'content', 'post_title', 'created_at']

class PublicUserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    avatar = serializers.ImageField()
    posts = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    role = serializers.CharField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['username', 'avatar', 'bio', 'role', 'posts', 'comments']

    def get_posts(self, obj):
        posts = BlogPost.objects.filter(author=obj.user)
        return PublicBlogPostSerializer(posts, many=True).data

    def get_comments(self, obj):
        comments = Comment.objects.filter(author=obj.user)
        return PublicCommentSerializer(comments, many=True).data

# ================= NOTIFICATIONS =================

class NotificationSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'recipient', 'message', 'is_read', 'timestamp', 'author_username']

# ================= BOOKMARKS =================
class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'content', 'created_at', 'image']

class BlogPostBookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = ['id', 'bookmarked_by']
        read_only_fields = ['bookmarked_by']


# ================= DASHBOARD VIEWS =================
class LikeSerializer(serializers.ModelSerializer):
    post = BlogPostSerializer(read_only=True)  # Includes full post details

    class Meta:
        model = Like
        fields = ['id', 'post', 'created_at']



class TopPostSerializer(serializers.ModelSerializer):
    likes = serializers.IntegerField(source='likes.count', read_only=True)
    author = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = BlogPost
        fields = ['id', 'title', 'likes', 'author', 'created_at']

class PostStatisticsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_posts = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    top_posts = TopPostSerializer(many=True)


class UserRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['role']

    def update(self, instance, validated_data):
        instance.role = validated_data.get('role', instance.role)
        instance.save()
        return instance
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'is_active']