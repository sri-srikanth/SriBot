import os, pyotp, schedule, time, threading
import robin_stocks.robinhood as rs

class SriBot:
   """
   SriBot class that handles all rebalancing and maintenance operations for a Robinhood portfolio.
   """
   def __init__(self, weights: dict) -> None:
      """
      Initializer method for SriBot instances. Requires a dictionary of weights
      to set up bot.

      Args:
          weights (dict): Dictionary {str:float} of weights with each key
          representing a ticker symbol and its corresponding value
          representing its weight. Weights must add up to 1.0.
      """
      # Create new Robinhood session using user credentials
      self.login()
      # Store user-desired weights
      self.weights: dict = {}
      weightSum: float = 0
      for w in weights.items():
         # Check for negative weights
         if w[1] < 0:
            raiseError(BOT=self, msg=f'Symbol ({w[0]}) weight cannot be negative!')
         weightSum += w[1]
         # Ensure total portfolio weight <= 1.0
         if weightSum > 1.0:
            raiseError(self, msg='Total portfolio weight cannot exceed 1.0!')
         # Add symbol and corresponding weight to self.weights
         self.weights[w[0]] = w[1]
         
      # Lazy-load user's current Robinhood positions and account details
      self.positions: dict | None = None
      self.account: dict | None = None
      
   def login(self):
      """
      Log into Robinhood using user-provided credentials. TODO: Take user input?
      """
      # Generate 2FA TOTP using Robinhood master keys
      masterKey: str | None = os.environ.get('Tester266MastK')
      totp: str = pyotp.TOTP(s=masterKey if masterKey else '').now()
      # Log into Robinhood using UN/PWD & TOTP
      rs.login(username=os.environ.get('Tester266Email'), password=os.environ.get('Tester266Pass'), mfa_code=totp, store_session=True)
      print('Logged into Robinhood. Hello from SriBot!')
        
   def rebalance(self):
      """
      Portfolio rebalancing method. Method analyzes user's current positions
      and determines whether portfolio rebalancing is required (TODO: based on 
      a threshold?). If rebalancing is required, overweight positions are 
      trimmed and underweight positions are added to.
      """
      print('REBALANCING...')
      # Update user's current Robinhood positions and account details prior to 
      # rebalancing
      self.positions = rs.build_holdings()
      self.account = rs.build_user_profile()
      # Initialize dictionary to hold needed changes to portfolio
      positionChanges: dict = {k:0 for k in self.weights}
      # Check if positions out-of-balance by ANY (TODO: change?) amount
      for w in self.weights.items():
         # Calculate ideal position value based on account size
         idealAmount: float = w[1] * float(self.account['equity'])
         # Get current position value in portfolio
         try:
            currAmount: float = float(self.positions[w[0]]['equity'])
         except KeyError:
            currAmount: float = 0
         # Calculate change needed in position value to reach ideal weighting
         positionChanges[w[0]] -= round(number=currAmount-idealAmount, ndigits=6)
      positionChanges.pop('$$$')
      print(positionChanges)
      
      # Execute trades based on required position changes
      for stock in positionChanges.items():
         # Overweight stock in portfolio by more than RH fractional share order 
         # minimum
         if stock[1] <= -1.0:
            rs.order_sell_fractional_by_price(symbol=stock[0], amountInDollars=abs(stock[1]), timeInForce='gfd', extendedHours=True)
            print('SOLD', stock[0], '@', stock[1])
         # Underweight stock in portfolio by more than RH fractional share 
         # order minimum
         elif stock[1] >= 1.0:
            rs.order_buy_fractional_by_price(symbol=stock[0], amountInDollars=stock[1], timeInForce='gfd', extendedHours=True)
            print('BOUGHT', stock[0], '@', stock[1])
   
   def logout(self):
      """
      Ends currently active Robinhood session.
      """
      # Log out of currently active Robinhood session. Must not be called 
      # without an active session.
      rs.logout()
      print('Logged out of Robinhood. Goodbye from SriBot!')
      
