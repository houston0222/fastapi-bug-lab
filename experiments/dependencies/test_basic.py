from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from typing import Annotated
from fastapi import HTTPException

app = FastAPI()


def get_value():
    return "dependency-value"


@app.get("/test")
def endpoint(value: str = Depends(get_value)):
    return {"value": value}


def test_basic_dependency():
    client = TestClient(app)

    response = client.get("/test")

    assert response.status_code == 200
    assert response.json() == {"value": "dependency-value"}

async def get_async_value():
    return "async-dependency-value"


@app.get("/test-async")
async def async_endpoint(value: str = Depends(get_async_value)):
    return {"value": value}


def test_basic_async_dependency():
    client = TestClient(app)

    response = client.get("/test-async")

    assert response.status_code == 200
    assert response.json() == {"value": "async-dependency-value"}

def get_inner():
    return "inner-value"


def get_outer(inner: str = Depends(get_inner)):
    return f"outer:{inner}"


@app.get("/test-nested")
def nested_endpoint(value: str = Depends(get_outer)):
    return {"value": value}


def test_nested_dependency():
    client = TestClient(app)

    response = client.get("/test-nested")

    assert response.status_code == 200
    assert response.json() == {"value": "outer:inner-value"}


call_count = 0


def get_cached_value():
    global call_count
    call_count += 1
    return call_count


@app.get("/test-cache")
def cache_endpoint(
    first: int = Depends(get_cached_value),
    second: int = Depends(get_cached_value),
):
    return {"first": first, "second": second}


def test_dependency_is_cached():
    global call_count
    call_count = 0

    client = TestClient(app)
    response = client.get("/test-cache")

    assert response.status_code == 200
    assert response.json() == {"first": 1, "second": 1}
    assert call_count == 1


@app.get("/test-no-cache")
def no_cache_endpoint(
    first: int = Depends(get_cached_value),
    second: int = Depends(get_cached_value, use_cache=False),
):
    return {"first": first, "second": second}


def test_dependency_without_cache():
    global call_count
    call_count = 0

    client = TestClient(app)
    response = client.get("/test-no-cache")

    assert response.status_code == 200
    assert response.json() == {"first": 1, "second": 2}
    assert call_count == 2

nested_call_count = 0


def get_nested_counter():
    global nested_call_count
    nested_call_count += 1
    return nested_call_count


def get_nested_cached(
    value: int = Depends(get_nested_counter),
):
    return value


def get_nested_uncached(
    value: int = Depends(get_nested_counter, use_cache=False),
):
    return value


@app.get("/test-nested-cache-interaction")
def nested_cache_interaction_endpoint(
    cached: int = Depends(get_nested_cached),
    uncached: int = Depends(get_nested_uncached),
):
    return {
        "cached": cached,
        "uncached": uncached,
    }


def test_nested_dependency_cache_interaction():
    global nested_call_count
    nested_call_count = 0

    client = TestClient(app)
    response = client.get("/test-nested-cache-interaction")

    assert response.status_code == 200
    assert response.json() == {
        "cached": 1,
        "uncached": 2,
    }
    assert nested_call_count == 2

async def get_async_inner():
    return "async-inner"


def get_sync_outer_from_async(
    value: str = Depends(get_async_inner),
):
    return f"sync-outer:{value}"


@app.get("/test-async-nested")
async def async_nested_endpoint(
    value: str = Depends(get_sync_outer_from_async),
):
    return {"value": value}


def test_async_nested_dependency():
    client = TestClient(app)

    response = client.get("/test-async-nested")

    assert response.status_code == 200
    assert response.json() == {
        "value": "sync-outer:async-inner"
    }

def get_sync_inner():
    return "sync-inner"


async def get_async_outer_from_sync(
    value: str = Depends(get_sync_inner),
):
    return f"async-outer:{value}"


@app.get("/test-sync-async-nested")
def sync_async_nested_endpoint(
    value: str = Depends(get_async_outer_from_sync),
):
    return {"value": value}


def test_sync_endpoint_async_nested_dependency():
    client = TestClient(app)

    response = client.get("/test-sync-async-nested")

    assert response.status_code == 200
    assert response.json() == {
        "value": "async-outer:sync-inner"
    }

async_call_count = 0


async def get_async_counter():
    global async_call_count
    async_call_count += 1
    return async_call_count


@app.get("/test-async-no-cache")
async def async_no_cache_endpoint(
    first: int = Depends(get_async_counter),
    second: int = Depends(get_async_counter, use_cache=False),
):
    return {"first": first, "second": second}


def test_async_dependency_without_cache():
    global async_call_count
    async_call_count = 0

    client = TestClient(app)
    response = client.get("/test-async-no-cache")

    assert response.status_code == 200
    assert response.json() == {
        "first": 1,
        "second": 2,
    }
    assert async_call_count == 2

async_nested_call_count = 0


async def get_async_nested_counter():
    global async_nested_call_count
    async_nested_call_count += 1
    return async_nested_call_count


