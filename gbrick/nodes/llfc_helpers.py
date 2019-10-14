
import time

from utils.exceptions import ValidationError, RoundError
from utils.trie.prepare import make_hash_root
from event.event_context import CandidateContext, VoteContext
from utils.crypto.hash import sha3_hex

from event.base import BaseEvent
from gbrick.validation import validate_has_transactions, validate_validator_set
from gbrick.chains.base import BaseChain
from gbrick.types.prepare import prepare_vote
from gbrick.types.base import (
    BaseHeader, BaseBlock, BaseVote
)


def filter_out_candidate(context: CandidateContext) -> None:
    # candidate block condition statement
    estimated_time_range(context)
    select_maximum(context)


def select_maximum(context: CandidateContext) -> None:

    # allowable max and old on select
    # select block that includes the largest number of transaction

    candidate = context.get_data_list()
    candidate.sort(key=lambda block: len(block.list_transactions),
                   reverse=True)

    max_number = len(candidate[0].list_transactions)

    for blk in context:
        if len(blk.list_transactions) < max_number:
            context.remove((blk.height, blk.creator))
            candidate.remove(blk)

    if not exists_stage(candidate):
        select_oldest(candidate, context)

    return


def select_oldest(candidate, context):
    # select block that includes the oldest of transaction
    candidate.sort(
        key=lambda block: get_old_transaction(block.list_transactions)
    )

    old_time = get_old_transaction(candidate[0].list_transactions)
    for blk in candidate:
        blk_old_tx = get_old_transaction(blk.list_transactions)
        if blk_old_tx > old_time:
            context.remove((blk.height, blk.creator))


def get_old_transaction(tx_list: list):
    old_tx = sorted(tx_list,
                    key=lambda tx: tx.timestamp)
    return old_tx[0].timestamp


def estimated_time_range(context: CandidateContext) -> None:
    """
    allowable range from fastest time block is 1.2s.
    >>> [1.0, 1.5, 2.0, 2.7]
    fastest time: 1.0
    consensus time range: 2.2s (1.0 + 1.2)
    result: 2.7s block is exclude this round
    >>> [1.0, 1.5, 2.0]
    """
    candidate = context.get_data_list()
    if len(candidate) < 1:
        raise ValidationError("candidate context block: {}".format(len(candidate)))

    block_times = context.time
    if len(block_times) < 1:
        raise ValidationError("candidate context time: {}".format(len(block_times)))

    block_times.sort()
    estimated = estimated_time_point(block_times)
    # (time, time range)

    for blk in candidate:
        if blk.header.timestamp >= estimated[0]:
            if blk.header.timestamp <= estimated[1]:
                continue
        context.remove((blk.height, blk.creator))


def estimated_time_point(times):
    distance = times[len(times)-1] - times[0]
    datum = times[0] + distance / 2
    estimated = (times[0], datum + 0.5)
    return estimated


def exists_stage(data):
    return len(data) == 1


def computation_hash_distance(header: BaseHeader,
                              context: CandidateContext) -> None:
    permit_hash = header.hash
    estimated_distance = []
    dist_point = 0
    # previous block from current block at distance computation

    for blk in context:
        compute_distance = 0

        for older, newer in zip(permit_hash, blk.pre_hash):
            compute_distance += older - newer
        if compute_distance < 0:
            compute_distance *= -1
        if dist_point < compute_distance:
            dist_point = compute_distance
        estimated_distance.append((blk.creator, compute_distance, blk.pre_hash))

    select = list(
        (creator, distance, candidate_hash)
        for creator, distance, candidate_hash
        in estimated_distance
        if distance == dist_point
    )

    if len(select) >= 1:
        # TODO: choose as validators-power,
        select.sort(key=lambda x: x[2])
        select_items = select.pop(0)
        estimated_distance.remove(select_items)
    else:
        raise RoundError('block is not selected')

    for creator, dist, candidate_hash in estimated_distance:
            context.remove((context.height, creator))


