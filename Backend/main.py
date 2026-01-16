from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List
from datetime import timedelta
from sqlalchemy.orm import Session  # session for DB operations
from fastapi.middleware.cors import CORSMiddleware

import src.config as sec ## security Configs
from src.Model.User import Token, UserCreate, UserResponse, TokenData ## Pydantic Models
from src.Database.database_userModel import User ## SQLAlchemy Models
from src.Database.dataBase import engine, SessionLocal, Base ## DB Configs
from src.utils import verify_Password, get_pwd_hash, create_access_token, verify_token

from src.Model.Product import Products
from src.Database import database_productModel
from src.json.dummyProducts import dummy_products


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# create the database tables
Base.metadata.create_all(bind=engine)
# create the FastAPI app
app  = FastAPI(title="User Management API with Auth")
## Dependency to get DB session
def get_db():   
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
)

        
## Auth Dependent to get current active user
## Auth Dependecy
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print(f"1 inside get_current_user function : {token}")
    token_data = verify_token(token) ## get the TokenData
    user = db.query(User).filter(token_data.email == User.email).first() 
    if not  user:
        raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Opps User Not Found",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return user 

def get_current_active_user(current_user: User = Depends(get_current_user)):
    print(f"1 inside get_current_active_user function : {current_user}")
    if not current_user.is_active:
        raise HTTPException(
                status_code=404,
                detail="Inactive User",
            )    
    return current_user

@app.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code= 404,
            detail="User already Exists"
        )
    hash_pwd = get_pwd_hash(user.password)
    db_user = User(
        name = user.name,
        email = user.email,
        role = user.role,
        hashed_password = hash_pwd
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
    
 ## Login   
@app.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    ## 1) search user in db
    user = db.query(User).filter(User.email == form_data.username).first()
    ## 2) verify if user exists and verify password
    if not user or not verify_Password(form_data.password,user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="wrong creditionals"
        )
    ## 3) user is inactive
    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="inactive user"
        )
        
    access_token_expires = timedelta(minutes=sec.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
        
@app.get("/profile", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_active_user)):
    return current_user

    
@app.get("/verify-token", response_model=TokenData)    
def verify_token_endpoint(current_user: User = Depends(get_current_active_user)):
    return {
        "valid": True,
        "user":{
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
        }
    }

@app.get("/users/", response_model=List[UserResponse])
def  get_users(current_user: User = Depends(get_current_active_user),db: Session =Depends(get_db)):
    print(f"1 inside get_users function : {current_user}")
    users = db.query(User).all()
    return users  

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hash_pwd = get_pwd_hash(user.password)
    db_user = User(
        name=user.name,
        email=user.email,
        role=user.role,
        hashed_password=hash_pwd
    )   
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserCreate,current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_user.name = user.name 
    db_user.email = user.email
    db_user.role = user.role
    db_user.hashed_password = get_pwd_hash(user.password)
    
    db.commit()
    db.refresh(db_user)
    return db_user


@app.delete("/users/{user_id}")
def delete_user(user_id: int, current_user: User = Depends(get_current_active_user),db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    db.delete(db_user)
    db.commit()
    return {"detail": "User deleted successfully"}

##**************** product APIs ******************##

def init__db():
    db = SessionLocal()
    count = db.query(database_productModel.Product).count()
    print("COunt of products in DB :", count)
    if count == 0 :
        for product in dummy_products:
            db.add(database_productModel.Product(**product.model_dump()))
        db.commit()
    
init__db()

@app.get("/products")
def get_products(db : Session = Depends(get_db)):
    db_products = db.query(database_productModel.Product).all()
    return db_products

@app.get("/products/{id}")  
async def  get_product_by_id(id: int, db: Session = Depends(get_db)):
    db_product =  db.query(database_productModel.Product).filter(database_productModel.Product.id == id).first()
    return f"No Product found with product id :{id}" if db_product is None else db_product

@app.post("/products")
def add_product(product: Products, db: Session = Depends(get_db)):
    db.add(database_productModel.Product(**product.model_dump()))
    db.commit()
    return product


@app.put("/products/{id}")
def update_product(id: int, product: Products, db: Session = Depends(get_db)):
    db_product = db.query(database_productModel.Product).filter(database_productModel.Product.id == id).first()
    if db_product:
        db_product.name = product.name or db_product.name
        db_product.description = product.description or db_product.description
        db_product.price = product.price or db_product.price
        db_product.quantity = product.quantity or db_product.quantity
        db.commit()
        return f"product with id : {id} updated successfully"
    else:   
        return {"error": "no such Product exists to update"}

@app.delete("/products/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    db_produc = db.query(database_productModel.Product).filter(database_productModel.Product.id == id).first()
    if db_produc:
        db.delete(db_produc)
        db.commit()
        return f"Product with id : {id} deleted successfully"
    else:
        return {"error": "Product not found"}