def get_outer_cached_async(
    value: int = Depends(get_async_nested_counter),
):
    return value


def get_outer_uncached_async(
    value: int = Depends(get_async_nested_counter, use_cache=False),
):
    return value


@app.get("/test-async-nested-no-cache")
async def async_nested_no_cache_endpoint(
    cached: int = Depends(get_outer_cached_async),
    uncached: int = Depends(get_outer_uncached_async),
):
    return {
        "cached": cached,
        "uncached": uncached,
    }


def test_async_nested_dependency_without_cache():
    global async_nested_call_count
    async_nested_call_count = 0

    client = TestClient(app)
    response = client.get("/test-async-nested-no-cache")

    assert response.status_code == 200
    assert response.json() == {
        "cached": 1,
        "uncached": 2,
    }
    assert async_nested_call_count == 2

def get_original_value():
    return "original"


def get_override_value():
    return "override"


@app.get("/test-override")
def override_endpoint(
    value: str = Depends(get_original_value),
):
    return {"value": value}


def test_dependency_override():
    app.dependency_overrides[get_original_value] = get_override_value

    try:
        client = TestClient(app)
        response = client.get("/test-override")

        assert response.status_code == 200
        assert response.json() == {"value": "override"}
    finally:
        app.dependency_overrides.clear()

def get_override_inner():
    return "original-inner"


def get_override_outer(
    value: str = Depends(get_override_inner),
):
    return f"outer:{value}"


def replace_override_inner():
    return "replaced-inner"


@app.get("/test-nested-override")
def nested_override_endpoint(
    value: str = Depends(get_override_outer),
):
    return {"value": value}


def test_nested_dependency_override():
    app.dependency_overrides[get_override_inner] = replace_override_inner

    try:
        client = TestClient(app)
        response = client.get("/test-nested-override")

        assert response.status_code == 200
        assert response.json() == {
            "value": "outer:replaced-inner"
        }
    finally:
        app.dependency_overrides.clear()

async def get_original_async():
    return "original-async"


async def get_replacement_async():
    return "replacement-async"


@app.get("/test-async-override")
async def async_override_endpoint(
    value: str = Depends(get_original_async),
):
    return {"value": value}


def test_async_dependency_override():
    app.dependency_overrides[get_original_async] = get_replacement_async

    try:
        client = TestClient(app)
        response = client.get("/test-async-override")

        assert response.status_code == 200
        assert response.json() == {
            "value": "replacement-async"
        }
    finally:
        app.dependency_overrides.clear()

async def get_async_original_for_sync_override():
    return "async-original"


def get_sync_replacement():
    return "sync-replacement"


@app.get("/test-async-to-sync-override")
async def async_to_sync_override_endpoint(
    value: str = Depends(get_async_original_for_sync_override),
):
    return {"value": value}


def test_async_dependency_overridden_by_sync_dependency():
    app.dependency_overrides[
        get_async_original_for_sync_override
    ] = get_sync_replacement

    try:
        client = TestClient(app)
        response = client.get("/test-async-to-sync-override")

        assert response.status_code == 200
        assert response.json() == {
            "value": "sync-replacement"
        }
    finally:
        app.dependency_overrides.clear()

def get_sync_original_for_async_override():
    return "sync-original"


async def get_async_replacement():
    return "async-replacement"


@app.get("/test-sync-to-async-override")
def sync_to_async_override_endpoint(
    value: str = Depends(get_sync_original_for_async_override),
):
    return {"value": value}


def test_sync_dependency_overridden_by_async_dependency():
    app.dependency_overrides[
        get_sync_original_for_async_override
    ] = get_async_replacement

    try:
        client = TestClient(app)
        response = client.get("/test-sync-to-async-override")

        assert response.status_code == 200
        assert response.json() == {
            "value": "async-replacement"
        }
    finally:
        app.dependency_overrides.clear()

yield_events = []


def get_yield_value():
    yield_events.append("setup")

    try:
        yield "yield-value"
    finally:
        yield_events.append("cleanup")


@app.get("/test-yield")
def yield_endpoint(
    value: str = Depends(get_yield_value),
):
    yield_events.append("endpoint")
    return {"value": value}


def test_yield_dependency():
    yield_events.clear()

    client = TestClient(app)
    response = client.get("/test-yield")

    assert response.status_code == 200
    assert response.json() == {"value": "yield-value"}

    assert yield_events == [
        "setup",
        "endpoint",
        "cleanup",
    ]

async_yield_events = []


async def get_async_yield_value():
    async_yield_events.append("setup")

    try:
        yield "async-yield-value"
    finally:
        async_yield_events.append("cleanup")


@app.get("/test-async-yield")
async def async_yield_endpoint(
    value: str = Depends(get_async_yield_value),
):
    async_yield_events.append("endpoint")
    return {"value": value}


