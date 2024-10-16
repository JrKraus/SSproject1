from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from typing import List, Optional

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///social_media.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# SQLAlchemy models
class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    is_admin = Column(Boolean, default=False)
    image_url = Column(String)
    posts = relationship("PostDB", back_populates="user")

class PostDB(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    post_text = Column(String)
    likes = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("UserDB", back_populates="posts")

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class UserBase(BaseModel):
    name: str
    is_admin: bool = False
    image_url: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

class PostBase(BaseModel):
    title: str
    post_text: str
    user_id: int

class PostCreate(PostBase):
    pass

class Post(PostBase):
    id: int
    likes: int = 0
    class Config:
        from_attributes = True
       
app = FastAPI()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User Endpoints

@app.post("/users/", response_model=User)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = UserDB(username=user.name, is_admin=user.is_admin, image_url=user.image_url)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return User(id=db_user.id, name=db_user.username, is_admin=db_user.is_admin, image_url=db_user.image_url)

@app.get("/users/", response_model=List[User])
async def get_users(name: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(UserDB)
    if name:
        query = query.filter(UserDB.username.contains(name))
    users = query.all()
    return [User(id=user.id, name=user.username, is_admin=user.is_admin, image_url=user.image_url) for user in users]

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return User(id=db_user.id, name=db_user.username, is_admin=db_user.is_admin, image_url=db_user.image_url)

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.username = user.name
    db_user.is_admin = user.is_admin
    db_user.image_url = user.image_url
    db.commit()
    db.refresh(db_user)
    return User(id=db_user.id, name=db_user.username, is_admin=db_user.is_admin, image_url=db_user.image_url)

@app.patch("/users/{user_id}/name", response_model=User)
async def patch_user_name(user_id: int, name: str, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.username = name
    db.commit()
    db.refresh(db_user)
    return User(id=db_user.id, name=db_user.username, is_admin=db_user.is_admin, image_url=db_user.image_url)

# Post Endpoints

@app.post("/posts/", response_model=Post)
async def create_post(post: PostCreate, db: Session = Depends(get_db)):
    db_post = PostDB(**post.dict())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.post("/posts/", response_model=Post)
async def create_post(post: PostCreate, db: Session = Depends(get_db)):
    db_post = PostDB(title=post.title, post_text=post.text, user_id=post.user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return Post(id=db_post.id, title=db_post.title, post_text=db_post.post_text, user_id=db_post.user_id, likes=db_post.likes)

@app.get("/posts/", response_model=List[Post])
async def get_posts(title: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(PostDB)
    if title:
        query = query.filter(PostDB.title.contains(title))
    posts = query.all()
    return [Post(id=post.id, title=post.title, post_text=post.post_text, user_id=post.user_id, likes=post.likes) for post in posts]

@app.get("/posts/{post_id}", response_model=Post)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(PostDB).filter(PostDB.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return Post(id=db_post.id, title=db_post.title, post_text=db_post.post_text, user_id=db_post.user_id, likes=db_post.likes)

@app.put("/posts/{post_id}", response_model=Post)
async def update_post(post_id: int, post: PostCreate, db: Session = Depends(get_db)):
    db_post = db.query(PostDB).filter(PostDB.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    db_post.title = post.title
    db_post.post_text = post.text
    db_post.user_id = post.user_id
    db.commit()
    db.refresh(db_post)
    return Post(id=db_post.id, title=db_post.title, post_text=db_post.post_text, user_id=db_post.user_id, likes=db_post.likes)

@app.patch("/posts/{post_id}/text", response_model=Post)
async def patch_post_text(post_id: int, text: str, db: Session = Depends(get_db)):
    db_post = db.query(PostDB).filter(PostDB.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    db_post.post_text = text
    db.commit()
    db.refresh(db_post)
    return Post(id=db_post.id, title=db_post.title, post_text=db_post.post_text, user_id=db_post.user_id, likes=db_post.likes)

@app.patch("/posts/{post_id}/likes/increment", response_model=Post)
async def increment_post_likes(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(PostDB).filter(PostDB.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    db_post.likes += 1
    db.commit()
    db.refresh(db_post)
    return db_post

@app.patch("/posts/{post_id}/likes/decrement", response_model=Post)
async def decrement_post_likes(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(PostDB).filter(PostDB.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    db_post.likes = max(0, db_post.likes - 1)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.delete("/posts/{post_id}", response_model=Post)
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(PostDB).filter(PostDB.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(db_post)
    db.commit()
    return db_post

@app.get("/users/", response_model=List[User ])
async def get_users(username: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(UserDB)
    if username:
        query = query.filter(UserDB.username.contains(username))
    print(query.all())  
    return query.all()

@app.get("/users/", response_model=List[User ])
async def get_users(username: Optional[str] = None, db: Session = Depends(get_db)):
        query = db.query(UserDB)
        if username:
            query = query.filter(UserDB.username.contains(username))
        print(query.all())
        
        return query.all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
   

