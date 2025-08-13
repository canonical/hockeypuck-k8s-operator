from ops import testing

from src.charm import HockeypuckK8SCharm


def test_base():
    """
    Integrate postgresql with hockeypuck and scale to 2 units and check if the
    charm is blocked.
    """
    ctx = testing.Context(HockeypuckK8SCharm)
    relation1 = testing.Relation("postgresql")
    state_in = testing.State(planned_units=2, relations=[relation1])
    state_out = ctx.run(ctx.on.start(), state_in)
    assert state_out.unit_status == testing.BlockedStatus(
        "Hockeypuck does not support multi-unit deployments"
    )