def test_async_yield_dependency():
    async_yield_events.clear()

    client = TestClient(app)
    response = client.get("/test-async-yield")

    assert response.status_code == 200
    assert response.json() == {"value": "async-yield-value"}

    assert async_yield_events == [
        "setup",
        "endpoint",
        "cleanup",
    ]

nested_yield_events = []


def get_nested_yield_inner():
    nested_yield_events.append("inner-setup")

    try:
        yield "inner-value"
    finally:
        nested_yield_events.append("inner-cleanup")


def get_nested_yield_outer(
    value: str = Depends(get_nested_yield_inner),
):
    nested_yield_events.append("outer")
    return f"outer:{value}"


@app.get("/test-nested-yield")
def nested_yield_endpoint(
    value: str = Depends(get_nested_yield_outer),
):
    nested_yield_events.append("endpoint")
    return {"value": value}


def test_nested_yield_dependency():
    nested_yield_events.clear()

    client = TestClient(app)
    response = client.get("/test-nested-yield")

    assert response.status_code == 200
    assert response.json() == {
        "value": "outer:inner-value"
    }

    assert nested_yield_events == [
        "inner-setup",
        "outer",
        "endpoint",
        "inner-cleanup",
    ]

override_yield_events = []


def get_original_yield():
    override_yield_events.append("original-setup")

    try:
        yield "original"
    finally:
        override_yield_events.append("original-cleanup")


def get_replacement_yield():
    override_yield_events.append("replacement-setup")

    try:
        yield "replacement"
    finally:
        override_yield_events.append("replacement-cleanup")


@app.get("/test-yield-override")
def yield_override_endpoint(
    value: str = Depends(get_original_yield),
):
    override_yield_events.append("endpoint")
    return {"value": value}


def test_yield_dependency_override():
    override_yield_events.clear()
    app.dependency_overrides[get_original_yield] = get_replacement_yield

    try:
        client = TestClient(app)
        response = client.get("/test-yield-override")

        assert response.status_code == 200
        assert response.json() == {"value": "replacement"}

        assert override_yield_events == [
            "replacement-setup",
            "endpoint",
            "replacement-cleanup",
        ]
    finally:
        app.dependency_overrides.clear()

yield_cache_events = []
yield_cache_counter = 0


def get_yield_counter():
    global yield_cache_counter

    yield_cache_counter += 1
    value = yield_cache_counter
    yield_cache_events.append(f"setup:{value}")

    try:
        yield value
    finally:
        yield_cache_events.append(f"cleanup:{value}")


@app.get("/test-yield-no-cache")
def yield_no_cache_endpoint(
    first: int = Depends(get_yield_counter),
    second: int = Depends(get_yield_counter, use_cache=False),
):
    yield_cache_events.append("endpoint")
    return {
        "first": first,
        "second": second,
    }


def test_yield_dependency_without_cache():
    global yield_cache_counter

    yield_cache_counter = 0
    yield_cache_events.clear()

    client = TestClient(app)
    response = client.get("/test-yield-no-cache")

    assert response.status_code == 200
    assert response.json() == {
        "first": 1,
        "second": 2,
    }

    assert yield_cache_events == [
        "setup:1",
        "setup:2",
        "endpoint",
        "cleanup:2",
        "cleanup:1",
    ]

nested_yield_cache_events = []
nested_yield_cache_counter = 0


def get_nested_yield_counter():
    global nested_yield_cache_counter

    nested_yield_cache_counter += 1
    value = nested_yield_cache_counter
    nested_yield_cache_events.append(f"setup:{value}")

    try:
        yield value
    finally:
        nested_yield_cache_events.append(f"cleanup:{value}")


def get_cached_yield_outer(
    value: int = Depends(get_nested_yield_counter),
):
    return value


def get_uncached_yield_outer(
    value: int = Depends(get_nested_yield_counter, use_cache=False),
):
    return value


@app.get("/test-nested-yield-no-cache")
def nested_yield_no_cache_endpoint(
    cached: int = Depends(get_cached_yield_outer),
    uncached: int = Depends(get_uncached_yield_outer),
):
    nested_yield_cache_events.append("endpoint")

    return {
        "cached": cached,
        "uncached": uncached,
    }


def test_nested_yield_dependency_without_cache():
    global nested_yield_cache_counter

    nested_yield_cache_counter = 0
    nested_yield_cache_events.clear()

    client = TestClient(app)
    response = client.get("/test-nested-yield-no-cache")

    assert response.status_code == 200
    assert response.json() == {
        "cached": 1,
        "uncached": 2,
    }

    assert nested_yield_cache_events == [
        "setup:1",
        "setup:2",
        "endpoint",
        "cleanup:2",
        "cleanup:1",
    ]

def get_annotated_value():
    return "annotated-value"


@app.get("/test-annotated")
def annotated_endpoint(
    value: Annotated[str, Depends(get_annotated_value)],
):
    return {"value": value}


def test_annotated_dependency():
    client = TestClient(app)

    response = client.get("/test-annotated")

    assert response.status_code == 200
    assert response.json() == {
        "value": "annotated-value"
    }

