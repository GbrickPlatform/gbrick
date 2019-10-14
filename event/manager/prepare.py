

from utils.config import EVENT_NAME
from event.manager.tx_manager import TransactionManager
from event.manager.candidate_manager import CandidateManager
from event.manager.vote_manager import VoteManager
from event.manager.finalize_manager import FinalizeManager
from event.manager.confirm_manager import ConfirmManager

# prepare event at the EventClass


def prepare_transaction_event(name) -> TransactionManager:
    return TransactionManager(name)


def prepare_candidate_event(name) -> CandidateManager:
    return CandidateManager(name)


def prepare_vote_event(name) -> VoteManager:
    return VoteManager(name)


def prepare_confirm_event(name) -> ConfirmManager:
    return ConfirmManager(name)


def prepare_finalize_event(name) -> FinalizeManager:
    return FinalizeManager(name)


def prepare_event():
    class EventContext:
        __slots__ = ('transaction',
                     'finalize',
                     'candidate',
                     'vote',
                     'confirm')

        def __init__(self):
            event_class = (
                prepare_transaction_event,
                prepare_finalize_event,
                prepare_candidate_event,
                prepare_vote_event,
                prepare_confirm_event
            )

            for name, make_event in zip(self.__slots__, event_class):
                setattr(self, name, make_event(EVENT_NAME(name)))

        def __iter__(self):
            for name in self.__slots__:
                yield name

    return EventContext()


