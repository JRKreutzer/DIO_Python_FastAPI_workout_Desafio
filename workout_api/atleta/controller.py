from datetime import datetime
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException, Query, status
from fastapi_pagination import LimitOffsetPage, paginate
from fastapi_pagination.utils import disable_installed_extensions_check
from pydantic import UUID4

from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaUpdate, AtletaDesafio, AtletaBasicOut
from workout_api.atleta.models import AtletaModel
from workout_api.contrib.repository.dependencies import DatabaseDependency

from workout_api.categorias.models import CategoriaModel
from workout_api.centro_treinamento.models import CentroTreinamentoModel

from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

router = APIRouter()

@router.post(
    "/", 
    summary="Criar novo atleta",
    status_code=status.HTTP_201_CREATED,
    response_model=AtletaOut
)
async def post(
    db_session: DatabaseDependency, 
    atleta_in: AtletaIn = Body(...)
):
    categoria_name = atleta_in.categoria.nome
    categoria = (await db_session.execute(select(CategoriaModel).filter_by(nome=categoria_name))).scalars().first()
    
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Categoria {categoria_name} não encontrada"
        )
    
    centro_treinamento_name = atleta_in.centro_treinamento.nome
    centro_treinamento = (await db_session.execute(select(CentroTreinamentoModel).filter_by(nome=centro_treinamento_name))).scalars().first()
    
    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Centro de treinamento {centro_treinamento_name} não encontrado"
        )
    
    try:
        atleta_out = AtletaOut(id=uuid4(), created_at=datetime.utcnow(), **atleta_in.model_dump())
        atleta_model = AtletaModel(**atleta_out.model_dump(exclude={"categoria", "centro_treinamento"}))
        atleta_model.categoria_id = categoria.pk_id
        atleta_model.centro_treinamento_id = centro_treinamento.pk_id
        db_session.add(atleta_model)
        await db_session.commit()
    except IntegrityError as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f"Já existe um atleta cadastrado com o CPF: {atleta_in.cpf}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocorreu um erro ao inserir os dados no banco"
        )

    return atleta_out


@router.get(
    '/', 
    summary='Consultar todos os Atletas',
    status_code=status.HTTP_200_OK,
    response_model=LimitOffsetPage[AtletaDesafio],
)
async def query(
    db_session: DatabaseDependency,
    nome: Optional[str] = Query(None, description="Filtrar por nome atleta"),
    cpf: Optional[str] = Query(None, description="Filtrar por nome atleta"),
    limit: int = Query(20, description="Número máximo de registros por página"),
    offset: int = Query(0, description="Número de registros a pular")
) -> LimitOffsetPage[AtletaDesafio]:
    
    query = select(AtletaModel)

    if nome:
        query = query.filter(AtletaModel.nome == nome)
    if cpf:
        query = query.filter(AtletaModel.cpf == cpf)
    
    atletas: LimitOffsetPage[AtletaDesafio] = (await db_session.execute(query)).scalars().all()

    return paginate(atletas)




@router.get(
    "/{id}", 
    summary="Consultar um atleta pelo id",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut
)
async def query(
    id: UUID4,
    db_session: DatabaseDependency, 
) -> AtletaOut:
    atleta: AtletaOut = (await db_session.execute(select(AtletaModel).filter_by(id=id))).scalars().first()
    
    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Atleta não encontrado no id: {id}"
        )

    return atleta

@router.patch(
    "/{id}", 
    summary="Editar um atleta pelo id",
    status_code=status.HTTP_200_OK,
    response_model=AtletaOut
)
async def query(
    id: UUID4,
    db_session: DatabaseDependency,
    atleta_up: AtletaUpdate = Body(...)
) -> AtletaOut:
    atleta: AtletaOut = (await db_session.execute(select(AtletaModel).filter_by(id=id))).scalars().first()
    
    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Atleta não encontrado no id: {id}"
        )

    atleta_update = atleta_up.model_dump(exclude_unset=True)
    
    for key, value in atleta_update.items():
        setattr(atleta, key, value)
    
    await db_session.commit()
    await db_session.refresh(atleta)

    return atleta

@router.delete(
    "/{id}", 
    summary="Deletar um atleta pelo id",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def query(
    id: UUID4,
    db_session: DatabaseDependency, 
) -> None:
    atleta: AtletaOut = (await db_session.execute(select(AtletaModel).filter_by(id=id))).scalars().first()
    
    if not atleta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Atleta não encontrado no id: {id}"
        )

    await db_session.delete(atleta)
    await db_session.commit()