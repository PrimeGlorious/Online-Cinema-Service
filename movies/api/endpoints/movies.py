from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from movies import crud, schemas, models
from movies.api.dependencies import get_db, get_current_user

router = APIRouter(prefix="/movies", tags=["movies"])


@router.post("/", response_model=schemas.MovieRead, status_code=status.HTTP_201_CREATED)
def create_movie(movie: schemas.MovieCreate, db: Session = Depends(get_db)):
    """
    Create a new movie.

    :param movie: Movie data to be created.
    :return: The created movie.
    """
    return crud.create_movie(db, movie)


@router.get("/{movie_id}", response_model=schemas.MovieRead)
def read_movie(movie_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a movie by its ID.

    :param movie_id: ID of the movie to retrieve.
    :raises 404: If movie is not found.
    :return: The requested movie.
    """
    db_movie = crud.get_movie(db, movie_id)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return db_movie


@router.put("/{movie_id}", response_model=schemas.MovieRead)
def update_movie(movie_id: int, movie_update: schemas.MovieUpdate, db: Session = Depends(get_db)):
    """
    Update a movie by its ID.

    :param movie_id: ID of the movie to update.
    :param movie_update: Updated movie data.
    :raises 404: If movie is not found.
    :return: The updated movie.
    """
    db_movie = crud.get_movie(db, movie_id)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return crud.update_movie(db, db_movie, movie_update)


@router.delete("/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    """
    Delete a movie by its ID.

    :param movie_id: ID of the movie to delete.
    :raises 404: If movie is not found.
    """
    db_movie = crud.get_movie(db, movie_id)
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    crud.delete_movie(db, db_movie)


@router.post("/{movie_id}/like", response_model=schemas.MovieLikeCreate)
def like_movie(movie_id: int, like: bool, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """
    Like or dislike a movie.

    :param movie_id: ID of the movie to like/dislike.
    :param like: Boolean flag indicating like (True) or dislike (False).
    :return: Created like record.
    """
    like_data = schemas.MovieLikeCreate(movie_id=movie_id, like=like)
    return crud.create_movie_like(db, user_id=user["id"], like_data=like_data)


@router.post("/{movie_id}/comment", response_model=schemas.MovieComment)
def add_comment(
    movie_id: int,
    comment: schemas.MovieCommentCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Add a comment to a movie.

    :param movie_id: ID of the movie.
    :param comment: Comment content and metadata.
    :raises 400: If movie ID in URL and payload do not match.
    :return: The created comment.
    """
    if comment.movie_id != movie_id:
        raise HTTPException(status_code=400, detail="Movie ID mismatch")
    return crud.create_movie_comment(db, user_id=user["id"], comment_data=comment)


@router.get("/{movie_id}/comments", response_model=List[schemas.MovieComment])
def get_comments(movie_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """
    Retrieve comments for a specific movie.

    :param movie_id: ID of the movie.
    :param skip: Number of records to skip.
    :param limit: Maximum number of comments to return.
    :return: List of comments.
    """
    return crud.get_movie_comments(db, movie_id=movie_id, skip=skip, limit=limit)


@router.post("/{movie_id}/rating", response_model=schemas.MovieRatingBase)
def rate_movie(
    movie_id: int,
    rating: schemas.MovieRatingCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Submit a rating for a movie.

    :param movie_id: ID of the movie.
    :param rating: Rating data.
    :raises 400: If movie ID in URL and payload do not match.
    :return: The created rating.
    """
    if rating.movie_id != movie_id:
        raise HTTPException(status_code=400, detail="Movie ID mismatch")
    return crud.create_movie_rating(db, user_id=user["id"], rating_data=rating)


@router.post("/{movie_id}/favorite", response_model=schemas.MovieFavoriteBase)
def add_favorite(movie_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """
    Add a movie to user's favorites.

    :param movie_id: ID of the movie to add to favorites.
    :return: The created favorite record.
    """
    fav_data = schemas.MovieFavoriteCreate(movie_id=movie_id)
    return crud.add_movie_favorite(db, user_id=user["id"], fav_data=fav_data)


@router.delete("/{movie_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(movie_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    """
    Remove a movie from user's favorites.

    :param movie_id: ID of the movie to remove.
    :raises 404: If favorite record not found.
    """
    removed = crud.remove_movie_favorite(db, user_id=user["id"], movie_id=movie_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Favorite not found")


@router.get("/", response_model=List[schemas.Movie])
def list_movies(
    search: Optional[str] = Query(None, description="Search by title, description, director or actor"),
    year_from: Optional[int] = Query(None),
    year_to: Optional[int] = Query(None),
    imdb_from: Optional[float] = Query(None),
    imdb_to: Optional[float] = Query(None),
    sort_by: Optional[str] = Query(None, description="Sort by price, year, imdb, votes"),
    sort_desc: bool = Query(True, description="Descending sort"),
    skip: int = 0,
    limit: int = 20,
    favorites_only: bool = False,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """
    List movies with optional filters, sorting, and favorites-only mode.

    :param search: Keyword to search in movie fields.
    :param year_from: Filter by minimum release year.
    :param year_to: Filter by maximum release year.
    :param imdb_from: Minimum IMDb score.
    :param imdb_to: Maximum IMDb score.
    :param sort_by: Field to sort by (e.g. price, year).
    :param sort_desc: Sort in descending order if True.
    :param favorites_only: Return only user's favorite movies if True.
    :return: Filtered and sorted list of movies.
    """
    if favorites_only:
        fav_movies_ids = [
            f.movie_id for f in db.query(models.MovieFavorite).filter_by(user_id=user["id"]).all()
        ]
        query = db.query(models.Movie).filter(models.Movie.id.in_(fav_movies_ids))
        movies = query.offset(skip).limit(limit).all()
        return movies
    else:
        _, movies = crud.search_filter_sort_movies(
            db,
            search=search,
            year_from=year_from,
            year_to=year_to,
            imdb_from=imdb_from,
            imdb_to=imdb_to,
            sort_by=sort_by,
            sort_desc=sort_desc,
            skip=skip,
            limit=limit,
        )
        return movies


@router.get("/notifications", response_model=List[schemas.CommentNotification])
def get_notifications(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
):
    """
    Retrieve unread comment notifications for the user.

    :param skip: Number of records to skip.
    :param limit: Maximum number of notifications to return.
    :return: List of notifications.
    """
    return (
        db.query(models.CommentNotification)
        .filter_by(user_id=user["id"])
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """
    Mark a notification as read.

    :param notification_id: ID of the notification to mark as read.
    :raises 404: If notification is not found.
    """
    notification = db.query(models.CommentNotification).filter_by(id=notification_id, user_id=user["id"]).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
