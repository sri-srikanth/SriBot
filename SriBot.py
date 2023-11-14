import os, pyotp
import robin_stocks.robinhood as rs

class SriBot:
   def __init__(self, weights: dict) -> None:
      """
      Initializer method for SriBot instances. Requires a dictionary of weights
      to set up bot.

      Args:
          weights (dict): Dictionary {str:float} of weights with each key
          representing a ticker symbol and its corresponding value
          representing its weight. Weights must add up to 1.0.
      """
      
      # Generate 2FA TOTP using Robinhood master keys
      totp: pyotp.TOTP = pyotp.TOTP(s=os.environ.get('Tester266MastK')).now()
      # Log into Robinhood using UN/PWD & TOTP
      rs.login(os.environ.get('Tester266Email'), os.environ.get('Tester266Pass'),mfa_code=totp, store_session=True)
      # Store user-desired weights
      self.weights: dict = {}
      weightSum: float = 0
      for w in weights.items():
         # Check for negative weights
         if w[1] < 0:
            raiseError(msg=f'Symbol ({w[0]}) weight cannot be negative!')
         weightSum += w[1]
         # Ensure total portfolio weight <= 1.0
         if weightSum > 1.0:
            raiseError(msg='Total portfolio weight cannot exceed 1.0!')
         # Add symbol and corresponding weight to self.weights
         self.weights[w[0]] = w[1]
         
      # Store user's current Robinhood positions and account details
      self.positions: dict = rs.build_holdings()
      self.account: dict = rs.build_user_profile()
      
   def rebalance(self):
      """
      Portfolio rebalancing method. Method analyzes user's current positions
      and determines whether portfolio rebalancing is required (TODO: based on 
      a threshold?). If rebalancing is required, overweight positions are 
      trimmed and underweight positions are added to.
      """
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
         positionChanges[w[0]] -= round(currAmount - idealAmount, ndigits=6)
      positionChanges.pop('$$$')
      
      # Execute trades based on required position changes
      for stock in positionChanges.items():
         # Overweight stock in portfolio
         if stock[1] < 0:
            rs.order_sell_fractional_by_price(symbol=stock[0], amountInDollars=abs(stock[1]),timeInForce='gfd',extendedHours=True)
         # Underweight stock in portfolio
         elif stock[1] > 0:
            rs.order_buy_fractional_by_price(symbol=stock[0], amountInDollars=stock[1],timeInForce='gfd',extendedHours=True)

def raiseError(msg: str):
   """
   Error handling function for easy debugging. Only to be called during an active Robinhood session (while logged in).

   Args:
       msg (str): Error description.

   Raises:
       Exception: Exception that is raised to terminate the bot with 
       appropriate msg.
   """
   # End currently active Robinhood session before terminating bot
   rs.logout()
   raise Exception(msg)

if __name__ == '__main__':
   # Test instance with 'Moderate Risk Appetite' portfolio weights
   BOT: SriBot = SriBot({'QQQ': 0.312, 'JEPQ': 0.0375, 'BBIN': 0.1205, 'AGG': 0.3375, 'BBAG': 0.1425, '$$$': 0.05})
   BOT.rebalance()
   # End currently active Robinhood session
   rs.logout() # TODO: incorporate into the eventual scheduling loop
   