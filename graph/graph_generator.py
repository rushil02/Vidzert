import random

import matplotlib.pyplot as plt

from graph.models import GraphCreationMeta


# Never change this value once set
coin_value = 0.01  # in INR


class _Graph(object):

    def __check_parameters(self):
        flag = True
        #  Zero value checks
        if coin_value == 0.0:
            flag = False
            self.error_meta.update({'ER_Zm1': 'Coin Value is Zero'})
        if int(self.people) == 0:
            flag = False
            self.error_meta.update({'ER_Zm2': 'No of people is Zero'})
        if self.max_coins == 0.0:
            flag = False
            self.error_meta.update({'ER_Zm3': 'Money is Zero'})
        if self.init_peak == 0.0:
            flag = False
            self.error_meta.update({'ER_Zm4': 'Initial peak is Zero'})
        if bool(self.win_models) is False:
            flag = False
            self.error_meta.update({'ER_Zm5': 'win model is empty'})
        if self.load_balancer_value == 0.0:
            flag = False
            self.error_meta.update({'ER_Zm6': 'Load Balancer Value is Zero'})

        # Other checks
        if self.people * self.base_limit >= self.max_coins:
            flag = False
            self.error_meta.update({'ER_m8': 'Money is too low with respect to base limit and people'})
        if self.max_coins <= 0:
            self.error_meta.update({'ER_m1': 'max_coins less than or equal to 0'})
            flag = False
        if self.peak_limit_coins <= 0:
            self.error_meta.update({
                'ER_m2': (str(self.base_limit) + ' coins - base limit is too high relative to money, '
                                                 'reduce people or base limit or increase money')})
            flag = False
        if (self.max_coins * self.init_peak) <= self.base_limit:
            self.error_meta.update({
                'ER_m3': 'No peak cannot be formed, not enough money'})
        return flag

    # Method 1
    def __initial_graph(self):
        current_coin = int(self.max_coins * self.init_peak)

        self.stats.update({'P0H': str(current_coin)})

        current_position = 0
        user_graph_position = 0
        total_coins = 0
        i = 1
        while current_coin > self.base_limit and current_position <= self.people:
            user_graph_position += 1
            self.user_dict.update({str(user_graph_position): str(current_coin)})
            for x in range(1, i + 1):
                total_coins += current_coin
                current_position += 1
                if current_position <= self.people:
                    self.model_dict.update({str(current_position): str(current_coin)})
                    self.user_pos_dict.update({str(current_position): str(user_graph_position)})
                else:
                    current_position -= 1
            i *= 2
            current_coin /= 2
        peak_coins = total_coins - (current_position * self.base_limit)

        self.stats.update({'P0C': str(current_position), 'P0T': str(peak_coins)})

        return current_position, user_graph_position, peak_coins

    # Method 3.1
    def __get_random_peak(self):  # Test this method for biased randomness on paper
        n = random.uniform(0, 1)
        upper_limit = 0.0
        select_peak = 0.0
        for ch in self.win_models:
            if upper_limit + self.win_models[ch] > n:
                select_peak = ch
                break
            upper_limit += self.win_models[ch]
        return select_peak

    # Method 2.2.1
    def __load_balancer(self, start_coin):
        # Increase randint range to decrease the probability of returning the same input value
        num = random.randint(1, 5)
        if num == 1:
            return start_coin
        else:
            start_coin /= random.randint(2, 10)
            if start_coin < (self.max_coins * min(self.win_models.keys())):
                start_coin *= 10
                return start_coin
            else:
                return self.__load_balancer(start_coin)

    # Method 2.2.2
    def __create_peak(self, start_coin):
        if start_coin <= self.base_limit:
            return 0, [], 0
        current_coin = start_coin
        total_coins = 0
        coverage = 0
        coins_list = []
        i = 1
        while current_coin > self.base_limit:
            for x in range(1, i + 1):
                total_coins += current_coin
                coins_list.append(current_coin)
                coverage += 1
            i *= 2
            current_coin /= 2

        total_coins = (total_coins * 2) - start_coin
        coverage = (coverage * 2) - 1

        coins_list_rev = list(coins_list)
        coins_list_rev.reverse()
        coins_list_rev.pop()
        coins_list_rev.extend(coins_list)  # Complete sequential list in peak order

        peak_coins = total_coins - (coverage * self.base_limit)
        return peak_coins, coins_list_rev, coverage

    # Method 2.2.3
    def __check_model_cost(self, total_peak_coins_orig, peak_coins):
        if peak_coins == 0:
            return total_peak_coins_orig, False
        else:
            total_peak_coins = total_peak_coins_orig
            total_peak_coins += peak_coins
            if total_peak_coins <= self.peak_limit_coins:
                return total_peak_coins, True
            else:
                return total_peak_coins_orig, False

    # Method 2.2.4
    def __find_smaller_peak(self, select_peak):
        temp = 0.0
        for ch in self.win_models:
            if temp < ch < select_peak:
                temp = ch
        return temp

    # Method 2.2.5
    def __find_larger_peak(self, select_peak):
        temp = max(self.win_models.keys())
        for ch in self.win_models:
            if temp > ch > select_peak:
                temp = ch
        return temp

    def __get_peak_1(self, select_peak, total_peak_coins):
        start_coin = int(self.max_coins * select_peak)

        if start_coin <= self.base_limit and not (select_peak == max(self.win_models.keys())):
            select_peak = self.__find_larger_peak(select_peak)  # Method 2.2.5
            return self.__get_peak_1(select_peak, total_peak_coins)  # Method 2.2
        elif start_coin <= self.base_limit and select_peak == max(self.win_models.keys()):
            return False, None, None, None, None, total_peak_coins
        else:
            return self.__get_peak_2(select_peak, total_peak_coins)

    # Method 2.2
    def __get_peak_2(self, select_peak, total_peak_coins):
        start_coin = int(self.max_coins * select_peak)

        if start_coin >= self.load_balancer_value:
            start_coin = self.__load_balancer(start_coin)  # Method 2.2.1

        peak_coins, coins_list, coverage = self.__create_peak(start_coin)  # Method 2.2.2
        total_peak_coins, flag = self.__check_model_cost(total_peak_coins, peak_coins)  # Method 2.2.3

        if flag is False:
            select_peak = self.__find_smaller_peak(select_peak)  # Method 2.2.4

            if not (select_peak == 0.0):
                return self.__get_peak_2(select_peak, total_peak_coins)  # Method 2.2
            else:
                return False, None, None, None, None, total_peak_coins
        else:
            return True, coins_list, start_coin, coverage, peak_coins, total_peak_coins

    # Method 3
    def __peaks_model_list(self, total_peak_coins):
        self.selected_peaks_dict = {}
        i = 0
        total_coverage = 0
        flag = True

        while flag:
            select_peak = self.__get_random_peak()  # Method 3.1

            # Method .2
            flag, coins_list, start_coin, coverage, peak_coins, total_peak_coins = self.__get_peak_1(select_peak,
                                                                                                     total_peak_coins)

            if flag is True:
                i += 1
                self.selected_peaks_dict.update({i: coins_list})

                # Stats
                self.stats.update({'P' + str(i) + 'H': str(start_coin),
                                   'P' + str(i) + 'C': str(coverage),
                                   'P' + str(i) + 'T': str(peak_coins)})

                total_coverage += coverage

        return total_peak_coins, total_coverage

    # Method 3.1
    def __create_last_peak(self, start_coin):
        current_coin = start_coin
        total_coins = 0
        coverage = 0
        coins_list = []
        i = 1

        while current_coin > self.base_limit:
            for x in range(1, i + 1):
                total_coins += current_coin
                coins_list.append(current_coin)
                coverage += 1
            i *= 2
            current_coin /= 2

        coins_list.reverse()
        peak_coins = total_coins - (coverage * self.base_limit)
        return peak_coins, coins_list, coverage

    # Method 2
    def __get_last_peak(self, total_peak_coins, current_position):
        aa = random.randint(0, 1)
        if aa is 1:
            last_peak = self.__get_random_peak()
            start_coin = int(self.max_coins * last_peak)

            if start_coin <= self.base_limit:
                return False, [], total_peak_coins, 0

            if start_coin >= self.load_balancer_value:
                start_coin = self.__load_balancer(start_coin)  # Method 2.2.1

            last_peak_coins, coins_list, coverage = self.__create_last_peak(start_coin)  # Method 3.1

            total_peak_coins, flag = self.__check_model_cost(total_peak_coins, last_peak_coins)  # Method 2.2.3

            if coverage + current_position >= self.people:
                flag = False

            if flag is True:

                self.stats.update({'LPH': str(start_coin),
                                   'LPC': str(coverage),
                                   'LPT': str(last_peak_coins)})

                return True, coins_list, total_peak_coins, coverage
            else:
                return False, [], total_peak_coins, 0

        else:
            return False, [], total_peak_coins, 0

    def _validate_model(self):
        i = 0
        total = 0.0
        total2 = 0.0
        flag = True
        highest_value = 0.0

        for key in self.model_dict:
            i += 1
            aa = float(self.model_dict[key])
            total += aa
            if aa > highest_value:
                highest_value = aa
            total2 += float(self.model_dict[str(i)])

        if i != self.people:
            self.error_meta.update({'ER_m5': 'graph exceeded number of people'})
            flag = False
        if total != total2:
            self.error_meta.update({'ER_m6': 'graph constructed with key errors'})
            flag = False
        if total2 > self.max_coins or total > self.max_coins:
            self.error_meta.update({'ER_m1': 'graph exceeded total money'})
            flag = False

        return flag, highest_value

    # Main Method
    def generate_model(self):
        assert self.__check_parameters(), "ERROR: Corrupt Arguments"
        # Initial peak
        current_position, user_graph_position, peak_coins = self.__initial_graph()  # Method 1
        # Validation of initial peak
        ii = 0
        while peak_coins > self.peak_limit_coins:
            ii += 1
            self.error_meta.update({'ER_init_peak_' + str(ii): str(self.init_peak) + ' - initial peak coins > limit'})
            if self.init_peak > min(self.win_models.keys()):
                self.init_peak = self.__find_smaller_peak(self.init_peak)
                self.user_pos_dict = {}
                self.model_dict = {}
                self.user_pos_dict = {}
                current_position, user_graph_position, peak_coins = self.__initial_graph()
            else:
                assert False, "ERROR: peak can not be formed @ initial"

        # Last peak
        # Method 2
        last_peak_flag, last_peak_coins_list, peak_coins, last_peak_coverage = self.__get_last_peak(peak_coins,
                                                                                                    current_position)

        # Populate all random peaks
        peak_coins, coverage = self.__peaks_model_list(peak_coins)  # Method 3

        # Stats
        self.stats.update({'TPC': str(peak_coins),
                           'TPCo': str(coverage + current_position + last_peak_coverage),
                           'NP': str(len(self.selected_peaks_dict)), 'LPF': str(last_peak_flag),
                           })

        # Integrate peak system in model
        length = float((self.people - (current_position + last_peak_coverage))) / (len(self.selected_peaks_dict) + 1)
        domain_set = length * 0.5
        marker = current_position

        while bool(self.selected_peaks_dict):
            marker += length

            peak = random.choice(self.selected_peaks_dict.keys())
            peak_coin_list = self.selected_peaks_dict[peak]
            del self.selected_peaks_dict[peak]

            current_peak_coverage = int(self.stats['P' + str(peak) + 'C'])

            # Contingency ==>> likely for small number of people
            if (marker - domain_set) > current_position:
                aa = int(random.uniform((marker - domain_set), (marker + domain_set)))
            elif (marker - domain_set) <= current_position < (marker + domain_set):
                aa = int(random.uniform((current_position + 1), (marker + domain_set)))
            else:
                del self.stats['P' + str(peak) + 'C']
                del self.stats['P' + str(peak) + 'H']
                del self.stats['P' + str(peak) + 'T']
                self.stats['NP'] = str(int(self.stats['NP']) - 1)
                continue

            if current_position < aa and current_position < (self.people - last_peak_coverage):
                user_graph_position += 1
                self.user_dict.update({str(user_graph_position): str(int(self.base_limit))})
            while current_position < aa and current_position < (self.people - last_peak_coverage):
                current_position += 1
                if current_position <= self.people:
                    self.model_dict.update({str(current_position): str(int(self.base_limit))})
                    self.user_pos_dict.update({str(current_position): str(user_graph_position)})
                else:
                    current_position -= 1

            if current_position < (self.people - (last_peak_coverage + current_peak_coverage)):
                for coin in peak_coin_list:
                    if coin != int(self.model_dict[str(current_position)]):
                        user_graph_position += 1
                        self.user_dict.update({str(user_graph_position): str(coin)})
                    current_position += 1

                    self.model_dict.update({str(current_position): str(coin)})
                    self.user_pos_dict.update({str(current_position): str(user_graph_position)})
            else:
                del self.stats['P' + str(peak) + 'C']
                del self.stats['P' + str(peak) + 'H']
                del self.stats['P' + str(peak) + 'T']
                self.stats['NP'] = str(int(self.stats['NP']) - 1)
                continue

        last_milestone = self.people - last_peak_coverage

        if current_position <= last_milestone:
            user_graph_position += 1
            self.user_dict.update({str(user_graph_position): str(int(self.base_limit))})
        while current_position < last_milestone:
            current_position += 1
            if current_position <= self.people:
                self.model_dict.update({str(current_position): str(int(self.base_limit))})
                self.user_pos_dict.update({str(current_position): str(user_graph_position)})
            else:
                current_position -= 1

        if last_peak_flag:
            for coin in last_peak_coins_list:
                if coin != int(self.model_dict[str(current_position)]):
                    user_graph_position += 1
                    self.user_dict.update({str(user_graph_position): str(coin)})
                current_position += 1
                if current_position <= self.people:
                    self.model_dict.update({str(current_position): str(coin)})
                    self.user_pos_dict.update({str(current_position): str(user_graph_position)})
                else:
                    current_position -= 1

        flag_final, highest_value = self._validate_model()
        assert flag_final, "ERROR: model could not be generated correctly"
        return highest_value

    def plot_graph(self, file_location, file_name):

        key_list = []
        value_list = []

        for key in self.model_dict:
            key_list.append(int(key))
            value_list.append(int(self.model_dict[key]))

        fig = plt.figure(figsize=(20, 10))
        aa = fig.add_subplot(1, 1, 1)

        aa.scatter(key_list, value_list)
        aa.set_title(file_name)
        aa.set_xlabel("Position")
        aa.set_ylabel("Coins")

        fig.savefig(file_location, dpi=300)

    def __init__(self, base_limit, people, money, init_peak, win_models, load_balancer_value):
        # Do not modify
        self.stats = {}  # model's final statistics
        self.model_dict = {}  # complete model
        self.user_dict = {}  # for display at front end
        self.user_pos_dict = {}  # key mapping between model_dict and user_dict
        self.error_meta = {}  # stores error if any

        self.base_limit = base_limit / coin_value
        self.people = people
        self.max_coins = money / coin_value
        self.init_peak = init_peak
        self.win_models = win_models
        self.peak_limit_coins = self.max_coins - (self.base_limit * self.people)
        self.load_balancer_value = load_balancer_value / coin_value

        self.stats.update({'BL': str(self.base_limit), 'CV': str(coin_value), 'WM': str(self.win_models),
                           'MO': str(money), 'PP': str(self.people), 'IP': str(self.init_peak),
                           'PLC': str(self.peak_limit_coins), 'LBV': str(self.load_balancer_value)})


