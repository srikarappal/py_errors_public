"""
Race condition scenario that ThinkingSDK can help detect.
Shows how concurrent access to shared resources can cause data corruption.
"""

import thinking_sdk_client as thinking
import threading
import time
import random

# Start ThinkingSDK
thinking.start(config_file="thinkingsdk.yaml")

# Shared resource without proper synchronization
bank_account = {"balance": 1000.0}
transaction_log = []

def withdraw(amount, account_holder):
    """Withdraw money - contains race condition"""
    global bank_account, transaction_log
    
    try:
        
        
        # Race condition: Check balance and withdraw are not atomic
        current_balance = bank_account["balance"]
        
        
        if current_balance >= amount:
            # Process processing delay - this creates the race condition window
            time.sleep(random.uniform(0.01, 0.05))
            
            # Another thread might modify balance here!
            bank_account["balance"] = current_balance - amount
            
            transaction_log.append({
                "account_holder": account_holder,
                "action": "withdraw", 
                "amount": amount,
                "balance_after": bank_account["balance"],
                "timestamp": time.time()
            })
            
            
            
            # Detect data corruption - balance should never go negative
            if bank_account["balance"] < 0:
                raise RuntimeError(f"RACE CONDITION DETECTED: Account balance is negative! "
                                 f"Balance: ${bank_account['balance']}, "
                                 f"Last withdrawal: ${amount} by {account_holder}")
        else:
            
            
    except Exception as e:
        raise

def main():
    
    
    # Create multiple threads trying to withdraw simultaneously
    threads = []
    withdrawals = [
        (300, "Alice"),
        (400, "Bob"), 
        (500, "Charlie"),
        (200, "David")
    ]
    
    for amount, holder in withdrawals:
        thread = threading.Thread(
            target=withdraw, 
            args=(amount, holder),
            name=f"WithdrawThread-{holder}"
        )
        threads.append(thread)
    
    # Start all threads simultaneously to maximize race condition chance
    for thread in threads:
        thread.start()
    
    # Wait for all to complete
    for thread in threads:
        thread.join()
    
    
    
    
    # Analyze for data corruption
    total_withdrawn = sum(tx["amount"] for tx in transaction_log if tx["action"] == "withdraw")
    expected_balance = 1000.0 - total_withdrawn
    
    
    
    
    if bank_account["balance"] != expected_balance:
        raise RuntimeError(f"DATA CORRUPTION DETECTED: Expected ${expected_balance}, "
                         f"but got ${bank_account['balance']}. "
                         f"Race condition caused inconsistent state!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        time.sleep(2)  
    finally:
        thinking.stop()