def get_annotated_inner():
    return "annotated-inner"


def get_annotated_outer(
    value: Annotated[str, Depends(get_annotated_inner)],
):
    return f"outer:{value}"


@app.get("/test-annotated-nested")
def annotated_nested_endpoint(
    value: Annotated[str, Depends(get_annotated_outer)],
):
    return {"value": value}


def test_annotated_nested_dependency():
    client = TestClient(app)

    response = client.get("/test-annotated-nested")

    assert response.status_code == 200
    assert response.json() == {
        "value": "outer:annotated-inner"
    }

annotated_cache_count = 0


def get_annotated_counter():
    global annotated_cache_count
    annotated_cache_count += 1
    return annotated_cache_count


@app.get("/test-annotated-cache")
def annotated_cache_endpoint(
    first: Annotated[int, Depends(get_annotated_counter)],
    second: Annotated[int, Depends(get_annotated_counter)],
):
    return {
        "first": first,
        "second": second,
    }


def test_annotated_dependency_cache():
    global annotated_cache_count
    annotated_cache_count = 0

    client = TestClient(app)
    response = client.get("/test-annotated-cache")

    assert response.status_code == 200
    assert response.json() == {
        "first": 1,
        "second": 1,
    }
    assert annotated_cache_count == 1

annotated_no_cache_count = 0


def get_annotated_no_cache_counter():
    global annotated_no_cache_count
    annotated_no_cache_count += 1
    return annotated_no_cache_count


@app.get("/test-annotated-no-cache")
def annotated_no_cache_endpoint(
    first: Annotated[int, Depends(get_annotated_no_cache_counter)],
    second: Annotated[
        int,
        Depends(get_annotated_no_cache_counter, use_cache=False),
    ],
):
    return {
        "first": first,
        "second": second,
    }


def test_annotated_dependency_without_cache():
    global annotated_no_cache_count
    annotated_no_cache_count = 0

    client = TestClient(app)
    response = client.get("/test-annotated-no-cache")

    assert response.status_code == 200
    assert response.json() == {
        "first": 1,
        "second": 2,
    }
    assert annotated_no_cache_count == 2

def get_annotated_original():
    return "annotated-original"


def get_annotated_replacement():
    return "annotated-replacement"


@app.get("/test-annotated-override")
def annotated_override_endpoint(
    value: Annotated[str, Depends(get_annotated_original)],
):
    return {"value": value}


def test_annotated_dependency_override():
    app.dependency_overrides[
        get_annotated_original
    ] = get_annotated_replacement

    try:
        client = TestClient(app)
        response = client.get("/test-annotated-override")

        assert response.status_code == 200
        assert response.json() == {
            "value": "annotated-replacement"
        }
    finally:
        app.dependency_overrides.clear()

def get_annotated_override_inner():
    return "original-inner"


def get_annotated_override_outer(
    value: Annotated[str, Depends(get_annotated_override_inner)],
):
    return f"outer:{value}"


def replace_annotated_override_inner():
    return "replacement-inner"


@app.get("/test-annotated-nested-override")
def annotated_nested_override_endpoint(
    value: Annotated[str, Depends(get_annotated_override_outer)],
):
    return {"value": value}


def test_annotated_nested_dependency_override():
    app.dependency_overrides[
        get_annotated_override_inner
    ] = replace_annotated_override_inner

    try:
        client = TestClient(app)
        response = client.get("/test-annotated-nested-override")

        assert response.status_code == 200
        assert response.json() == {
            "value": "outer:replacement-inner"
        }
    finally:
        app.dependency_overrides.clear()

def get_failing_dependency():
    raise HTTPException(
        status_code=418,
        detail="dependency-failed",
    )


@app.get("/test-dependency-exception")
def dependency_exception_endpoint(
    value: str = Depends(get_failing_dependency),
):
    return {"value": value}


def test_dependency_exception():
    client = TestClient(app)

    response = client.get("/test-dependency-exception")

    assert response.status_code == 418
    assert response.json() == {
        "detail": "dependency-failed"
    }

yield_exception_events = []


def get_resource_before_failure():
    yield_exception_events.append("setup")

    try:
        yield "resource"
    finally:
        yield_exception_events.append("cleanup")


def get_failing_outer_dependency(
    resource: str = Depends(get_resource_before_failure),
):
    yield_exception_events.append("outer")
    raise HTTPException(
        status_code=409,
        detail="outer-failed",
    )


@app.get("/test-yield-dependency-exception")
def yield_dependency_exception_endpoint(
    value: str = Depends(get_failing_outer_dependency),
):
    yield_exception_events.append("endpoint")
    return {"value": value}


def test_yield_cleanup_when_nested_dependency_fails():
    yield_exception_events.clear()

    client = TestClient(app)
    response = client.get("/test-yield-dependency-exception")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "outer-failed"
    }

    assert yield_exception_events == [
        "setup",
        "outer",
        "cleanup",
    ]

