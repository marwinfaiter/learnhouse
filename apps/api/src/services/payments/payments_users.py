from fastapi import HTTPException, Request
from sqlmodel import Session, select
from typing import Any
from src.db.payments.payments_users import PaymentsUser, PaymentStatusEnum, ProviderSpecificData
from src.db.payments.payments_products import PaymentsProduct
from src.db.users import InternalUser, PublicUser, AnonymousUser
from src.db.organizations import Organization
from src.services.orgs.orgs import rbac_check
from datetime import datetime

async def create_payment_user(
    request: Request,
    org_id: int,
    user_id: int,
    product_id: int,
    status: PaymentStatusEnum,
    provider_data: Any,
    current_user: PublicUser | AnonymousUser | InternalUser,
    db_session: Session,
) -> PaymentsUser:
    # Check if organization exists
    statement = select(Organization).where(Organization.id == org_id)
    org = db_session.exec(statement).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # RBAC check
    await rbac_check(request, org.org_uuid, current_user, "create", db_session)

    # Check if product exists
    statement = select(PaymentsProduct).where(
        PaymentsProduct.id == product_id,
        PaymentsProduct.org_id == org_id
    )
    product = db_session.exec(statement).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    provider_specific_data = ProviderSpecificData(
        stripe_customer=provider_data if provider_data else None,
    )

    # Check if user already has a payment user
    statement = select(PaymentsUser).where(
        PaymentsUser.user_id == user_id,
        PaymentsUser.org_id == org_id,
        PaymentsUser.payment_product_id == product_id
    )
    existing_payment_user = db_session.exec(statement).first()

    if existing_payment_user:
        if existing_payment_user.status == PaymentStatusEnum.PENDING:
            # Delete existing pending payment
            db_session.delete(existing_payment_user)
            db_session.commit()
        else:
            raise HTTPException(status_code=400, detail="User already has purchase for this product")

    # Create new payment user
    payment_user = PaymentsUser(
        user_id=user_id,
        org_id=org_id,
        payment_product_id=product_id,
        provider_specific_data=provider_specific_data.model_dump(),
        status=status
    )

    db_session.add(payment_user)
    db_session.commit()
    db_session.refresh(payment_user)

    return payment_user

async def get_payment_user(
    request: Request,
    org_id: int,
    payment_user_id: int,
    current_user: PublicUser | AnonymousUser | InternalUser,
    db_session: Session,
) -> PaymentsUser:
    # Check if organization exists
    statement = select(Organization).where(Organization.id == org_id)
    org = db_session.exec(statement).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # RBAC check
    await rbac_check(request, org.org_uuid, current_user, "read", db_session)

    # Get payment user
    statement = select(PaymentsUser).where(
        PaymentsUser.id == payment_user_id,
        PaymentsUser.org_id == org_id
    )
    payment_user = db_session.exec(statement).first()
    if not payment_user:
        raise HTTPException(status_code=404, detail="Payment user not found")

    return payment_user

async def update_payment_user_status(
    request: Request,
    org_id: int,
    payment_user_id: int,
    status: PaymentStatusEnum,
    current_user: PublicUser | AnonymousUser | InternalUser,
    db_session: Session,
) -> PaymentsUser:
    # Check if organization exists
    statement = select(Organization).where(Organization.id == org_id)
    org = db_session.exec(statement).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # RBAC check
    await rbac_check(request, org.org_uuid, current_user, "update", db_session)

    # Get existing payment user
    statement = select(PaymentsUser).where(
        PaymentsUser.id == payment_user_id,
        PaymentsUser.org_id == org_id
    )
    payment_user = db_session.exec(statement).first()
    if not payment_user:
        raise HTTPException(status_code=404, detail="Payment user not found")

    # Update status
    payment_user.status = status
    payment_user.update_date = datetime.now()

    db_session.add(payment_user)
    db_session.commit()
    db_session.refresh(payment_user)

    return payment_user

async def list_payment_users(
    request: Request,
    org_id: int,
    current_user: PublicUser | AnonymousUser | InternalUser,
    db_session: Session,
) -> list[PaymentsUser]:
    # Check if organization exists
    statement = select(Organization).where(Organization.id == org_id)
    org = db_session.exec(statement).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # RBAC check
    await rbac_check(request, org.org_uuid, current_user, "read", db_session)

    # Get all payment users for org ordered by id
    statement = select(PaymentsUser).where(
        PaymentsUser.org_id == org_id
    ).order_by(PaymentsUser.id.desc()) # type: ignore
    payment_users = list(db_session.exec(statement).all())  # Convert to list

    return payment_users

async def delete_payment_user(
    request: Request,
    org_id: int,
    payment_user_id: int,
    current_user: PublicUser | AnonymousUser | InternalUser,
    db_session: Session,
) -> None:
    # Check if organization exists
    statement = select(Organization).where(Organization.id == org_id)
    org = db_session.exec(statement).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # RBAC check
    await rbac_check(request, org.org_uuid, current_user, "delete", db_session)

    # Get existing payment user
    statement = select(PaymentsUser).where(
        PaymentsUser.id == payment_user_id,
        PaymentsUser.org_id == org_id
    )
    payment_user = db_session.exec(statement).first()
    if not payment_user:
        raise HTTPException(status_code=404, detail="Payment user not found")

    # Delete payment user
    db_session.delete(payment_user)
    db_session.commit()
