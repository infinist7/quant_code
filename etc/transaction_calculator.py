class stock_transaction_calculator:
    def __init__(self):
        self.total_stock = 0  # 총 주식 수
        self.total_amount = 0  # 총 매수 금액
        self.net_profit = 0
        self.transactions = []  # 모든 거래 기록

    def buy(self, price, quantity):
        self.total_amount += price * quantity
        self.total_stock += quantity

        average_price = self.total_amount / self.total_stock

        self.transactions.append({
            'type': '매수',
            'price': price,
            'quantity': quantity,
            'average_price': average_price
        })

        print(f"매수: {quantity}주를 {price}원에 매수. 새로운 평균 매수 단가: {average_price:.2f}원")

    def sell(self, price, quantity):
        if quantity > self.total_stock:
            print(f"매도 불가: 보유한 주식 수보다 더 많은 {quantity}주를 매도하려고 했습니다.")
            return

        average_price = self.total_amount / self.total_stock
        sell_amount = price * quantity
        cost_of_sold_shares = average_price * quantity
        profit_loss = sell_amount - cost_of_sold_shares

        self.total_amount -= cost_of_sold_shares
        self.total_stock -= quantity
        self.net_profit += profit_loss

        self.transactions.append({
            'type': '매도',
            'price': price,
            'quantity': quantity,
            'profit_loss': profit_loss
        })

        if profit_loss > 0:
            print(f"매도: {quantity}주를 {price}원에 매도. 수익: {profit_loss:.2f}원")
        else:
            print(f"매도: {quantity}주를 {price}원에 매도. 손실: {profit_loss:.2f}원")

    def get_summary(self):
        print("거래기록")
        for transaction in self.transactions:
            if transaction['type'] == '매수':
                print(
                    f"매수: {transaction['quantity']}주를 {transaction['price']}원에 매수. 평균 단가: {transaction['average_price']:.2f}원")
            else:
                print(
                    f"매도: {transaction['quantity']}주를 {transaction['price']}원에 매도. 수익/손실: {transaction['profit_loss']:.2f}원")

        print("\n\n")
        print("거래결과")
        print(f"순수익: {self.net_profit:.2f}원")
        print(f"남은 보유 주식 수: {self.total_stock}주")
        print(f"평단: {self.total_amount / self.total_stock:.2f}원")
        print(f"남은 매수 금액: {self.total_amount:.2f}원")