def aggregate_vote_from_context(header: BaseHeader,
                                context: VoteContext,
                                logger):
    for v in context:
        if v.num_block_height != header.num_height:
            raise ValidationError(
                "event context height: {} "
                "current vote height: {}".format(
                    context.height, v.num_block_height
                )
            )

    vt_data = []
    for vt in context:
        vt_data.append((vt.num_block_height, vt.hash_candidate_block))

    select_blocks = set(vt_data)

    diff_vote = select_blocks.difference(
        [(header.num_height, header.pre_hash)]
    )

    if len(diff_vote) == 0:
        # 선택한 블록과 다른 투표 모두 동일한 투표일 때.
        return header.pre_hash

    # 선택한 블록과 다른 투표일 때
    if len(diff_vote) >= 1:
        logger.debug("node-select: {}, "
                     "diff-select: {}".format(header.pre_hash[:8], diff_vote))

    aggregate = {}
    for h, agree_blk in diff_vote:
        aggregate[agree_blk] = 0
        # { 'candidate-hash-key': 0,  'candidate-hash-key': 0 }

    for vt in context:
        if header.pre_hash != vt.hash_candidate_block:
            aggregate[vt.hash_candidate_block] += 1

    # my select = 1    , 3
    # other select = 3 , 1
    for k, v in aggregate.items():
        f = 3
        # TODO: F computation
        #   1 <= f  pass
        #   1 > f  vote pow, penalty
        if v >= f:
            return k
        elif v <= f:
            return header.pre_hash
        else:
            raise RoundError(
                "aggregate vote error: "
                "{}".format(aggregate)
            )


def make_candidate(block: BaseBlock,
                   event: BaseEvent,
                   chain: BaseChain):
    # make candidate with prepared block

    if chain.is_validator:
        transactions = event.get_transaction()

        try:
            validate_transactions = validate_has_transactions(transactions, chain)
        except ValidationError:
            manager = getattr(event.event, 'transaction')
            manager.storage.delete_keys([tx.hash for tx in transactions])
            return False

        chain.logger.info("build new height ({})".format(chain.height + 1))

        trie = make_hash_root(validate_transactions)
        block.header.hash_transaction_root = trie.root

        block.header.timestamp = time.time()
        block.header.hash_candidate_block = block.pre_hash

        signature = chain.make_signature(block.pre_hash)

        return block.copy(header=block.header.copy(byte_signature=signature),
                          list_transactions=validate_transactions)


def select_candidate(permit_header: BaseHeader,
                     event: BaseEvent,
                     chain: BaseChain) -> CandidateContext:
    # pre-vote, select candidate for voting
    context = event.get_candidate(permit_header.num_height+1)
    # 3 ~ 4 candidate blk

    blk_list = context.get_data_list()

    validator_set = [blk.creator for blk in blk_list]

    validate_validator_set(validator_set, chain)

    filter_out_candidate(context)

    if len(context.data) > 1:
        computation_hash_distance(permit_header, context)

    return context


def make_vote(select_block,
              chain: BaseChain) -> BaseVote:
    if chain.is_validator:
        vote = prepare_vote(num_version=chain.version,
                            num_block_height=select_block.height,
                            hash_candidate_block=select_block.pre_hash,
                            address_creator=chain.nodebase)
        vote.hash_vote = vote.hash
        signature = chain.make_signature(vote.hash_vote)

        return vote.copy(byte_signature=signature)


def make_confirm_from_vote(height,
                           aggregate_vote_blk,
                           chain: BaseChain):
    if chain.is_validator:
        confirm_set = [str(height), chain.nodebase.decode(), aggregate_vote_blk.decode()]
        sig = chain.make_signature(sha3_hex(','.join(confirm_set)))
        confirm_set.append(sig.decode())

        return confirm_set


def aggregate_vote(select_header: BaseHeader,
                   event: BaseEvent,
                   chain: BaseChain,
                   logger):
    # aggregate vote for confirm
    context = event.get_vote(select_header.num_height)
    vt_list = context.get_data_list()
    validator_set = [vt.creator for vt in vt_list]
    validate_validator_set(validator_set, chain)
    blk_hash = aggregate_vote_from_context(select_header, context, logger)

    return blk_hash, context


def aggregate_confirm(confirm,
                      event: BaseEvent,
                      chain: BaseChain,
                      logger) -> BaseBlock:
    height, _, confirm_blk, _ = confirm

    # Todo: confirm event get() method 내부에서 데이터 파싱 로직 빼기 (리팩토링)
    #  confirm 데이터 파싱해서 잘못된 컨펌은 penalty 부여

    blk_hash, validator_set = event.get_confirm(height)

    validate_validator_set(validator_set, chain)

    if blk_hash != confirm_blk:
        # TODO: penalty progress, vote power down
        pass

    logger.debug("confirm-blk-set: {}".format((height, blk_hash)))

    context = event.get_candidate(int(height))

    final_blk = None

    for b in context:
        if b.pre_hash == blk_hash:
            final_blk = b
            break

    if final_blk is None:
        raise RoundError('confirm error: confirm block not exists')

    return final_blk.copy()


async def make_finalize_from_confirm(confirm_block: BaseBlock,
                                     context: VoteContext,
                                     chain: BaseChain):
    if confirm_block.creator == chain.nodebase:
        finalize_blk = await chain.make_finalize_from_confirm(confirm_block,
                                                              context.get_data_list())
        return finalize_blk, True
    else:
        return None, False




