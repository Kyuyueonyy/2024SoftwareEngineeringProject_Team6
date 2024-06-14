from app import app, db
from app.models import User, Post, Comment

# 애플리케이션 컨텍스트를 명시적으로 설정
with app.app_context():
    db.drop_all()  # 기존 테이블 삭제
    db.create_all()  # 테이블 생성
