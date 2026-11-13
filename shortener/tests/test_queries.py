import pytest
from django.urls import reverse

from shortener.tests.factories import UrlFactory, UserFactory

LIST_URL = reverse("shortener:url-list")

# 1 query for the urls joined with their owner + 1 query for all their tags
LIST_QUERIES = 2


def make_urls(count):
    UrlFactory.create_batch(count, owner=UserFactory(username="ana"), tags=["Work", "Social"])


@pytest.mark.parametrize("count", [1, 20])
def test_list_query_count_does_not_grow_with_urls(api_client, django_assert_num_queries, count):
    make_urls(count)

    with django_assert_num_queries(LIST_QUERIES):
        response = api_client.get(LIST_URL)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == count
    assert all(url["owner"] == "ana" for url in body)
    assert all(sorted(url["tags"]) == ["Social", "Work"] for url in body)