async_yield_exception_events = []


async def get_async_resource_before_failure():
    async_yield_exception_events.append("setup")

    try:
        yield "async-resource"
    finally:
        async_yield_exception_events.append("cleanup")


async def get_async_failing_outer_dependency(
    resource: str = Depends(get_async_resource_before_failure),
):
    async_yield_exception_events.append("outer")

    raise HTTPException(
        status_code=409,
        detail="async-outer-failed",
    )


@app.get("/test-async-yield-dependency-exception")
async def async_yield_dependency_exception_endpoint(
    value: str = Depends(get_async_failing_outer_dependency),
):
    async_yield_exception_events.append("endpoint")
    return {"value": value}


def test_async_yield_cleanup_when_nested_dependency_fails():
    async_yield_exception_events.clear()

    client = TestClient(app)
    response = client.get("/test-async-yield-dependency-exception")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "async-outer-failed"
    }

    assert async_yield_exception_events == [
        "setup",
        "outer",
        "cleanup",
    ]

multiple_yield_exception_events = []


def get_first_resource():
    multiple_yield_exception_events.append("first-setup")

    try:
        yield "first"
    finally:
        multiple_yield_exception_events.append("first-cleanup")


def get_second_resource():
    multiple_yield_exception_events.append("second-setup")

    try:
        yield "second"
    finally:
        multiple_yield_exception_events.append("second-cleanup")


def get_failing_dependency_with_resources(
    first: str = Depends(get_first_resource),
    second: str = Depends(get_second_resource),
):
    multiple_yield_exception_events.append("failure")

    raise HTTPException(
        status_code=409,
        detail="failed",
    )


@app.get("/test-multiple-yield-exception")
def multiple_yield_exception_endpoint(
    value: str = Depends(get_failing_dependency_with_resources),
):
    multiple_yield_exception_events.append("endpoint")
    return {"value": value}


def test_multiple_yield_cleanup_order_on_exception():
    multiple_yield_exception_events.clear()

    client = TestClient(app)
    response = client.get("/test-multiple-yield-exception")

    assert response.status_code == 409

    assert multiple_yield_exception_events == [
        "first-setup",
        "second-setup",
        "failure",
        "second-cleanup",
        "first-cleanup",
    ]

partial_setup_events = []


def get_successful_resource():
    partial_setup_events.append("first-setup")

    try:
        yield "first"
    finally:
        partial_setup_events.append("first-cleanup")


def get_resource_that_fails_before_yield():
    partial_setup_events.append("second-setup")

    raise HTTPException(
        status_code=503,
        detail="setup-failed",
    )

    yield "never"


@app.get("/test-partial-yield-setup-failure")
def partial_yield_setup_failure_endpoint(
    first: str = Depends(get_successful_resource),
    second: str = Depends(get_resource_that_fails_before_yield),
):
    partial_setup_events.append("endpoint")
    return {
        "first": first,
        "second": second,
    }


def test_cleanup_when_later_yield_dependency_fails_before_yield():
    partial_setup_events.clear()

    client = TestClient(app)
    response = client.get("/test-partial-yield-setup-failure")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "setup-failed"
    }

    assert partial_setup_events == [
        "first-setup",
        "second-setup",
        "first-cleanup",
    ]

async_partial_setup_events = []


async def get_successful_async_resource():
    async_partial_setup_events.append("first-setup")

    try:
        yield "first"
    finally:
        async_partial_setup_events.append("first-cleanup")


async def get_async_resource_that_fails_before_yield():
    async_partial_setup_events.append("second-setup")

    raise HTTPException(
        status_code=503,
        detail="async-setup-failed",
    )

    yield "never"


@app.get("/test-async-partial-yield-setup-failure")
async def async_partial_yield_setup_failure_endpoint(
    first: str = Depends(get_successful_async_resource),
    second: str = Depends(get_async_resource_that_fails_before_yield),
):
    async_partial_setup_events.append("endpoint")
    return {
        "first": first,
        "second": second,
    }


def test_async_cleanup_when_later_yield_dependency_fails_before_yield():
    async_partial_setup_events.clear()

    client = TestClient(app)
    response = client.get("/test-async-partial-yield-setup-failure")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "async-setup-failed"
    }

    assert async_partial_setup_events == [
        "first-setup",
        "second-setup",
        "first-cleanup",
    ]

mixed_yield_events = []


def get_sync_mixed_resource():
    mixed_yield_events.append("sync-setup")

    try:
        yield "sync"
    finally:
        mixed_yield_events.append("sync-cleanup")


async def get_async_mixed_resource():
    mixed_yield_events.append("async-setup")

    try:
        yield "async"
    finally:
        mixed_yield_events.append("async-cleanup")


async def get_mixed_failing_dependency(
    sync_value: str = Depends(get_sync_mixed_resource),
    async_value: str = Depends(get_async_mixed_resource),
):
    mixed_yield_events.append("failure")

    raise HTTPException(
        status_code=409,
        detail="mixed-failed",
    )


