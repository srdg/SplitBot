from os import path
import logging as logger 


n, expenses, filename = None, None, None
user_map, reverse_user_map = {}, {}
cash_flow = []

def read_matrix():
    """Read info from file"""
    expenses = None
    global filename
    read_string = ''
    with open(filename) as f:
        read_string = f.read().strip()
    
    expenses = [[float(item) for item in row.split(' ')] for row in read_string.split('\n')] 
    return expenses

def write_matrix():
    """Serialize info to file"""
    global expenses, filename
    write_string = ''
    for row in expenses:
        write_string += ' '.join([str(i) for i in row])
        write_string += '\n'
    with open(filename, 'w+') as f:
        f.write(write_string)

def prune_graph(amounts):
    """Optimize the net payable amount graph to minimize the cash flow"""
    global cash_flow
    maxCrd = amounts.index(max(amounts)) # index of user who gets paid the max amount (+ve)
    maxDeb = amounts.index(min(amounts)) # index of user who has to pay the max amount(-ve)

    if amounts[maxCrd] == 0 and amounts[maxDeb] == 0:
        return 0
    
    min_payable = min(amounts[maxCrd], -amounts[maxDeb]) 
    amounts[maxCrd] -= min_payable
    amounts[maxDeb] += min_payable

    cash_flow.append("{} pays {:.2f} to {}".format(user_map[maxDeb], min_payable, user_map[maxCrd]))
    prune_graph(amounts)

def optimize_cost():
    """Read the expense matrix and calculate the net payable amount graph"""
    global expenses, filename
    if path.exists(filename) and path.isfile(filename):
        expenses = read_matrix()

    amounts = []
    for row in range(n):
        net_amt = 0 # net amount payable to/from <user[row]> 
        for col in range(n):
            net_amt += expenses[row][col]-expenses[col][row] # paid - owed
        amounts.append(net_amt)

    prune_graph(amounts)

def set_entries(payer, users, amount, split_as='-1'):
    """Add expense entry to matrix"""
    global expenses, reverse_user_map
    payer_index = reverse_user_map[payer.strip().capitalize()]
    
    if users == 'all':
        users = list(reverse_user_map.keys())
    else:
        users = users.split(',')


    payable_amt = {}
    if split_as == '-1':
        for user in users:
            user_index = reverse_user_map[user.strip().capitalize()]
            payable_amt[user_index] = amount/len(users)
    else:
        payable_amts = [float(i.strip()) for i in split_as.strip().split(',')]
        assert sum(payable_amts) == amount, "The split amount does not equate to original amount"
        assert len(payable_amts) == len(users), "Please make sure you give the amount to split for all users,else give -1, or skip it, to distribute it equally."
        for user_counter in range(len(users)):
            user_index = reverse_user_map[users[user_counter].strip().capitalize()]
            payable_amt[user_index] = payable_amts[user_counter]

    for user in users : 
        user_index = reverse_user_map[user.strip().capitalize()]
        expenses[payer_index][user_index] += payable_amt[user_index]


def log_payment(args):
    """Log payment entry and add to expense"""
    global expenses
    if path.exists(filename) and path.isfile(filename):
        expenses = read_matrix()
    amount, paid_by, paid_to, paid_for, split_as = args['amount'], args['paidby'], args['paidto'], args['paidfor'], args['splitas']
    set_entries(paid_by, paid_to, amount, split_as)
    # TODO write in csv / feather format
    logmsg = "{0} paid {1} INR on behalf of {2} for {3}".format(paid_by, amount, paid_to, paid_for)
    logger.info(logmsg)
    write_matrix()
    return logmsg


def init_tracking(message):
  global n, expenses, filename
  global user_map, reverse_user_map

  msg = message.content
  users = [username.strip().capitalize() for username in msg[msg.index(' ')+1:].split(',')]
  # Ideally, the following filename has to be a writable file.
  filename = 'expenses/'+message.channel.name+'.txt'
  logger.basicConfig(filename='logs/'+message.channel.name+'.log', format='[%(levelname)s] %(message)s', level=logger.INFO)
  n = len(users)
  expenses = [[0 for i in range(n)] for j in range(n)]
  for user_idx in range(len(users)):
    user_map[user_idx] = users[user_idx]
    reverse_user_map[users[user_idx]] = user_idx
  write_matrix()
  return "Initialized tracking for {}! Group members are {}".format(message.channel.name,', '.join(users))


def add_entry(message):
  """Assumes each person adds their own entries"""
  # parse args
  args = {}
  msg = message.content.split(' ')
  #paid <amount> <msg> [<payee>] [<split>]
  #e.g. paid 3549.20 "taxi ride"
  #e.g. paid 104.35 snacks PersonA,PersonB 100,4.35
  args['paidby'] = message.author.name
  args['amount'] = float(msg[1])
  args['paidfor'] = msg[2]
  if len(msg) == 3:
    args['paidto'] = msg[3]
  else:
    args['paidto'] = 'all'
  if len(msg) == 4:
    args['splitas'] = msg[4]
  else:
    args['splitas'] = '-1'
  return log_payment(args)