def raiseError(BOT: SriBot, msg: str):
   """
   Error handling function for easy debugging. Only to be called during an 
   active Robinhood session (while logged in). Logs out of current Robinhood 
   session and terminates SriBot with exception.

   Args:
       BOT (SriBot): SriBot instance to raise error for.
       msg (str): Error description.

   Raises:
       Exception: Exception that is raised to terminate the bot with 
       appropriate msg.
   """
   # Log out and terminate bot with exception
   BOT.logout()
   raise Exception(msg)

def autoRebalance(BOT: SriBot):
   """
   Facilitates automatic rebalancing upon daily market open. Function logs in 
   first to ensure active Robinhood session exists and rebalances portfolio.

   Args:
       BOT (SriBot): Instance of SriBot whose portfolio to rebalance.
   """
   # Schedule Robinhood login and portfolio rebalancing to repeat daily at 
   # market open.
   schedule.every().day.at(time_str='08:30').do(job_func=BOT.login)
   schedule.every().day.at(time_str='08:31').do(job_func=BOT.rebalance)
   # Continue running all pending tasks in scheduler throughout SriBot runtime
   while True:
      schedule.run_pending()
      time.sleep(1)

def REPL(BOT: SriBot):
   """
   Run-Eval-Print-Loop to execute user commands during SriBot's runtime. Runs 
   on main thread and terminates SriBot & main thread upon receiving user 
   command to log out.
   Supported commands:
      l, logout         Logs out of currently active Robinhood session and 
                        terminates SriBot/main thread.
      r, rebalance      Runs rebalancing function.
      p, positions      Displays all of user's currently held Robinhood 
                        positions (incl. their current prices, quantities in 
                        portfolio, cost basis, total equity in portfolio, and 
                        total return) and net account value & free cash.

   Args:
       BOT (SriBot): SriBot instance to run REPL for.
   """
   # Run until termination of main thread
   while True:
      # Request user input and store as an all-lowercase string
      action = input('What would you like SriBot to do?: ').lower()
      # Evaluate user input
      match action:
         # 'Logout' command
         case 'l' | 'logout':
            BOT.logout()
            exit()
         # 'Rebalance' command
         case 'r' | 'rebalance':
            BOT.rebalance()
         # 'View Positions' command
         case 'p' | 'positions':
            # Fetch user's current Robinhood positions and account details if 
            # not already loaded
            if not BOT.positions or not BOT.account:
               BOT.positions = rs.build_holdings()
               BOT.account = rs.build_user_profile()
            # Print intro divider
            print('-------------------------------\n           POSITIONS           \n-------------------------------')
            # Print position details for all positions
            for pos in BOT.positions.items():
               print(f'{pos[0]} ({pos[1]['name']}): \n')
               print('Price: $' + pos[1]['price'])
               print('Quantity:', pos[1]['quantity'], 'share(s)')
               print('Cost Basis: $' + pos[1]['average_buy_price'])
               print('Total Equity: $' + pos[1]['equity'])
               sign = '(-' if pos[1]['price'] > pos[1]['average_buy_price'] else '('
               print('Total Return: $' + pos[1]['equity_change'], sign + pos[1]['percent_change'] + '%)')
               print('-------------------------------')
            # Print concluding divider
            print('NET VALUE: $' + str(round(float(BOT.account['equity']) - float(BOT.account['cash']), ndigits=6)), '+ $' + BOT.account['cash'], 'in CASH', '\n-------------------------------')
         # Invalid command
         case _:
            print('Invalid command for SriBot! Please try again.')

if __name__ == '__main__':
   """
   Driver code.
   """
   # Create SriBot instance w/ 'Moderate Risk Appetite' portfolio weights
   BOT: SriBot = SriBot({'QQQ': 0.312, 'JEPQ': 0.0375, 'BBIN': 0.1205, 'AGG': 0.3375, 'BBAG': 0.1425, '$$$': 0.05})
   
   # Create and start daemon thread to auto-rebalance portfolio on a schedule 
   # while allowing main thread to run
   autoRBT = threading.Thread(target=autoRebalance, args=[BOT])
   autoRBT.daemon = True
   autoRBT.start()
   
   # Start REPL
   REPL(BOT=BOT)
