import csv
import io
import datetime
import json
from django.utils import timezone
from .models import Movie, Tags, MovieUpload


def process_csv_file(upload_id):
    """
    处理上传的CSV文件并添加到电影数据库
    
    CSV格式应为:
    name,director,country,years,leader,d_rate_nums,d_rate,intro,tags
    
    其中tags是以|分隔的标签列表
    """
    try:
        upload = MovieUpload.objects.get(id=upload_id)
        upload.status = "processing"
        upload.save()
        
        # 读取CSV文件
        csv_file = upload.csv_file
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        processed_count = 0
        imported_movie_ids = []  # 用于存储导入的电影ID
        
        # 打印CSV内容进行调试
        print(f"Processing CSV file: {upload.csv_file.name}")
        rows = list(reader)
        print(f"Found {len(rows)} rows in CSV")
        
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
                if Movie.objects.filter(name=row['name']).exists():
                    print(f"Movie already exists: {row['name']}")
                    continue
                
                # 处理日期格式
                try:
                    years_date = datetime.datetime.strptime(row['years'], '%Y-%m-%d').date()
                except ValueError as e:
                    print(f"Date format error: {e}")
                    # 尝试其他常见格式
                    try:
                        years_date = datetime.datetime.strptime(row['years'], '%Y/%m/%d').date()
                    except ValueError as e:
                        print(f"Alternative date format error: {e}")
                        continue
                
                # 创建电影记录
                movie = Movie(
                    name=row['name'],
                    director=row.get('director', '未知'),
                    country=row.get('country', '未知'),
                    years=years_date,
                    leader=row.get('leader', '未知'),
                    d_rate_nums=int(row.get('d_rate_nums', 0)),
                    d_rate=row.get('d_rate', '0'),
                    intro=row.get('intro', ''),
                    num=0,
                    douban_link=row.get('douban_link', ''),
                    douban_id=row.get('douban_id', '')
                )
                
                # 保存电影以获取ID
                movie.save()
                print(f"Saved movie: {movie.name} with ID: {movie.id}")
                
                # 添加到导入的电影ID列表
                imported_movie_ids.append(movie.id)
                
                # 处理标签
                if 'tags' in row and row['tags']:
                    tag_names = row['tags'].split('|')
                    for tag_name in tag_names:
                        tag_name = tag_name.strip()
                        if tag_name:
                            # 获取或创建标签
                            tag, created = Tags.objects.get_or_create(name=tag_name)
                            movie.tags.add(tag)
                            print(f"Added tag: {tag_name} to movie: {movie.name}")
                
                processed_count += 1
            except Exception as e:
                # 记录错误但继续处理
                print(f"Error processing row: {e}")
                continue
        
        # 更新上传状态并保存导入的电影ID
        upload.status = "completed"
        upload.processed_count = processed_count
        upload.notes = json.dumps({'imported_movie_ids': imported_movie_ids})
        upload.save()
        
        print(f"CSV processing completed. Processed {processed_count} movies. Imported IDs: {imported_movie_ids}")
        return processed_count
    except Exception as e:
        # 处理整体失败
        print(f"CSV processing failed with error: {e}")
        if 'upload' in locals():
            upload.status = "failed"
            upload.save()
        return 0 