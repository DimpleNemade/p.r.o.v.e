def versioned_endpoints(endpoints):
    """Publish the canonical v1 surface while legacy aliases remain available."""

    return [endpoint for endpoint in endpoints if endpoint[0].startswith("/api/v1/")]
