from rest_framework import generics, permissions, status, filters
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .serializers import (
    RegisterSerializer, BlogPostSerializer, CommentSerializer,
    UserProfileSerializer, PublicUserProfileSerializer, NotificationSerializer,
    CustomTokenObtainPairSerializer, PostStatisticsSerializer, UserRoleSerializer, UserSerializer
)
from django.db.models import Count
from .models import BlogPost, Comment, UserProfile, Notification
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAdminUser
# ================= AUTH =================
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class TokenRefreshViewCustom(TokenRefreshView):
    pass

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# ================= USER PROFILES =================
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user = self.request.user
        if hasattr(user, 'profile'):
            return user.profile
        raise NotFound("Profile does not exist for this user.")

    def perform_update(self, serializer):
        user = self.request.user
        profile = user.profile
        data = self.request.data
        user.username = data.get('username', user.username)
        user.save()
        serializer.save(user=user)

class PublicUserProfileView(generics.RetrieveAPIView):
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = PublicUserProfileSerializer
    lookup_field = 'user_id'
    permission_classes = []

class UpdateUserRoleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        role = request.data.get("role")
        if role not in ["Guest", "Author"]:
            return Response({"error": "Invalid role."}, status=400)
        profile = request.user.profile
        profile.role = role
        profile.save()
        return Response({"message": "Role updated."})

# ================= POSTS =================
class BlogPostListCreateView(generics.ListCreateAPIView):
    queryset = BlogPost.objects.all().order_by('-created_at')
    serializer_class = BlogPostSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return []

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_context(self):
        return {'request': self.request}

class BlogPostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BlogPost.objects.all()
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.request.user != serializer.instance.author:
            raise PermissionDenied("You can only edit your own posts.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.author:
            raise PermissionDenied("You can only delete your own posts.")
        instance.delete()

    def get_serializer_context(self):
        return {'request': self.request}

class TrendingBlogPostView(generics.ListAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = []

    def get_queryset(self):
        return BlogPost.objects.annotate(like_count=Count('likes')).order_by('-like_count')[:10]

# ================= COMMENTS =================
class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post__id=post_id).order_by('-created_at')

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
        if comment.post.author != self.request.user:
            Notification.objects.create(
                recipient=comment.post.author,
                message=f"{self.request.user.username} commented on your post: '{comment.post.title}'"
            )

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return []

class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.request.user != serializer.instance.author:
            raise PermissionDenied("You can only edit your own comments.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.author:
            raise PermissionDenied("You can only delete your own comments.")
        instance.delete()

# ================= LIKES =================
class LikePostView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, post_id):
        post = get_object_or_404(BlogPost, id=post_id)
        user = request.user
        if user in post.likes.all():
            post.likes.remove(user)
            return Response({'detail': 'Unliked'})
        else:
            post.likes.add(user)
            if post.author != user:
                Notification.objects.create(
                    recipient=post.author,
                    message=f"{user.username} liked your post: '{post.title}'"
                )
            return Response({'detail': 'Liked'})

class PostLikeCountView(APIView):
    def get(self, request, post_id):
        post = get_object_or_404(BlogPost, id=post_id)
        return Response({"likes": post.likes.count()})

class LikeCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        user = request.user
        if user in comment.liked_by.all():
            comment.liked_by.remove(user)
            return Response({'detail': 'Comment unliked'})
        else:
            comment.liked_by.add(user)
            return Response({'detail': 'Comment liked'})

class CommentLikeCountView(APIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        return Response({"likes": comment.liked_by.count()})

# ================= NOTIFICATIONS =================
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-timestamp')

class CreateNotificationView(generics.CreateAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

class MarkNotificationAsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notif.is_read = True
        notif.save()
        return Response({"detail": "Marked as read"})

# ================= SEARCH & FILTER =================
class BlogPostSearchFilterView(generics.ListAPIView):
    queryset = BlogPost.objects.all().order_by('-created_at')
    serializer_class = BlogPostSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['title', 'content', 'tags']
    filterset_fields = ['category', 'tags', 'author__username']

# ================= DASHBOARD =================
class DashboardUserPostsView(generics.ListAPIView):
    serializer_class = BlogPostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BlogPost.objects.filter(author=self.request.user).order_by('-created_at')

class DashboardUserCommentsView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user).order_by('-created_at')

class DashboardLikedContentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        liked_posts = BlogPost.objects.filter(likes=user)
        liked_comments = Comment.objects.filter(liked_by=user)

        post_data = BlogPostSerializer(liked_posts, many=True, context={'request': request}).data
        comment_data = CommentSerializer(liked_comments, many=True).data

        return Response({
            "liked_posts": post_data,
            "liked_comments": comment_data
        })


class DashboardUserNotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-timestamp')


class PostStatisticsView(generics.GenericAPIView):
    serializer_class = PostStatisticsSerializer

    def get(self, request):
        # Query the data needed for statistics
        total_users = User.objects.count()
        total_posts = BlogPost.objects.count()
        total_comments = Comment.objects.count()
        top_posts = BlogPost.objects.annotate(like_count=Count('likes')).order_by('-like_count')[:5]
        
        # Prepare the data to be serialized
        data = {
            "total_users": total_users,
            "total_posts": total_posts,
            "total_comments": total_comments,
            "top_posts": top_posts
        }

        # Serialize the data
        serializer = self.get_serializer(data)
        return Response(serializer.data)
    

class UserRoleUpdateView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRoleSerializer  # Assume you have a serializer for user roles
    permission_classes = [IsAdminUser]  # Only admins can change roles
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        role = request.data.get('role')
        
        # Validate the role before updating (you can define allowed roles in your model)
        if role not in ['Guest', 'Author']:
            return Response({"detail": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)
        
        user.role = role
        user.save()
        return Response({"detail": "Role updated successfully"})
    
class TrendingPostsView(generics.ListAPIView):
    queryset = BlogPost.objects.all().order_by('-likes_count')  # Assuming you track the likes count
    serializer_class = BlogPostSerializer  # Adjust according to your serializer
    pagination_class = None  # Or use pagination if the result is large
    
    def get_queryset(self):
        # You can modify this to return posts with the most likes or comments
        return BlogPost.objects.all().order_by('-likes_count')[:10]  # Top 10 trending posts


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
