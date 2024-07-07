from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException, status
from pydantic import UUID4

from workout_api.categorias.models import CategoriaModel
from workout_api.categorias.schemas import CategoriaIn, CategoriaOut
from workout_api.contrib.repository.dependencies import DatabaseDependency

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

router = APIRouter()

@router.post(
    "/", 
    summary="Criar nova categoria",
    status_code=status.HTTP_201_CREATED,
    response_model=CategoriaOut
)
async def post(
    db_session: DatabaseDependency, 
    categoria_in: CategoriaIn = Body(...)
) -> CategoriaOut:
    
    categoria_out = CategoriaOut(id=uuid4(), **categoria_in.model_dump())
    categoria_model = CategoriaModel(**categoria_out.model_dump())

    try:
        db_session.add(categoria_model)
        await db_session.commit()
    except IntegrityError as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f"Já existe uma categoria cadastrado com o nome: {categoria_out.nome}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ocorreu um erro ao inserir os dados no banco: {e}"
        )
    
    return categoria_out

@router.get(
    "/", 
    summary="Consultar totas categorias",
    status_code=status.HTTP_200_OK,
    response_model=list[CategoriaOut]
)
async def query(
    db_session: DatabaseDependency, 
) -> list[CategoriaOut]:
    categorias: list[CategoriaOut] = (await db_session.execute(select(CategoriaModel))).scalars().all()
    
    return categorias

@router.get(
    "/{id}", 
    summary="Consultar uma categoria pelo id",
    status_code=status.HTTP_200_OK,
    response_model=CategoriaOut
)
async def query(
    id: UUID4,
    db_session: DatabaseDependency, 
) -> CategoriaOut:
    categoria: CategoriaOut = (await db_session.execute(select(CategoriaModel).filter_by(id=id))).scalars().first()
    
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Categoria não encontrada no id: {id}"
        )

    return categoria