from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from moy_nalog.methods.method import BaseMethod
from moy_nalog.methods.api import BaseAPI
from moy_nalog.http import BASE_URL
from moy_nalog.exceptions import RejectedIncomeError
from moy_nalog.types import Income


class AddIncomeMethod(BaseMethod):
    def __init__(
        self,
        api: BaseAPI,
        name: str,
        created_at: date | datetime,
        quantity: int,
        amount: int | float,
    ) -> None:
        super().__init__(api)

        self.BASE_URL = "/income"

        self._name = name
        self._created_at = created_at
        self._quantity = quantity
        self._amount = Decimal(amount)

    @property
    def body(self) -> dict:
        return {
            "paymentType": "CASH",
            "ignoreMaxTotalIncomeRestriction": False,
            "client": {
                "contactPhone": None,
                "displayName": None,
                "incomeType": "FROM_INDIVIDUAL",
                "inn": None,
            },
            "requestTime": self._format_date_to_local_iso(),
            "operationTime": self._format_date_to_local_iso(self._created_at),
            "services": [
                {
                    "name": self._name,
                    "amount": float(
                        self._amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    ),
                    "quantity": self._quantity,
                }
            ],
            "totalAmount": float(
                (self._amount * self._quantity).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            ),
        }

    def _get_url(self, approved_receipt_uuid: str) -> str:
        inn = self._api.connection.auth.details.inn
        return f"{BASE_URL}/receipt/{inn}/{approved_receipt_uuid}"

    async def _make_request(self) -> dict:
        return await self._api.post(self.BASE_URL, self.body)

    async def execute(self) -> Income:
        response = await self._make_request()
        if not (approved_receipt_uuid := response.get("approvedReceiptUuid")):
            raise RejectedIncomeError("Cannot get approvedReceiptUuid")
        url = self._get_url(approved_receipt_uuid)

        return Income(
            id=approved_receipt_uuid,
            approved_receipt_uuid=approved_receipt_uuid,
            json_url=f"{url}/json",
            print_url=f"{url}/print",
        )
