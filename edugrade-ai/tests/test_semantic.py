from app.services import semantic_service as sem


def test_self_similarity():
    assert sem.similarity("the missile man of india", "the missile man of india") > 0.99


def test_related_vs_unrelated():
    a = "missile man of india"
    assert sem.similarity(a, "he was known as the missile man of india") > \
           sem.similarity(a, "photosynthesis converts light into chemical energy in plants")