@app.get("/test-mixed-yield-failure")
async def mixed_yield_failure_endpoint(
    value: str = Depends(get_mixed_failing_dependency),
):
    mixed_yield_events.append("endpoint")
    return {"value": value}


def test_mixed_sync_async_yield_cleanup_order():
    mixed_yield_events.clear()

    client = TestClient(app)
    response = client.get("/test-mixed-yield-failure")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "mixed-failed"
    }

    assert mixed_yield_events == [
        "sync-setup",
        "async-setup",
        "failure",
        "async-cleanup",
        "sync-cleanup",
    ]

override_async_yield_events = []


def get_sync_yield_original():
    override_async_yield_events.append("original-setup")

    try:
        yield "original"
    finally:
        override_async_yield_events.append("original-cleanup")


async def get_async_yield_replacement():
    override_async_yield_events.append("replacement-setup")

    try:
        yield "replacement"
    finally:
        override_async_yield_events.append("replacement-cleanup")


@app.get("/test-sync-yield-to-async-yield-override")
async def sync_yield_to_async_yield_override_endpoint(
    value: str = Depends(get_sync_yield_original),
):
    override_async_yield_events.append("endpoint")
    return {"value": value}


def test_sync_yield_dependency_overridden_by_async_yield():
    override_async_yield_events.clear()
    app.dependency_overrides[
        get_sync_yield_original
    ] = get_async_yield_replacement

    try:
        client = TestClient(app)
        response = client.get("/test-sync-yield-to-async-yield-override")

        assert response.status_code == 200
        assert response.json() == {
            "value": "replacement"
        }

        assert override_async_yield_events == [
            "replacement-setup",
            "endpoint",
            "replacement-cleanup",
        ]
    finally:
        app.dependency_overrides.clear()

override_sync_yield_events = []


async def get_async_yield_original():
    override_sync_yield_events.append("original-setup")

    try:
        yield "original"
    finally:
        override_sync_yield_events.append("original-cleanup")


def get_sync_yield_replacement():
    override_sync_yield_events.append("replacement-setup")

    try:
        yield "replacement"
    finally:
        override_sync_yield_events.append("replacement-cleanup")


@app.get("/test-async-yield-to-sync-yield-override")
async def async_yield_to_sync_yield_override_endpoint(
    value: str = Depends(get_async_yield_original),
):
    override_sync_yield_events.append("endpoint")
    return {"value": value}


def test_async_yield_dependency_overridden_by_sync_yield():
    override_sync_yield_events.clear()
    app.dependency_overrides[
        get_async_yield_original
    ] = get_sync_yield_replacement

    try:
        client = TestClient(app)
        response = client.get("/test-async-yield-to-sync-yield-override")

        assert response.status_code == 200
        assert response.json() == {
            "value": "replacement"
        }

        assert override_sync_yield_events == [
            "replacement-setup",
            "endpoint",
            "replacement-cleanup",
        ]
    finally:
        app.dependency_overrides.clear()

override_cache_count = 0


def get_override_cache_original():
    return -1


def get_override_cache_replacement():
    global override_cache_count
    override_cache_count += 1
    return override_cache_count


@app.get("/test-override-no-cache")
def override_no_cache_endpoint(
    first: int = Depends(get_override_cache_original),
    second: int = Depends(get_override_cache_original, use_cache=False),
):
    return {
        "first": first,
        "second": second,
    }


def test_dependency_override_with_no_cache():
    global override_cache_count
    override_cache_count = 0

    app.dependency_overrides[
        get_override_cache_original
    ] = get_override_cache_replacement

    try:
        client = TestClient(app)
        response = client.get("/test-override-no-cache")

        assert response.status_code == 200
        assert response.json() == {
            "first": 1,
            "second": 2,
        }
        assert override_cache_count == 2
    finally:
        app.dependency_overrides.clear()

nested_override_cache_count = 0


def get_nested_override_cache_original():
    return -1


def get_nested_override_cache_replacement():
    global nested_override_cache_count
    nested_override_cache_count += 1
    return nested_override_cache_count


def get_nested_override_cached(
    value: int = Depends(get_nested_override_cache_original),
):
    return value


def get_nested_override_uncached(
    value: int = Depends(
        get_nested_override_cache_original,
        use_cache=False,
    ),
):
    return value


@app.get("/test-nested-override-no-cache")
def nested_override_no_cache_endpoint(
    cached: int = Depends(get_nested_override_cached),
    uncached: int = Depends(get_nested_override_uncached),
):
    return {
        "cached": cached,
        "uncached": uncached,
    }


