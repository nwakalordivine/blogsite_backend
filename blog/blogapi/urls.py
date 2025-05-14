from django.urls import path
from .views import (
    RegisterView, BlogPostListCreateView, BlogPostDetailView, 
    CommentListCreateView, DashboardUserPostsView, DashboardUserCommentsView, 
    DashboardLikedContentView, DashboardUserNotificationsView, LogoutView, 
    CustomTokenObtainPairView, UserProfileView, PublicUserProfileView, 
    LikePostView, NotificationListView, BlogPostSearchFilterView, UserListView,
    CommentDetailView, PostStatisticsView, UserRoleUpdateView, TrendingPostsView, LikeCommentView, CommentLikeCountView, MarkNotificationAsReadView
)
from rest_framework_simplejwt.views import TokenRefreshView



urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),  # Login with email
    path('auth/logout/', LogoutView.as_view(), name='logout'),  # Logout (invalidate refresh token)
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Blog posts
    path('posts/', BlogPostListCreateView.as_view(), name='post-list-create'),
    path('posts/<int:post_id>/', BlogPostDetailView.as_view(), name='post-detail'),
    
    # Comments
    path('comments/<int:post_id>/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('comments/<int:comment_id>/', CommentDetailView.as_view(), name='comment-detail'),
    
    # User Profile
    path('users/me/', UserProfileView.as_view(), name='user-profile'),
    path("profiles/<int:user_id>/", PublicUserProfileView.as_view(), name="public-user-profile"),  # Corrected the lookup parameter
    
    # Likes
    path('likes/<int:post_id>/', LikePostView.as_view(), name='like-post'),
    
    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:id>/', MarkNotificationAsReadView.as_view(), name="mark-notification-read"),

    
    # Search and Filter
    path('posts/search-filter/', BlogPostSearchFilterView.as_view(), name='post-search-filter'),
    
    # Dashboard views (User-specific content)
    path('dashboard/posts/', DashboardUserPostsView.as_view(), name='dashboard-user-posts'),
    path('dashboard/comments/', DashboardUserCommentsView.as_view(), name='dashboard-user-comments'),
    path('dashboard/likes/', DashboardLikedContentView.as_view(), name='dashboard-user-likes'),
    path('dashboard/notifications/', DashboardUserNotificationsView.as_view(), name='dashboard-user-notifications'),
    
    # Post statistics
    path('api/stats/posts/', PostStatisticsView.as_view(), name='post_statistics'),

    path('users/role/', UserRoleUpdateView.as_view(), name="user-role-update"),
    path('posts/trending/', TrendingPostsView.as_view(), name="trending-posts"),
    path('like/comment/<int:comment_id>/', LikeCommentView.as_view(), name="like-comment"),
    path('like/comment/<int:comment_id>/', CommentLikeCountView.as_view(), name="comment-like-count"),
    path('admin/users/', UserListView.as_view(), name="user-list")


]



