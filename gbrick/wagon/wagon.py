

from gbrick.wagon.state import State
from gbrick.wagon.execute_context import ExecuteContext

from gbrick.types.prepare import prepare_receipt
from utils.trie.prepare import make_hash_root
from gbrick.wagon.executor import Executor

from utils.exceptions import (
    ValidationError, FinalizeError,
    CacheError
)

from gbrick.types.base import (
    BaseHeader, BaseTransaction, BaseBlock
)

from gbrick.wagon.base import (
    BaseWagon, BaseExecutor, BaseState
)


class Status:
    complete = 'completed'
    cancel = 'cancel'


class Wagon(BaseWagon):
    """ Vritual Machine: wagon
    :note: vm wagon: transaction execute, code execute
    """

    @property
    def status(self):
        if self._status is None:
            self._status = Status()
        return self._status

    @property
    def state(self) -> BaseState:
        if self._state is None:
            self._state = State(self._db_context, self.header)
        return self._state

    def genesis_declare(self, block, constant):
        return self.state.genesis_declare(block, constant)

    def set_execute_result(self, context: ExecuteContext, header, transaction):
        """ set receipt data
        :param ExecuteContext context: write to receipt on context
        :param BlockHeader header: write to height on current header
        :param Trasaction transaction: write to tx-hash on transaction
        :return: None
        """
        if context.is_error:
            status = self.status.cancel
        else:
            status = self.status.complete

        # TODO: computation result.
        receipt = prepare_receipt(hash_transaction=transaction.hash,
                                  fee_limit=context.limited,
                                  height=header.num_height,
                                  paid_fee=context.paid,
                                  created_address=context.create_address,
                                  status=status,
                                  message=context.message,
                                  error_message=context.error)
        self._receipts.append((context.index, receipt))
        self._total_paid += context.paid

    def prepare_executor(self, index, transaction) -> (ExecuteContext, BaseExecutor):
        """ prepare executor, execute context class
        :note:
            execute_context - context are use on executor
            executor - transaction execute on context
        :param int index: transaction indexed
        :param Transaction transaction: setup target
        :return: tuple(execute_context, executor)
        """
        nonce = self.state.state_db.get_nonce(transaction.address_sender)
        execute_context = ExecuteContext(index,
                                         transaction.address_sender,
                                         transaction.address_recipient,
                                         transaction.amount_value,
                                         transaction.amount_fee,
                                         nonce,
                                         transaction.type_transaction)
        return execute_context, Executor()

    async def execute_transaction(self,
                                  version,
                                  index,
                                  header: BaseHeader,
                                  transaction: BaseTransaction) -> None:
        """
        :param int version: chain version
        :param int index: transaction indexed
        :param BlockHeader header: block header
        :param Transaction transaction: execute target
        :return:
        """
        context, executor = self.prepare_executor(index, transaction)
        await self.state.execute_transaction(version, header, transaction, executor, context)
        self.set_execute_result(context, header, transaction)

    async def execute_transactions(self, version, block: BaseBlock) -> BaseBlock:
        """ execute transactions

        :param int version: chain version.
        :param Block block: next height block.
        :return: Block class
        """
        if block.height != self.header.num_height+1:
            raise ValidationError(
                "wagon is execute on height={}, "
                "currently doesn't execute on height={}".format(
                    self.header.num_height, block.height
                )
            )
        for index, transaction in enumerate(block.list_transactions):
            # self._tasks.add(
            #     asyncio.ensure_future(
            #         self.execute_transaction(version, index, block.header, transaction))
            # )
            await self.execute_transaction(version, index, block.header, transaction)

        # await self.event()
        self._receipts.sort(key=lambda obj: obj[0])
        self._trie = make_hash_root(
            [receipt for _, receipt in self._receipts]
        )
        self._pre_finalize(block)
        return block.copy(header=block.header.copy(hash_receipt_root=self._trie.root,
                                                   hash_state_root=self.state.cache_trie_root))

    def _set_reward(self, validator_id, reward):
        """
        :param bytes validator_id: validator account address
        :param int reward: block reward
        :return: None
        """
        validator = self._db_context.state.get_validator(validator_id)
        self._db_context.state.compute_balance(validator.address_account, reward)

    def __computation_block_rewards(self, block):
        """ The validator who vote are rewarded.
        :param Block block:
        :return: None
        """
        # block-creator -> block rewards [undefined]
        # ::vote validators rewards::
        # [power, penalty] ratio computation -> rewards ratio
        # base_reword * ratio : validators total rewards
        # vote pointer..
        
        validators = []
        for v in block.list_vote:
            if v.hash_candidate_block == block.pre_hash:
                validators.append(v.creator)
        # state -> get vt pow
        base_reward = self._total_paid // len(validators)
        for validator in validators:
            self._set_reward(validator, base_reward)

    def _pre_finalize(self, block):
        if block.height > 0:
            self.__computation_block_rewards(block)

    def finalize(self, block):
        self._commit(block)

    def _commit(self, block) -> None:
        # TODO: exceptions -> snapshot revert.
        try:
            self.state.commit()
            trie = make_hash_root(block.list_transactions)
            self._db_context.chain.set_trie(trie)
            self._db_context.chain.set_trie(self._trie)
            trie = make_hash_root(block.list_vote)
            self._db_context.chain.set_trie(trie)
            self._db_context.chain.commit(block)
        except CacheError:
            raise FinalizeError
        finally:
            self.clear()

    def clear(self):
        self._trie = None
        self._receipts.clear()
        self.state.clear()




