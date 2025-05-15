import os
import csv
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

def allowed_file(filename, allowed_extensions=None):
    """检查文件扩展名是否允许"""
    if allowed_extensions is None:
        allowed_extensions = current_app.config['ALLOWED_EXTENSIONS']
        
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_file(file, directory=None):
    """保存文件到服务器"""
    if directory is None:
        directory = current_app.config['UPLOAD_FOLDER']
        
    # 确保目录存在
    os.makedirs(directory, exist_ok=True)
    
    # 生成安全的文件名
    filename = secure_filename(file.filename)
    
    # 保存文件
    file_path = os.path.join(directory, filename)
    file.save(file_path)
    
    # 返回相对路径，这里只返回文件名而不是完整路径，避免目录重复问题
    # 如果目录是 media/movie_uploads，则只需返回 movie_uploads/filename 即可
    # 避免返回时又加上了目录路径
    base_dir = os.path.basename(directory)
    relative_path = os.path.join(base_dir, filename)
    return relative_path

def process_csv_file(file_path, upload_id=None):
    """
    处理CSV文件中的电影数据
    
    CSV格式应为:
    name,director,country,years,leader,d_rate_nums,d_rate,intro,origin_image_link,douban_link,douban_id,imdb_link,tags
    
    其中tags是以|分隔的标签列表
    """
    from app.models.models import Tags, Movie, MovieUpload
    from app.create_app import db
    
    movies_data = []
    processed_count = 0
    imported_movie_ids = []  # 用于存储导入的电影ID
    
    try:
        # 更新上传状态
        if upload_id:
            try:
                upload = MovieUpload.query.get(upload_id)
                if upload:
                    upload.status = 'processing'
                    db.session.commit()
                    print(f"Updated upload {upload_id} status to 'processing'")
            except Exception as e:
                print(f"Error updating upload status to processing: {str(e)}")
                # 继续处理，不中断
                
        # 打印CSV内容进行调试
        print(f"Processing CSV file: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 尝试检查是否存在包含file_path中的文件名的文件
            # 这是为了处理路径中重复目录的问题
            dirname = os.path.dirname(os.path.dirname(file_path))
            basename = os.path.basename(file_path)
            alternative_path = os.path.join(dirname, basename)
            if os.path.exists(alternative_path):
                print(f"File found at alternative path: {alternative_path}")
                file_path = alternative_path
            else:
                raise FileNotFoundError(f"CSV file not found at: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                csv_reader = csv.DictReader(f)
                rows = list(csv_reader)
                print(f"Found {len(rows)} rows in CSV")
            except Exception as e:
                print(f"Error reading CSV: {str(e)}")
                raise
            
            for row in rows:
                try:
                    # 打印每行数据进行调试
                    print(f"Processing row: {row}")
                    
                    # 检查必填字段
                    required_fields = ['name', 'director', 'country', 'years', 'leader', 'd_rate_nums', 'd_rate']
                    missing_fields = [field for field in required_fields if field not in row or not row[field]]
                    if missing_fields:
                        print(f"Skipping row due to missing fields: {missing_fields}")
                        continue
                    
                    # 检查电影是否已存在
                    existing_movie = Movie.query.filter_by(name=row['name']).first()
                    if existing_movie:
                        print(f"Movie already exists: {row['name']}")
                        
                        # 即使电影存在，也更新标签关系
                        if 'tags' in row and row['tags']:
                            tag_names = row['tags'].split('|') if '|' in row['tags'] else row['tags'].split(',')
                            for tag_name in tag_names:
                                tag_name = tag_name.strip()
                                if not tag_name:
                                    continue
                                    
                                tag = Tags.query.filter_by(name=tag_name).first()
                                if not tag:
                                    tag = Tags(name=tag_name)
                                    db.session.add(tag)
                                    db.session.flush()
                                
                                # 检查电影是否已经关联了该标签
                                if tag not in existing_movie.tags:
                                    existing_movie.tags.append(tag)
                        
                        # 添加到导入的电影ID列表，即使是更新了现有电影
                        imported_movie_ids.append(existing_movie.id)
                        processed_count += 1
                        continue
                    
                    # 处理日期格式
                    try:
                        years_date = datetime.strptime(row['years'], '%Y-%m-%d').date()
                    except ValueError as e:
                        print(f"Date format error: {e}")
                        # 尝试其他常见格式
                        try:
                            years_date = datetime.strptime(row['years'], '%Y/%m/%d').date()
                        except ValueError as e:
                            print(f"Alternative date format error: {e}")
                            continue
                    
                    # 创建新电影
                    movie = Movie(
                        name=row['name'],
                        director=row.get('director', '未知'),
                        country=row.get('country', '未知'),
                        years=years_date,
                        leader=row.get('leader', '未知'),
                        d_rate_nums=int(row.get('d_rate_nums', 0)),
                        d_rate=row.get('d_rate', '0'),
                        intro=row.get('intro', ''),
                        origin_image_link=row.get('origin_image_link', ''),
                        image_link='movie_cover/default.jpg',  # 默认图片，使用正确的路径格式
                        douban_link=row.get('douban_link', ''),
                        douban_id=row.get('douban_id', ''),
                        imdb_link=row.get('imdb_link', '')
                    )
                    
                    # 处理标签
                    if 'tags' in row and row['tags']:
                        tag_names = row['tags'].split('|') if '|' in row['tags'] else row['tags'].split(',')
                        for tag_name in tag_names:
                            tag_name = tag_name.strip()
                            if not tag_name:
                                continue
                                
                            tag = Tags.query.filter_by(name=tag_name).first()
                            if not tag:
                                tag = Tags(name=tag_name)
                                db.session.add(tag)
                                db.session.flush()
                            
                            # 检查电影是否已经关联了该标签
                            if tag not in movie.tags:
                                movie.tags.append(tag)
                            print(f"Added tag: {tag_name} to movie: {movie.name}")
                    
                    db.session.add(movie)
                    db.session.flush()  # 获取ID但不提交
                    
                    # 添加到导入的电影ID列表
                    imported_movie_ids.append(movie.id)
                    processed_count += 1
                    print(f"Added movie: {movie.name} with ID: {movie.id}")
                    
                except Exception as e:
                    # 记录错误但继续处理其他行
                    print(f"Error processing row: {e}")
                    continue
            
            # 提交所有更改
            db.session.commit()
            
            # 更新上传状态
            if upload_id:
                try:
                    upload = MovieUpload.query.get(upload_id)
                    if upload:
                        upload.processed_count = processed_count
                        upload.status = 'completed'
                        upload.notes = json.dumps({'imported_movie_ids': imported_movie_ids})
                        db.session.commit()
                        print(f"Updated upload {upload_id} status to 'completed' with {processed_count} movies")
                except Exception as e:
                    print(f"Error updating upload status to completed: {str(e)}")
                    
            print(f"CSV processing completed. Processed {processed_count} movies. Imported IDs: {imported_movie_ids}")
            return processed_count, "Success"
            
    except Exception as e:
        error_message = f"CSV processing failed with error: {str(e)}"
        print(error_message)
        try:
            db.session.rollback()
            
            # 更新上传状态为失败
            if upload_id:
                try:
                    upload = MovieUpload.query.get(upload_id)
                    if upload:
                        upload.status = 'failed'
                        upload.notes = error_message
                        db.session.commit()
                        print(f"Updated upload {upload_id} status to 'failed'")
                except Exception as inner_e:
                    print(f"Error updating upload status to failed: {str(inner_e)}")
        except Exception as rollback_e:
            print(f"Error during rollback: {str(rollback_e)}")
                
        return 0, error_message 
