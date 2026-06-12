"""The minimum event bus: the only deliberate breach in the firewall.

Direction of flow is enforced structurally, not by convention:

* Publishing requires a ``TaperOutlet``, a capability object the bus
  issues exactly once. The taper engine holds it; nothing else can.
* Subscribers receive events through plain callables and are handed no
  reference to the bus's publish path at all.

So events flow taper -> progression, never back. The progression engine
cannot influence reel odds because it has no channel that reaches the
coral side; it can only listen.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Callable, Type, TypeVar

from recovering_player.events import TaperEvent

E = TypeVar("E", bound=TaperEvent)
Handler = Callable[[TaperEvent], None]


class BreachViolation(RuntimeError):
    """Raised on any attempt to widen the firewall breach."""


class TaperOutlet:
    """Publish-only capability. The single permitted way into the bus."""

    def __init__(self, deliver: Callable[[TaperEvent], None]) -> None:
        self._deliver = deliver

    def publish(self, event: TaperEvent) -> None:
        if not isinstance(event, TaperEvent):
            raise BreachViolation(
                "only TaperEvent records may cross the firewall"
            )
        self._deliver(event)


class MinimumEventBus:
    """One inlet, many listeners, an append-only log. Nothing more.

    The bus is deliberately minimal so the breach stays auditable: the
    full causal history of the teal side is ``bus.log``, and every entry
    in it originated from the one outlet.
    """

    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)
        self._log: list[TaperEvent] = []
        self._outlet_issued = False

    def issue_outlet(self) -> TaperOutlet:
        """Create the single publish capability. Callable exactly once."""
        if self._outlet_issued:
            raise BreachViolation(
                "the firewall permits exactly one breach; "
                "an outlet has already been issued"
            )
        self._outlet_issued = True
        return TaperOutlet(self._deliver)

    def subscribe(self, event_type: Type[E], handler: Callable[[E], None]) -> None:
        self._handlers[event_type].append(handler)  # type: ignore[arg-type]

    def _deliver(self, event: TaperEvent) -> None:
        self._log.append(event)
        for event_type, handlers in self._handlers.items():
            if isinstance(event, event_type):
                for handler in list(handlers):
                    handler(event)

    @property
    def log(self) -> tuple[TaperEvent, ...]:
        return tuple(self._log)
