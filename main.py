import os
import argparse
import sys
from engine.advisor_engine import AdvisorEngine
from engine.execution_engine import ExecutionEngine

def main():
    parser = argparse.ArgumentParser(description="Titan Hammer - Production System")
    parser.add_argument('--advisor', action='store_true', help="Run Advisor Engine (Decision Layer)")
    parser.add_argument('--execute', action='store_true', help="Run Execution Engine (Action Layer)")
    parser.add_argument('--equity', type=float, help="Current Portfolio Equity (Required for Advisor)")
    
    args = parser.parse_args()

    # Configuration from Env Vars
    titan_equity = args.equity
    if titan_equity is None:
        env_equity = os.environ.get("TITAN_EQUITY")
        if env_equity:
            titan_equity = float(env_equity)
    
    titan_mode = os.environ.get("TITAN_MODE", "LIVE")
    titan_state_dir = os.environ.get("TITAN_STATE_DIR")

    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    if titan_state_dir:
        # If env var provided, use it (Cloud friendliness)
        state_dir = os.path.join(titan_state_dir, 'state')
        orders_dir = os.path.join(titan_state_dir, 'orders')
        logs_dir = os.path.join(titan_state_dir, 'logs')
    else:
        # Default local structure
        state_dir = os.path.join(base_dir, 'state')
        orders_dir = os.path.join(base_dir, 'orders')
        logs_dir = os.path.join(base_dir, 'logs')

    advisor_state_path = os.path.join(state_dir, 'engine_state.json')
    execution_output_path = os.path.join(orders_dir, 'target_allocation.json')
    
    # Ensure dirs
    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(orders_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    
    print(f">>> Titan Hammer initializing (Mode: {titan_mode})")

    if args.advisor:
        if titan_equity is None:
            print("ERROR: Equity value required. Set --equity or TITAN_EQUITY env var.")
            sys.exit(1)
            
        print(f">>> Starting Advisor Engine... (Equity: ${titan_equity:,.2f})")
        engine = AdvisorEngine(advisor_state_path, current_equity=titan_equity)
        engine.run()
        print(">>> Advisor Cycle Complete.")
        
    if args.execute:
        print(">>> Starting Execution Engine...")
        engine = ExecutionEngine(advisor_state_path, execution_output_path)
        engine.run()
        print(">>> Execution Cycle Complete.")

    if not args.advisor and not args.execute:
        parser.print_help()

if __name__ == "__main__":
    main()
