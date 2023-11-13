import os, pyotp, time
import robin_stocks.robinhood as rs

class SriBot:
   def __init__(self, weights: dict) -> None:
      # Generate 2FA TOTP using Robinhood master key
      totp: pyotp.TOTP = pyotp.TOTP(s=os.environ.get('RHMastK')).now()
      # Log into Robinhood using UN/PWD & TOTP
      rs.login(os.environ.get('MainEmail'),os.environ.get('RHPass'),mfa_code=totp)
      
      # Store user-desired weights
      self.weights: dict = dict(weights)
      # Store user's current Robinhood positions
      self.positions: dict = rs.build_holdings()
      # Calculate total money invested
      self.positionsValue: float = sum((float(self.positions[symbol]['equity']) for symbol in self.positions.keys()))
            

# Driver code
if __name__ == '__main__':
   # Test instance with sample weights
   BOT = SriBot({'TSLA': 0.5, 'ARLP': 0.2, 'MSFT': 0.3})
   # End current Robinhood session
   rs.logout()
   print('DONE')