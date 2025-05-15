import numpy as np
import pandas as pd
from math import sqrt
import pickle
import os
from flask import current_app
from models.models import User, Movie, Rate
from datetime import datetime, timedelta

# 为了保持与原始代码相似，我们定义相同的缓存键
USER_CACHE = "recommend_for_user_{user_id}"
ITEM_CACHE = "recommend_for_item_{item_id}"


# 加载或创建物品相似度矩阵
def load_item_sim_matrix():
    matrix_file = os.path.join(current_app.root_path, 'data', 'item_rec.pkl')
    if os.path.exists(matrix_file):
        with open(matrix_file, 'rb') as f:
            return pickle.load(f)
    else:
        return {}


# 保存物品相似度矩阵
def save_item_sim_matrix(matrix):
    matrix_file = os.path.join(current_app.root_path, 'data', 'item_rec.pkl')
    os.makedirs(os.path.dirname(matrix_file), exist_ok=True)
    with open(matrix_file, 'wb') as f:
        pickle.dump(matrix, f)


# 更新物品相似度矩阵
def update_item_movie_sim_matrix():
    from flask import current_app
    from models.models import Rate, Movie
    from sqlalchemy import func

    # 从数据库获取所有评分数据
    rate_data = Rate.query.all()
    if not rate_data:
        return {}

    # 处理评分数据
    data = {}
    for rate in rate_data:
        user_id = rate.user_id
        movie_id = rate.movie_id
        mark = rate.mark
        if user_id not in data:
            data[user_id] = {}
        data[user_id][movie_id] = mark

    # 获取所有电影
    movies = Movie.query.all()
    movie_ids = [movie.id for movie in movies]

    # 计算相似度矩阵
    sim_matrix = {}
    for m1 in movie_ids:
        sim_matrix[m1] = {}
        for m2 in movie_ids:
            if m1 == m2:
                sim_matrix[m1][m2] = 1.0
                continue

            # 找到同时评价两部电影的用户
            users = []
            for user, movies in data.items():
                if m1 in movies and m2 in movies:
                    users.append(user)

            if len(users) == 0:
                sim_matrix[m1][m2] = 0
                continue

            # 计算皮尔逊相关系数
            ratings1 = [data[user][m1] for user in users]
            ratings2 = [data[user][m2] for user in users]

            sum1 = sum(ratings1)
            sum2 = sum(ratings2)

            sum1_sq = sum([pow(i, 2) for i in ratings1])
            sum2_sq = sum([pow(i, 2) for i in ratings2])

            product_sum = sum([ratings1[i] * ratings2[i] for i in range(len(users))])

            num = product_sum - (sum1 * sum2 / len(users))
            den = sqrt((sum1_sq - pow(sum1, 2) / len(users)) * (sum2_sq - pow(sum2, 2) / len(users)))

            if den == 0:
                sim_matrix[m1][m2] = 0
            else:
                sim_matrix[m1][m2] = num / den

    # 保存相似度矩阵
    save_item_sim_matrix(sim_matrix)
    return sim_matrix


