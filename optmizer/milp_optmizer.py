import pulp as pl
import re


class Milp_Opt:
    def __init__(self, communication_strategy):
        self.cs = communication_strategy

    def opt(self, selected_clients):
        selected_clients = selected_clients.copy()

        # Creation of the assignment problem
        model = pl.LpProblem("Max_Prob", pl.LpMaximize)

        # Decision Variables
        x = [[[pl.LpVariable(f"x_{i}_{j}_{k}", cat=pl.LpBinary) for k in range(len(self.cs.tm.user_power))] for j in
              range(self.cs.tm.rb_number)] for i in range(len(selected_clients))]

        # Objective function
        model += pl.lpSum(
            ((self.cs.W[selected_clients[i]][j][k] * x[i][j][k]) - (self.cs.lmbda * self.cs.tm.user_power[k] * self.cs.tm.user_delay[selected_clients[i]][j][k] * x[i][j][k]))
            for k in range(len(self.cs.tm.user_power)) for j in range(self.cs.tm.rb_number)
            for i in range(len(selected_clients))), "Max"

        model += pl.lpSum([x[i][j][k] for k in range(len(self.cs.tm.user_power)) for j in range(self.cs.tm.rb_number) for i in
                           range(len(selected_clients))]) <= self.cs.min_fit_clients, f"min_fit_clients"

        # Constraints: Each customer is assigned to exactly one channel and power
        for i in range(len(selected_clients)):
            model += pl.lpSum(x[i][j][k] for k in range(len(self.cs.tm.user_power)) for j in
                              range(self.cs.tm.rb_number)) >= 0, f"Customer_Channel_Constraints_{i} >= 0"

        for i in range(len(selected_clients)):
            model += pl.lpSum(x[i][j][k] for k in range(len(self.cs.tm.user_power)) for j in
                              range(self.cs.tm.rb_number)) <= 1, f"Customer_Channel_Constraints_{i} <= 1"

        # Constraints: Each channel is assigned to exactly one customer
        for j in range(self.cs.tm.rb_number):
            model += pl.lpSum(x[i][j][k] for k in range(len(self.cs.tm.user_power)) for i in
                              range(len(selected_clients))) >= 0, f"Channel_Customer_Constraints_{j} >= 0"

        for j in range(self.cs.tm.rb_number):
            model += pl.lpSum(x[i][j][k] for k in range(len(self.cs.tm.user_power)) for i in
                              range(len(selected_clients))) <= 1, f"Channel_Customer_Constraints_{j} <= 1"

        for i in range(len(selected_clients)):
            for j in range(self.cs.tm.rb_number):
                for k in range(len(self.cs.tm.user_power)):
                    model += x[i][j][k] * self.cs.tm.user_delay[selected_clients[i]][j][
                        k] <= self.cs.delay_requirement, f"Delay_Constraints_{i}_{j}_{k}"
                    model += x[i][j][k] * self.cs.tm.user_upload_energy[selected_clients[i]][j][
                        k] <= self.cs.energy_requirement, f"Energy_Constraints_{i}_{j}_{k}"
                    model += x[i][j][k] * self.cs.tm.q[selected_clients[i]][j][
                        k] <= self.cs.error_rate_requirement, f"Packet_Error_Rate_Constraints_{i}_{j}_{k}"

        ################
        # Solving the problem
        status = model.solve()
        print(pl.LpStatus[status])
        print("Total cost:", pl.value(model.objective))

        _selected_clients = []
        _rb_allocation = []
        _user_power_allocation = []
        for var in model.variables():
            if pl.value(var) == 1:
                indices = [int(i) for i in re.findall(r'\d+', var.name)]
                _selected_clients.append(selected_clients[indices[0]])
                _rb_allocation .append(indices[1])
                _user_power_allocation.append(indices[2])

        print("<<<<<<<<<")
        for i in range(len(_selected_clients)):
            print(f"Device {i + 1}: {_selected_clients[i]} assigned to the Channel {_rb_allocation[i]} "
                  f"with power {self.cs.tm.user_power[_user_power_allocation[i]]} - "                
                  f"distance: {self.cs.tm.user_distance[_selected_clients[i]]}")

        return _selected_clients.copy(), _rb_allocation.copy(), _user_power_allocation.copy()
