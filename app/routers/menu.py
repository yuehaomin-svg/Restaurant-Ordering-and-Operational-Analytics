from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import DiningTable, MenuCategory, MenuItem
from app.schemas import CategoryCreate, CategoryRead, DiningTableCreate, DiningTableRead, MenuItemCreate, MenuItemRead

router = APIRouter(prefix="/api", tags=["menu"])


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(database: Session = Depends(get_db)) -> list[MenuCategory]:
    return list(database.scalars(select(MenuCategory).order_by(MenuCategory.name)))


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, database: Session = Depends(get_db)) -> MenuCategory:
    if database.scalar(select(MenuCategory).where(MenuCategory.name == payload.name)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category already exists")
    category = MenuCategory(**payload.model_dump())
    database.add(category)
    database.commit()
    return category


@router.get("/menu-items", response_model=list[MenuItemRead])
def list_menu_items(database: Session = Depends(get_db)) -> list[MenuItem]:
    return list(database.scalars(select(MenuItem).order_by(MenuItem.name)))


@router.post("/menu-items", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
def create_menu_item(payload: MenuItemCreate, database: Session = Depends(get_db)) -> MenuItem:
    if not database.scalar(select(MenuCategory).where(MenuCategory.id == payload.category_id)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    menu_item = MenuItem(**payload.model_dump())
    database.add(menu_item)
    database.commit()
    return menu_item


@router.get("/tables", response_model=list[DiningTableRead])
def list_tables(database: Session = Depends(get_db)) -> list[DiningTable]:
    return list(database.scalars(select(DiningTable).order_by(DiningTable.name)))


@router.post("/tables", response_model=DiningTableRead, status_code=status.HTTP_201_CREATED)
def create_table(payload: DiningTableCreate, database: Session = Depends(get_db)) -> DiningTable:
    if database.scalar(select(DiningTable).where(DiningTable.name == payload.name)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Table already exists")
    table = DiningTable(**payload.model_dump())
    database.add(table)
    database.commit()
    return table
