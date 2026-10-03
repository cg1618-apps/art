"""The rows a resource list becomes. Shared by every `<table>_resource`."""


def build(model, payload_resources) -> list:
    """One `model` row per resource sent, positioned by its place in the
    list. Assigned to the owner's relationship, they replace the old rows
    whole: those are orphans and go in the same flush."""
    return [
        model(position=position, name=resource.name, url=resource.url)
        for position, resource in enumerate(payload_resources)
    ]
