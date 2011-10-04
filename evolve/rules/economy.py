class ResourceSet(object):
    def __init__(self):
        self.data = {}

    def add(self, resource, amount, cost=0):
        current = self.data.get(resource, (0,0))
        new = (current[0]+amount, current[1]+cost)
        self.data[resource] = new

    def get(self, resource):
        return self.data.get(resource, (0,0))

    def contains(self, resource, amount):
        return resource in self.data and self.data[resource][0] >= amount
    
    def cost(self):
        return sum(cost for (resource,(amount, cost)) in self.data.iteritems())

class PaymentOption(object):
    def __init__(self):
        self.money = 0
        self.left_trade = ResourceSet()
        self.right_trade = ResourceSet()
        self.local = ResourceSet()

    def better_than(self, other):
        """
        Is this payment option strictly "better" than an alternative?
        
        Better means that in needs strictly less money in each direction
        """
        return (self.left_trade.cost() < other.left_trade.cost()) and (self.right_trade.cost() < other.right_trade.cost())

    def __unicode__(self):
        left = self.left_trade.cost()
        right = self.right_trade.cost()
        return "$%d ($%d left, $%d right)" % (self.money+left+right, left, right)


def empty_cost(cost):
    # cost is a dict, {resource_name: required_amount}. It also maps '$' to the needed money
    # returns True if there's something to pay
    return sum(cost.values())==0

def get_payments(cost, money, local_resources, left_resources, left_costs, right_resources, right_costs):
    results = get_payments_base(cost, money, local_resources, left_resources, left_costs, right_resources, right_costs)
    # This sorting order implies that, if an option is "better" than another, the "better" one is on the left
    results.sort(key=lambda o: (o.left_trade.cost()+o.right_trade.cost(), o.left_trade.cost()))
    clean_results = []
    for o in results:
        for c in clean_results:
            if c.better_than(o): break
        else: # If no item in clean_results better than o
            clean_results.append(o)
    return results

def get_payments_base(cost, money, local_resources, left_resources, left_costs, right_resources, right_costs):
    # cost is a dict, {resource_name: required_amount}. It also maps '$' to the needed money
    # money is an int, available money
    # local, left, right resources are lists of lists of (amount, resource). inner lists are alternatives
    # left, right costs are mappings from resource to money
    # Returns a list of payment options

    # Check for money:
    if empty_cost(cost):
        return [PaymentOption()]
    elif cost['$'] > 0:
        if cost['$'] > money:
            return [] # Not enough money
        else:
            money_payed = cost['$']
            cost['$'] = 0
            results = get_payments_base(cost, money-money_payed, local_resources, left_resources, left_costs, right_resources, right_costs)
            for o in results:
                o.money += money_payed
            return results
    # If local resources, try to pay with them first
    elif local_resources:
        alternatives = local_resources[0]
        # Ways to pay without using any of the alternatives
        results = get_payments_base(cost, money, local_resources[1:], left_resources, left_costs, right_resources, right_costs)
        # Ways to pay using each of the alternatives
        for amount, resource in alternatives:
            if cost[resource] > 0: # resource is useful to pay for the cost
                used_amount = min(amount, cost[resource])
                updated_cost = dict(cost)
                updated_cost[resource] = cost[resource] - used_amount
                new_results = get_payments_base(updated_cost, money, local_resources[1:], left_resources, left_costs, right_resources, right_costs)
                for o in new_results:
                    o.local.add(resource, used_amount)
                results += new_results
        return results
    # If left trade, try to pay with them
    elif left_resources:
        alternatives = left_resources[0]
        # Ways to pay without using any of the alternatives
        results = get_payments_base(cost, money, local_resources, left_resources[1:], left_costs, right_resources, right_costs)
        # Ways to pay using each of the alternatives
        for amount, resource in alternatives:
            if cost[resource] > 0: # resource is useful to pay for the cost
                unit_cost = left_costs[resource]
                assert unit_cost > 0 # Otherwise, range below fails
                used_amount = min(amount, cost[resource])
                for pay in range(unit_cost, min(money, used_amount*unit_cost)+1, unit_cost):
                    updated_cost = dict(cost)
                    updated_cost[resource] = cost[resource] - pay//unit_cost
                    new_results = get_payments_base(updated_cost, money-pay, local_resources, left_resources[1:], left_costs, right_resources, right_costs)
                    for o in new_results:
                        o.left_trade.add(resource, pay//unit_cost, pay)
                    results += new_results
        return results
    elif right_resources:
        alternatives = right_resources[0]
        # Ways to pay without using any of the alternatives
        results = get_payments_base(cost, money, local_resources, left_resources, left_costs, right_resources[1:], right_costs)
        # Ways to pay using each of the alternatives
        for amount, resource in alternatives:
            if cost[resource] > 0: # resource is useful to pay for the cost
                unit_cost = right_costs[resource]
                assert unit_cost > 0 # Otherwise, range below fails
                used_amount = min(amount, cost[resource])
                for pay in range(unit_cost, min(money, used_amount*unit_cost)+1, unit_cost):
                    updated_cost = dict(cost)
                    updated_cost[resource] = cost[resource] - pay//unit_cost
                    new_results = get_payments_base(updated_cost, money-pay, local_resources, left_resources, left_costs, right_resources[1:], right_costs)
                    for o in new_results:
                        o.right_trade.add(resource, pay//unit_cost, pay)
                    results += new_results
        return results
    else:
        return [] # Can't afford