# 基于用户的协同过滤推荐
def user_cf(target_user_id, n_items=15):
    from flask import current_app
    from models.models import Rate, User, Movie
    from sqlalchemy import func

    # 获取目标用户的评分数据
    target_user_rates = Rate.query.filter_by(user_id=target_user_id).all()
    if not target_user_rates:
        # 如果用户没有评分，则返回浏览量最高的电影
        return Movie.query.order_by(Movie.num.desc()).limit(n_items).all()

    # 获取所有用户的评分数据
    all_rates = Rate.query.all()

    # 构建用户-电影评分矩阵
    user_movie_matrix = {}
    for rate in all_rates:
        user_id = rate.user_id
        movie_id = rate.movie_id
        mark = rate.mark
        if user_id not in user_movie_matrix:
            user_movie_matrix[user_id] = {}
        user_movie_matrix[user_id][movie_id] = mark

    # 目标用户已评分电影集合
    target_user_movies = set(rate.movie_id for rate in target_user_rates)

    # 计算用户间相似度
    user_similarity = {}
    for user_id in user_movie_matrix:
        if user_id == target_user_id:
            continue

        # 找到两个用户共同评分的电影
        common_movies = set(user_movie_matrix[user_id].keys()) & target_user_movies
        if len(common_movies) == 0:
            continue

        # 计算皮尔逊相关系数
        ratings1 = [user_movie_matrix[target_user_id][movie_id] for movie_id in common_movies]
        ratings2 = [user_movie_matrix[user_id][movie_id] for movie_id in common_movies]

        sum1 = sum(ratings1)
        sum2 = sum(ratings2)

        sum1_sq = sum([pow(i, 2) for i in ratings1])
        sum2_sq = sum([pow(i, 2) for i in ratings2])

        product_sum = sum([ratings1[i] * ratings2[i] for i in range(len(common_movies))])

        num = product_sum - (sum1 * sum2 / len(common_movies))
        den = sqrt((sum1_sq - pow(sum1, 2) / len(common_movies)) * (sum2_sq - pow(sum2, 2) / len(common_movies)))

        if den == 0:
            similarity = 0
        else:
            similarity = num / den

        user_similarity[user_id] = similarity

    # 按相似度排序，找到最相似的用户
    sorted_similarity = sorted(user_similarity.items(), key=lambda x: x[1], reverse=True)

    # 获取推荐的电影
    recommendations = {}
    for user_id, _ in sorted_similarity[:5]:  # 选择前5个最相似的用户
        user_rates = user_movie_matrix[user_id]
        for movie_id, rating in user_rates.items():
            if movie_id not in target_user_movies:  # 推荐用户未评分的电影
                if movie_id not in recommendations:
                    recommendations[movie_id] = {'score': 0, 'weight_sum': 0}
                recommendations[movie_id]['score'] += rating * user_similarity[user_id]
                recommendations[movie_id]['weight_sum'] += abs(user_similarity[user_id])

    # 计算加权评分
    for movie_id in recommendations:
        if recommendations[movie_id]['weight_sum'] > 0:
            recommendations[movie_id]['final_score'] = recommendations[movie_id]['score'] / recommendations[movie_id][
                'weight_sum']
        else:
            recommendations[movie_id]['final_score'] = 0

    # 按最终评分排序
    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1]['final_score'], reverse=True)

    # 获取推荐电影ID列表
    recommended_movie_ids = [movie_id for movie_id, _ in sorted_recommendations[:n_items]]

    # 如果推荐数量不足，添加浏览量最高的未评分电影
    if len(recommended_movie_ids) < n_items:
        # 获取目标用户未评分的电影，按浏览量排序
        additional_movies = Movie.query.filter(
            ~Movie.id.in_(list(target_user_movies) + recommended_movie_ids)).order_by(Movie.num.desc()).limit(
            n_items - len(recommended_movie_ids)).all()
        recommended_movie_ids += [movie.id for movie in additional_movies]

    # 返回推荐电影对象列表
    return Movie.query.filter(Movie.id.in_(recommended_movie_ids)).all()


# 基于用户的推荐入口函数
def recommend_by_user_id(user_id, n_items=15):
    """基于用户的协同过滤推荐"""
    return user_cf(user_id, n_items)


# 基于物品的推荐入口函数
def recommend_by_item_id(user_id, n_items=15):
    """基于物品的协同过滤推荐"""
    from flask import current_app
    from models.models import Rate, Movie

    # 获取目标用户的评分数据
    user_rates = Rate.query.filter_by(user_id=user_id).all()

    if not user_rates:
        # 如果用户没有评分，则返回浏览量最高的电影
        return Movie.query.order_by(Movie.num.desc()).limit(n_items).all()

    # 加载物品相似度矩阵
    item_sim_matrix = load_item_sim_matrix()
    if not item_sim_matrix:
        item_sim_matrix = update_item_movie_sim_matrix()

    # 用户已评分电影ID和分数
    user_rate_dict = {rate.movie_id: rate.mark for rate in user_rates}

    # 推荐分数字典
    recommendations = {}

    # 计算推荐分数
    for movie_id, rating in user_rate_dict.items():
        if movie_id not in item_sim_matrix:
            continue

        for similar_movie_id, similarity in item_sim_matrix[movie_id].items():
            # 跳过用户已评分的电影
            if similar_movie_id in user_rate_dict:
                continue

            if similar_movie_id not in recommendations:
                recommendations[similar_movie_id] = {'score': 0, 'weight_sum': 0}

            recommendations[similar_movie_id]['score'] += similarity * rating
            recommendations[similar_movie_id]['weight_sum'] += abs(similarity)

    # 计算加权评分
    for movie_id in recommendations:
        if recommendations[movie_id]['weight_sum'] > 0:
            recommendations[movie_id]['final_score'] = recommendations[movie_id]['score'] / recommendations[movie_id][
                'weight_sum']
        else:
            recommendations[movie_id]['final_score'] = 0

    # 按最终评分排序
    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1]['final_score'], reverse=True)

    # 获取推荐电影ID列表
    recommended_movie_ids = [movie_id for movie_id, _ in sorted_recommendations[:n_items]]

    # 如果推荐数量不足，添加浏览量最高的未评分电影
    if len(recommended_movie_ids) < n_items:
        # 获取用户未评分的电影，按浏览量排序
        rated_movie_ids = list(user_rate_dict.keys()) + recommended_movie_ids
        additional_movies = Movie.query.filter(~Movie.id.in_(rated_movie_ids)).order_by(Movie.num.desc()).limit(
            n_items - len(recommended_movie_ids)).all()
        recommended_movie_ids += [movie.id for movie in additional_movies]

    # 返回推荐电影对象列表
    return Movie.query.filter(Movie.id.in_(recommended_movie_ids)).all()
