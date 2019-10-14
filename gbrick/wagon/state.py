
from gbrick.validation import validate_transaction

from gbrick.wagon.base import (
    BaseState, BaseExecutor, BaseExecuteContext
)
from utils.exceptions import ValidationError, FeeLimitedError
from gbrick.db.base import BaseStateDB
from gbrick.validation import validate_payable

from gbrick.types.base import (
    BaseHeader, BaseTransaction
)


class State(BaseState):

    @property
    def cache_trie_root(self):
        return self.state_db.cache_trie_root

    @property
    def state_db(self) -> BaseStateDB:
        return self._db_context.state

    @property
    def state_root(self):
        return self.state_db.state_root

    def genesis_declare(self, block, constant):
        return self._genesis_declare(block, constant)

    def _genesis_declare(self, block, constant):
        """
        :param Block block: Genesis block
        :param Constant constant: genesis data
        :return: Block
        """
        self.state_db.set_root(constant.none_root)
        self.state_db.set_minimum(constant.minimum)
        self.state_db.set_balance(constant.creator, constant.published_balance)
        for address, validator_id, signature in constant.constant_validator:
            self.state_db.increase_nonce(constant.creator)
            self.state_db.increase_nonce(address)
            self.state_db.compute_balance(constant.creator, -1 * constant.minimum)
            self.state_db.compute_balance(address, constant.minimum)
            self.state_db.set_delegated(address, address, constant.minimum)
            self.state_db.register_validator(address, validator_id, signature)
        self.commit()
        header = block.header.copy(hash_state_root=self.state_root,
                                   hash_transaction_root=constant.none_root,
                                   hash_vote_root=constant.none_root,
                                   hash_receipt_root=constant.none_root)
        return block.copy(header=header)

    async def execute_transaction(self,
                                  version,
                                  header: BaseHeader,
                                  transaction: BaseTransaction,
                                  executor: BaseExecutor,
                                  context: BaseExecuteContext):
        """ execute to transaction on executor
        :param int version: chain version
        :param BlockHeader header: validation on state header
        :param Transaction transaction: validation on transaction
        :param Executor executor: execute transaction
        :param ExecuteContext context: context are use on executor
        :return: NoReturn
        >>> execute_transaction(1, Header, Transaction, Executor, Context)
        """
        if header.num_height != self.header.num_height+1:
            raise ValidationError(
                "execute transaction on height={}, "
                "currently doesn't execute on height={}".format(
                    self.header.num_height, header.num_height
                )
            )

        try:
            await self.validate_transaction(version, transaction)
            await executor(self, context, transaction)
        except (ValidationError, FeeLimitedError) as err:
            context.set_error(err)
            self.state_db.compute_balance(context.txbase, context.fee_remainder)
        # try:
        #     await self.validate_transaction(version, transaction)
        # except ValidationError as err:
        #     context.set_error(err)
        # else:
        #     try:
        #         await executor(self, context, transaction)
        #     except (ValidationError, FeeLimitedError) as err:
        #         context.set_error(err)
        #         self.state_db.compute_balance(context.txbase, context.fee_remainder)

            # receipt db put error data

    async def validate_transaction(self, version, transaction: BaseTransaction):
        """ validation sender, hash, signature, payable
        :param int version: chain version
        :param Transaction transaction: validation transaction
        :return:NoReturn
        """
        if version != transaction.num_version:
            raise ValidationError(
                "transaction version {}, "
                "current chain version {}".format(
                    version, transaction.num_version
                )
            )
        await validate_transaction(transaction)
        balance = self.state_db.get_balance(transaction.address_sender)
        validate_payable(transaction, balance)

    def commit(self):
        self.state_db.commit()

    def clear(self):
        self.state_db.clear()



