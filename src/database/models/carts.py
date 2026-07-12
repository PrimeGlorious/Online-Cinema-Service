from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import (
    Base,
)

class CartModel(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="cart", uselist=False)

    cart_items: Mapped[list["CartItemModel"]] = relationship("CartItemModel", back_populates="cart", cascade="all, delete-orphan")


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"),
        unique=False,
        nullable=False
    )
    cart: Mapped["CartModel"] = relationship(
        "CartModel",
        back_populates="cart_items"
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id",
                   ondelete="CASCADE"),
        unique=False,
        nullable=False
    )
    movie: Mapped["MovieModel"] = relationship(
        "MovieModel",
        back_populates="cart_items"
    )
    added_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "movie_id",
            "cart_id",
            name="unique_movie_cart_constraint"
        ),
    )