class VideoGraph(_Graph):
    def _fetch_meta(self):
        # win_models -> dictionary {win_model_percentage: probability} ===>> check for summation(probability) = 1
        self.win_models, meta_values = GraphCreationMeta.objects.get_graph_meta('V')

        # Initial peak percentage
        try:
            self.init_peak = meta_values['init_peak']
        except KeyError:
            self.init_peak = 0.0
        # Coin value at which peak load balancer is initiated
        try:
            self.load_balancer_value = meta_values['load_balancer_value']
        except KeyError:
            self.load_balancer_value = 0.0
        # lowest value to be given to promoter in INR
        try:
            self.base_limit = meta_values['base_limit']
        except KeyError:
            self.base_limit = 0.0
        # Percentage of value to be deducted if the video is featured
        try:
            self.featured_cost_percentage = meta_values['featured_cost_percentage']
        except KeyError:
            self.featured_cost_percentage = 0.0
        # Charge for one person at Client end
        try:
            self.per_person_cost = meta_values["per_person_cost"]
        except KeyError:
            self.per_person_cost = 0.0
        # money to be spent of total
        try:
            self.expense_percentage = meta_values["expense_percentage"]
        except KeyError:
            self.expense_percentage = 0.0

    def __init__(self, featured, money):
        self._fetch_meta()

        if featured:
            net_money = money - (money * self.featured_cost_percentage)
        else:
            net_money = money

        people = int(net_money / self.per_person_cost)

        spend_money = net_money * self.expense_percentage

        super(VideoGraph, self).__init__(base_limit=self.base_limit, people=people, money=spend_money,
                                         init_peak=self.init_peak, win_models=self.win_models,
                                         load_balancer_value=self.load_balancer_value)


