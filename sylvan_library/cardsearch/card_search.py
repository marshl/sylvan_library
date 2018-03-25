from cardsearch.parameters import AndParam, CardSortParam, CardNameSortParam


class CardSearch:
    def __init__(self):
        self.root_parameter = AndParam()
        self.sort_params = list()

    def add_sort_param(self, sort_param: CardSortParam):
        self.sort_params.append(sort_param)

    def result_search(self):
        result = self.root_parameter.get_result()
        self.add_sort_param(CardNameSortParam())
        result = result.order_by(*[order for sort_param in self.sort_params for order in sort_param.get_sort_list()])
        return result
