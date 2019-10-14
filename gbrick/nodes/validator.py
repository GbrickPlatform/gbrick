
import asyncio
import datetime

from gbrick.nodes.base import BaseNode
from gbrick.chains.base import BaseChain
from event.base import BaseEvent
from gbrick.types.base import BaseBlock, BaseVote
from event.event_context import CandidateContext, VoteContext
from utils.logger import getLogger
from utils.util import chain_information

from utils.exceptions import (
    RoundError, ValidationError, FinalizeError
)

from gbrick.nodes.llfc_helpers import (
    make_candidate, select_candidate,
    make_vote, aggregate_vote,
    aggregate_confirm, make_finalize_from_confirm,
    make_confirm_from_vote
)


class Validator(BaseNode):
    _logger = None

    def __init__(self, chain: BaseChain, event: BaseEvent, syncer):
        """
        :param Chain chain: Chain class
        :param Event event: Event class
        :param Syncer syncer: Syncer class
        """
        self._chain = chain
        self._event = event
        self._syncer = syncer

    @property
    def chain(self) -> BaseChain:
        return self._chain

    @property
    def event(self) -> BaseEvent:
        return self._event

    @property
    def logger(self):
        if self._logger is None:
            self._logger = getLogger('node')
        return self._logger

    # ---  event control  --- #

    async def event_transaction(self):
        return await self.event.transaction_exists()

    async def event_candidate(self):
        return await self.event.candidate_exists()

    async def event_vote(self):
        return await self.event.vote_exists()

    async def event_confirm(self):
        return await self.event.confirm_exists()

    async def event_finalize(self):
        return await self.event.finalize_exists()

    async def send(self, obj, exchange):
        await self.event.send(obj, exchange)

    async def accumulated_processing(self):
        self.logger.info('accumulated block processing... start at {}'.format(self.chain.height))
        try:
            while True:
                permit_header = self.chain.get_header_from_height(self.chain.height)
                blk = self.get_finalize(permit_header)
                await self.finalize(blk)
                await self.event.clear(self.chain, blk)
        except IndexError:
            return

    def syncer_run(self):
        asyncio.ensure_future(self._syncer.load())

    async def prepare_node_synchronization(self):
        await self._syncer.run()

    # ---  consensus control  --- #

    def prepare_candidate_from_header(self, header) -> BaseBlock:
        return self.chain.prepare_candidate_from_header(header)

    def make_candidate(self, block: BaseBlock):
        return make_candidate(block, self.event, self.chain)

    def select_candidate(self, header) -> CandidateContext:
        return select_candidate(header, self.event, self.chain)

    def make_vote(self, context) -> BaseVote:
        return make_vote(context, self.chain)

    def aggregate_vote(self, header) -> VoteContext:
        return aggregate_vote(header, self.event,  self.chain, self.logger)

    def make_confirm_from_vote(self, height, vote_blk):
        return make_confirm_from_vote(height, vote_blk, self.chain)

    def aggregate_confirm(self, block) -> BaseBlock:
        return aggregate_confirm(block, self.event, self.chain, self.logger)

    async def make_finalize_from_confirm(self, block, context):
        return await make_finalize_from_confirm(block, context, self.chain)

    # ---  chain finalize  --- #

    async def finalize(self, blk):
        await self.chain.finalize(blk)

    def get_finalize(self, permit_header):
        return self.event.get_finalize_block(permit_header.num_height + 1)

    async def _run(self):
        self.syncer_run()
        self.event.prepare(self.chain)
        await self.progress()

    # --- in progress node  --- #

    async def progress(self):
        # consensus sequence
        await self.prepare_node_synchronization()
        sequence = True
        while True:
            if sequence:
                # current chain information
                chain_information(self.chain, self.chain.logger)
                sequence = False

            # validator-set setup for next consensus
            count, terms = self.chain.get_validator_count()
            self.event.set_info(count, terms)   # vote allow, length

            # when chain height at 1
            # get_header_from_height(height): header.num_height equal to chain.height + 1
            # always prepare candidate block is higher than chain height
            # prepare candidate block at default data set on chain

            # --- create cnadidate block --- #
            permit_header = self.chain.get_header_from_height(self.chain.height)
            prepare_candidate = self.prepare_candidate_from_header(permit_header)

            # waiting transaction event
            await self.event_transaction()
            # make candidate block on occur to event
            candidate_blk = self.make_candidate(prepare_candidate)

            if not candidate_blk:
                continue
            # --- create candidate block --- #

            # todo 8/14

            try:
                # select candidate after consensus process at this height
                final_blk = await self._progress(candidate_blk, permit_header)
            except FinalizeError:
                # not safe finality block
                self.logger.info("sync-start at "
                                 "{}, {}".format(self.chain.height, datetime.datetime.now()))
                await self._syncer.run()
                self.logger.debug("sync-end at "
                                  "{}, {}".format(self.chain.height, datetime.datetime.now()))
            except AttributeError:
                # block is many exist
                await self.accumulated_processing()
            else:
                self.chain.logger.info("execution-set: {}".format(len(final_blk.list_transactions)))
                # finality
                await self.finalize(final_blk)
                await self.event.clear(self.chain, final_blk)
                sequence = True

    async def _progress(self, candidate_blk, permit_header):
        while True:
            try:
                # pre-prepare (propose)
                await self.send(candidate_blk, 'candidate')
                await self.event_candidate()

                candidate_context = self.select_candidate(permit_header)
                # block, *_ = (BLOCK, )
                # block = BLOCK,  *_ = ()
                select_blk, *_ = candidate_context.data.values()
                self.logger.debug('select-blk: {}'.format(select_blk.pre_hash))

                # prepare (pre-vote)
                vote = self.make_vote(select_blk)
                self.logger.debug('make-vote : {}'.format(vote.hash_candidate_block))
                await self.send(vote, 'vote')
                await self.event_vote()

                # commit (confirm)
                vote_blk, vote_context = self.aggregate_vote(select_blk.header)
                confirm = self.make_confirm_from_vote(permit_header.num_height+1, vote_blk)
                await self.send(confirm, 'confirm')
                await self.event_confirm()
                # TODO: confirm data validation.
                confirm_blk = self.aggregate_confirm(confirm)
            except RoundError as err:
                self.logger.error("fall outside the normal way, "
                                  "reason: {}".format(str(err)))
                try:
                    flk = self.get_finalize(permit_header)
                except IndexError:
                    await self.event.reset(self.chain)
                    await asyncio.sleep(1)
                else:
                    if self.chain.height+1 != flk.height:
                        raise FinalizeError
                    else:
                        return flk
            except ValidationError as err:
                self.logger.error("validation error, "
                                  "reason: {}".format(str(err)))
            else:
                final_blk, flag = await self.make_finalize_from_confirm(confirm_blk, vote_context)
                if flag:
                    self.logger.info("make-finalize: {}".format(final_blk.height))
                    await self.send(final_blk, 'finalize')
                # TODO: finalize block 이 들어오지 않을 경우, 처리방안
                #  ex: 죽는 노드가 파이널 블록 생성자 일때..
                await self.event_finalize()
                return self.get_finalize(permit_header)



