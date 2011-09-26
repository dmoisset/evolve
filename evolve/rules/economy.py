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
        return sum(cost for (resource,(amount, cost)) in self.data)

class PaymentOption(object):
    def __init__(self):
        self.money = 0
        self.left_trade = ResourceSet()
        self.right_trade = ResourceSet()
        self.local = ResourceSet()

def empty_cost(cost):
    # cost is a dict, {resource_name: required_amount}. It also maps '$' to the needed money
    # returns True if there's something to pay
    return sum(cost.values())==0

def get_payments(cost, money, local_resources, left_resources, left_costs, right_resources, right_costs):
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
            results = get_payments(cost, money-money_payed, local_resources, left_resources, left_costs, right_resources, right_costs)
            for o in results:
                o.money += money_payed
            return results
    # If local resources, try to pay with them first
    elif local_resources:
        alternatives = local_resources[0]
        # Ways to pay without using any of the alternatives
        results = get_payments(cost, money, local_resources[1:], left_resources, left_costs, right_resources, right_costs)
        # Ways to pay using each of the alternatives
        for amount, resource in alternatives:
            if cost[resource] > 0: # resource is useful to pay for the cost
                used_amount = max(amount, cost[resource])
                updated_cost = dict(cost)
                updated_cost[resource] = cost[resource] - used_amount
                new_results = get_payments(updated_cost, money, local_resources[1:], left_resources, left_costs, right_resources, right_costs)
                for o in new_results:
                    o.local.add(resource, used_amount)
                results += new_results
        return results
    else:
        return [] # Can't afford

