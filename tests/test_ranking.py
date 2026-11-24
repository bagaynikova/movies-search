import pytest

from utils.ranking import weighted_rating


def test_weighted_rating_is_between_movie_and_catalog_rating():
    assert weighted_rating(9.0, 100, 7.0, 100) == pytest.approx(8.0)


def test_weighted_rating_with_no_votes_and_zero_threshold():
    assert weighted_rating(0.0, 0, 7.0, 0) == 0.0


def test_weighted_rating_moves_toward_catalog_mean_for_few_votes():
    result = weighted_rating(10.0, 1, 6.0, 100)
    assert 6.0 < result < 6.1


def test_weighted_rating_rejects_negative_vote_count():
    with pytest.raises(ValueError):
        weighted_rating(8.0, -1, 7.0, 100)