def test_nested_override_with_no_cache():
    global nested_override_cache_count
    nested_override_cache_count = 0

    app.dependency_overrides[
        get_nested_override_cache_original
    ] = get_nested_override_cache_replacement

    try:
        client = TestClient(app)
        response = client.get("/test-nested-override-no-cache")

        assert response.status_code == 200
        assert response.json() == {
            "cached": 1,
            "uncached": 2,
        }
        assert nested_override_cache_count == 2
    finally:
        app.dependency_overrides.clear()


yield_override_cache_events = []
yield_override_cache_count = 0


def get_yield_override_cache_original():
    yield -1


def get_yield_override_cache_replacement():
    global yield_override_cache_count

    yield_override_cache_count += 1
    value = yield_override_cache_count
    yield_override_cache_events.append(f"setup:{value}")

    try:
        yield value
    finally:
        yield_override_cache_events.append(f"cleanup:{value}")


@app.get("/test-yield-override-no-cache")
def yield_override_no_cache_endpoint(
    first: int = Depends(get_yield_override_cache_original),
    second: int = Depends(
        get_yield_override_cache_original,
        use_cache=False,
    ),
):
    yield_override_cache_events.append("endpoint")

    return {
        "first": first,
        "second": second,
    }


def test_yield_override_with_no_cache():
    global yield_override_cache_count

    yield_override_cache_count = 0
    yield_override_cache_events.clear()

    app.dependency_overrides[
        get_yield_override_cache_original
    ] = get_yield_override_cache_replacement

    try:
        client = TestClient(app)
        response = client.get("/test-yield-override-no-cache")

        assert response.status_code == 200
        assert response.json() == {
            "first": 1,
            "second": 2,
        }

        assert yield_override_cache_events == [
            "setup:1",
            "setup:2",
            "endpoint",
            "cleanup:2",
            "cleanup:1",
        ]
    finally:
        app.dependency_overrides.clear()

annotated_yield_cache_events = []
annotated_yield_cache_count = 0


def get_annotated_yield_counter():
    global annotated_yield_cache_count

    annotated_yield_cache_count += 1
    value = annotated_yield_cache_count
    annotated_yield_cache_events.append(f"setup:{value}")

    try:
        yield value
    finally:
        annotated_yield_cache_events.append(f"cleanup:{value}")


@app.get("/test-annotated-yield-no-cache")
def annotated_yield_no_cache_endpoint(
    first: Annotated[
        int,
        Depends(get_annotated_yield_counter),
    ],
    second: Annotated[
        int,
        Depends(
            get_annotated_yield_counter,
            use_cache=False,
        ),
    ],
):
    annotated_yield_cache_events.append("endpoint")

    return {
        "first": first,
        "second": second,
    }


def test_annotated_yield_without_cache():
    global annotated_yield_cache_count

    annotated_yield_cache_count = 0
    annotated_yield_cache_events.clear()

    client = TestClient(app)
    response = client.get("/test-annotated-yield-no-cache")

    assert response.status_code == 200
    assert response.json() == {
        "first": 1,
        "second": 2,
    }

    assert annotated_yield_cache_events == [
        "setup:1",
        "setup:2",
        "endpoint",
        "cleanup:2",
        "cleanup:1",
    ]

def get_query_value(value: int):
    return value


@app.get("/test-query-dependency")
def query_dependency_endpoint(
    value: int = Depends(get_query_value),
):
    return {"value": value}