class SurveyGraph(_Graph):
    def _fetch_meta(self):
        # win_models -> dictionary {win_model_percentage: probability} ===>> check for summation(probability) = 1
        self.win_models, meta_values = GraphCreationMeta.objects.get_graph_meta('S')

        # Initial peak percentage
        try:
            self.init_peak = meta_values['init_peak']
        except KeyError:
            self.init_peak = 0.0
        # Coin value at which peak load balancer is initiated
        try:
            self.load_balancer_value = meta_values['load_balancer_value']
        except KeyError:
            self.load_balancer_value = 0.0
        # lowest value to be given to promoter in INR
        try:
            self.base_limit = meta_values['base_limit']
        except KeyError:
            self.base_limit = 0.0
        # Percentage of value to be deducted if the video is featured
        try:
            self.featured_cost_percentage = meta_values['featured_cost_percentage']
        except KeyError:
            self.featured_cost_percentage = 0.0
        # Charge for one person at Client end
        try:
            self.per_person_cost = meta_values["per_person_cost"]
        except KeyError:
            self.per_person_cost = 0.0
        # money to be spent of total
        try:
            self.expense_percentage = meta_values["expense_percentage"]
        except KeyError:
            self.expense_percentage = 0.0

    def __init__(self, featured, money):
        self._fetch_meta()

        if featured:
            net_money = money - (money * self.featured_cost_percentage)
        else:
            net_money = money

        people = int(net_money / self.per_person_cost)

        spend_money = net_money * self.expense_percentage
        super(SurveyGraph, self).__init__(base_limit=self.base_limit, people=people, money=spend_money,
                                          init_peak=self.init_peak, win_models=self.win_models,
                                          load_balancer_value=self.load_balancer_value)
