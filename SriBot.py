import os, pyotp, time
import robin_stocks.robinhood as rs
import logging

class SriBot:
   def __init__(self, weights: dict) -> None:
      """
      Initializer method for SriBot. Requires a dictionary of weights
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

if __name__ == '__main__':
   try:
      # Test instance with sample weights
      BOT = SriBot({'TSLA': 0.5, 'ARLP': 0.2, 'MSFT': 0.3})
   except Exception as e: 
      logging.exception(f' {e}',exc_info=False)
   
   # End current Robinhood session
   rs.logout()
   print('DONE')