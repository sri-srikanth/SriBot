import os, pyotp, time
import robin_stocks.robinhood as rs
import logging

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
      totp: pyotp.TOTP = pyotp.TOTP(s=os.environ.get('RHMastK')).now()
      # Log into Robinhood using UN/PWD & TOTP
      rs.login(os.environ.get('MainEmail'),os.environ.get('RHPass'),mfa_code=totp)
      
      # Store user-desired weights
      self.weights = {}
      weightSum = 0
      for w in weights.items():
         # Check for negative weights
         if w[1] < 0:
            raise Exception(f'Symbol ({w[0]}) weight cannot be negative!')
         weightSum += w[1]
         # Ensure total portfolio weight <= 1.0
         if weightSum > 1.0:
            raise Exception('Total portfolio weight cannot exceed 1.0!')
         # Add symbol and corresponding weight to self.weights
         self.weights[w[0]] = w[1]
         
      # Store user's current Robinhood positions
      self.positions: dict = rs.build_holdings()
      # Calculate total money invested
      self.positionsValue: float = sum((float(self.positions[symbol]['equity']) for symbol in self.positions.keys()))
      
   def rebalance(self):
      """
      Portfolio rebalancing method. Method analyzes user's current positions
      and determines whether portfolio rebalancing is required (TODO: based on 
      a threshold?). If rebalancing is required, overweight positions are 
      trimmed and underweight positions are added to.
      """
      # Initialize dictionary to hold needed changes to portfolio
      positionChanges = {k:0 for k in self.weights}
      # Check if positions out-of-balance by ANY (TODO: change?) amount
      for w in self.weights.items():
         # Calculate ideal position value
         idealAmount = w[1] * self.positionsValue
         # Get current position value in portfolio
         try:
            currAmount = float(self.positions[w[0]]['equity'])
         except KeyError:
            currAmount = 0
         # Calculate change needed in position value to reach ideal weighting
         positionChanges[w[0]] -= currAmount - idealAmount
            
      # Execute trades based on required position changes
      for stock in positionChanges.items():
         # Overweight stock in portfolio
         if stock[1] < 0:
            rs.order_sell_fractional_by_price(symbol=stock[0], amountInDollars=abs(stock[1]),timeInForce='gfd',extendedHours=True)
         # Underweight stock in portfolio
         elif stock[1] > 0:
            rs.order_buy_fractional_by_price(symbol=stock[0], amountInDollars=stock[1],timeInForce='gfd',extendedHours=True)
            

if __name__ == '__main__':
   try:
      # Test instance with sample weights
      BOT = SriBot({'JEPQ': 0.5, 'LLY': 0.2, 'UNH': 0.3})
      BOT.rebalance()
   except Exception as e: 
      logging.exception(f' {e}',exc_info=False) # TODO: reveal trace?
   
   # End current Robinhood session
   rs.logout()
   print('DONE')