def test_dependency_with_query_parameter():
    client = TestClient(app)

    response = client.get(
        "/test-query-dependency",
        params={"value": "42"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "value": 42,
    }

def get_validated_inner(value: int):
    return value


def get_validated_outer(
    value: int = Depends(get_validated_inner),
):
    return value * 2


@app.get("/test-nested-query-validation")
def nested_query_validation_endpoint(
    result: int = Depends(get_validated_outer),
):
    return {"result": result}


def test_nested_dependency_query_validation():
    client = TestClient(app)

    response = client.get(
        "/test-nested-query-validation",
        params={"value": "21"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "result": 42,
    }

validation_events = []


def get_invalid_validation_inner(value: int):
    validation_events.append("inner")
    return value


def get_invalid_validation_outer(
    value: int = Depends(get_invalid_validation_inner),
):
    validation_events.append("outer")
    return value


@app.get("/test-invalid-nested-query")
def invalid_nested_query_endpoint(
    value: int = Depends(get_invalid_validation_outer),
):
    validation_events.append("endpoint")
    return {"value": value}


def test_invalid_query_stops_nested_dependency_execution():
    validation_events.clear()

    client = TestClient(app)

    response = client.get(
        "/test-invalid-nested-query",
        params={"value": "not-an-integer"},
    )

    assert response.status_code == 422

    assert validation_events == []

validation_cleanup_events = []


def get_validation_resource():
    validation_cleanup_events.append("setup")

    try:
        yield "resource"
    finally:
        validation_cleanup_events.append("cleanup")


def get_validated_number(value: int):
    validation_cleanup_events.append("validated")
    return value


@app.get("/test-validation-yield-cleanup")
def validation_yield_cleanup_endpoint(
    resource: str = Depends(get_validation_resource),
    number: int = Depends(get_validated_number),
):
    validation_cleanup_events.append("endpoint")

    return {
        "resource": resource,
        "number": number,
    }


def test_yield_cleanup_when_sibling_validation_fails():
    validation_cleanup_events.clear()

    client = TestClient(app)

    response = client.get(
        "/test-validation-yield-cleanup",
        params={"value": "not-an-integer"},
    )

    assert response.status_code == 422

    assert validation_cleanup_events == [
        "setup",
        "cleanup",
    ]

reverse_validation_cleanup_events = []


def get_reverse_validated_number(value: int):
    reverse_validation_cleanup_events.append("validated")
    return value


def get_reverse_validation_resource():
    reverse_validation_cleanup_events.append("setup")

    try:
        yield "resource"
    finally:
        reverse_validation_cleanup_events.append("cleanup")


@app.get("/test-reverse-validation-yield")
def reverse_validation_yield_endpoint(
    number: int = Depends(get_reverse_validated_number),
    resource: str = Depends(get_reverse_validation_resource),
):
    reverse_validation_cleanup_events.append("endpoint")

    return {
        "number": number,
        "resource": resource,
    }


def test_resource_not_acquired_after_sibling_validation_failure():
    reverse_validation_cleanup_events.clear()

    client = TestClient(app)

    response = client.get(
        "/test-reverse-validation-yield",
        params={"value": "not-an-integer"},
    )

    assert response.status_code == 422

    assert reverse_validation_cleanup_events == [
        "setup",
        "cleanup",
    ]

multiple_validation_events = []


def get_first_invalid_value(first: int):
    multiple_validation_events.append("first")
    return first


def get_second_invalid_value(second: int):
    multiple_validation_events.append("second")
    return second


@app.get("/test-multiple-validation-errors")
def multiple_validation_errors_endpoint(
    first: int = Depends(get_first_invalid_value),
    second: int = Depends(get_second_invalid_value),
):
    multiple_validation_events.append("endpoint")
    return {
        "first": first,
        "second": second,
    }


def test_multiple_dependency_validation_errors_are_collected():
    multiple_validation_events.clear()

    client = TestClient(app)

    response = client.get(
        "/test-multiple-validation-errors",
        params={
            "first": "invalid-first",
            "second": "invalid-second",
        },
    )

    assert response.status_code == 422
    assert multiple_validation_events == []

    errors = response.json()["detail"]

    assert len(errors) == 2
    assert errors[0]["loc"] == ["query", "first"]
    assert errors[1]["loc"] == ["query", "second"]

invalid_cached_events = []


def get_invalid_cached_value(value: int):
    invalid_cached_events.append("executed")
    return value


@app.get("/test-invalid-cached-dependency")
def invalid_cached_dependency_endpoint(
    first: int = Depends(get_invalid_cached_value),
    second: int = Depends(get_invalid_cached_value),
):
    return {
        "first": first,
        "second": second,
    }


def test_invalid_cached_dependency_errors():
    invalid_cached_events.clear()

    client = TestClient(app)

    response = client.get(
        "/test-invalid-cached-dependency",
        params={"value": "invalid"},
    )

    assert response.status_code == 422
    assert invalid_cached_events == []

    errors = response.json()["detail"]

    assert len(errors) == 2

invalid_mixed_cache_events = []


def get_invalid_mixed_cache_value(value: int):
    invalid_mixed_cache_events.append("executed")
    return value


@app.get("/test-invalid-mixed-cache")
def invalid_mixed_cache_endpoint(
    first: int = Depends(get_invalid_mixed_cache_value),
    second: int = Depends(
        get_invalid_mixed_cache_value,
        use_cache=False,
    ),
):
    return {
        "first": first,
        "second": second,
    }


def test_invalid_dependency_with_mixed_cache():
    invalid_mixed_cache_events.clear()

    client = TestClient(app)

    response = client.get(
        "/test-invalid-mixed-cache",
        params={"value": "invalid"},
    )

    assert response.status_code == 422
    assert invalid_mixed_cache_events == []

    errors = response.json()["detail"]

    assert len(errors) == 2

shared_graph_events = []


def get_shared_leaf(value: int):
    shared_graph_events.append(f"leaf:{value}")
    return value


def get_shared_outer(
    value: int = Depends(get_shared_leaf),
):
    shared_graph_events.append(f"outer:{value}")
    return value


@app.get("/test-shared-graph-cache")
def shared_graph_cache_endpoint(
    direct: int = Depends(get_shared_leaf),
    nested: int = Depends(get_shared_outer),
):
    return {
        "direct": direct,
        "nested": nested,
    }


def test_shared_dependency_across_graph_paths():
    shared_graph_events.clear()

    client = TestClient(app)

    response = client.get(
        "/test-shared-graph-cache",
        params={"value": "42"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "direct": 42,
        "nested": 42,
    }

    assert shared_graph_events == [
        "leaf:42",
        "outer:42",
    ]