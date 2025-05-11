# coding=utf-8
"""


"""
from django.urls import path

from user import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout, name="logout"),
    path("all_movie/", views.index, name="all_movie"),
    path("movie/<int:movie_id>/", views.movie, name="movie"),
    path("score/<int:movie_id>/", views.score, name="score"),
    path("comment/<int:movie_id>/", views.make_comment, name="comment"),
    path("like_comment/<int:comment_id>/<int:movie_id>/", views.like_comment, name="like_comment"),
    path("unlike_comment/<int:comment_id>/<int:movie_id>/", views.unlike_comment, name="unlike_comment"),
    path("collect/<int:movie_id>/", views.collect, name="collect"),
    path("decollect/<int:movie_id>/", views.decollect, name="decollect"),
    path("personal/", views.personal, name="personal"),
    path("mycollect/", views.mycollect, name="mycollect"),
    path("my_comments/", views.my_comments, name="my_comments"),
    path("my_rate/", views.my_rate, name="my_rate"),
    path("delete_comment/<int:comment_id>", views.delete_comment, name="delete_comment"),
    path("delete_rate/<int:rate_id>", views.delete_rate, name="delete_rate"),
    # 收藏最多
    path("hot_movie/", views.hot_movie, name="hot_movie"),
    path("most_view/", views.most_view, name="most_view"),
    path("most_mark/", views.most_mark, name="most_mark"),
    path("latest_movie/", views.latest_movie, name="latest_movie"),
    # path("mark_sort/", views.mark_sort, name="mark_sort"),
    path("search/", views.search, name="search"),
    path("all_tags/", views.all_tags, name="all_tags"),
    path("one_tag/<int:one_tag_id>/", views.one_tag, name="one_tag"),
    path("choose_tags/", views.choose_tags, name="choose_tags"),
    path("director_movie/<str:director_name>", views.director_movie, name="director_movie"),
    path("user_recommend/", views.user_recommend, name="user_recommend"),
    path("item_recommend/", views.item_recommend, name="item_recommend"),
    path("user_recommend_view/", views.user_recommend_view, name="user_recommend_view"),
    path("item_recommend_view/", views.item_recommend_view, name="item_recommend_view"),
    
    # Analytics Dashboard
    path("analytics/", views.analytics_dashboard, name="analytics_dashboard"),
    path("api/tag_distribution/", views.tag_distribution_api, name="tag_distribution_api"),
    path("api/tag_ratings/", views.tag_ratings_api, name="tag_ratings_api"),
    path("api/top_rated_movies/", views.top_rated_movies_api, name="top_rated_movies_api"),
    
    # 电影上传和管理
    path("upload_movie_csv/", views.upload_movie_csv, name="upload_movie_csv"),
    path("movie_upload_list/", views.movie_upload_list, name="movie_upload_list"),
    path("upload_status/<int:upload_id>/", views.upload_status, name="upload_status"),
    path("upload_movie_list/<int:upload_id>/", views.upload_movie_list, name="upload_movie_list"),
    path("add_movie_manual/", views.add_movie_manual, name="add_movie_manual"),
    path("get_csv_template/", views.get_csv_template, name="get_csv_template"),
    
    # 共享推荐功能
    path("create_share/", views.create_shared_recommendation, name="create_share"),
    path("my_shares/", views.view_my_shares, name="view_my_shares"),
    path("edit_share/<int:share_id>/", views.edit_share, name="edit_share"),
    path("delete_share/<int:share_id>/", views.delete_share, name="delete_share"),
    path("shared/<str:share_key>/", views.view_shared, name="view_shared"),
    path("shared_with_me/", views.shared_with_me, name="shared_with_me"),
]
