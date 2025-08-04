#!/usr/bin/env python3
"""
Strategy Deployment Management Tool
Handles Test → Live promotion and environment management
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent.parent))


class StrategyDeployer:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config" / "strategies"
        self.backup_dir = self.base_dir / "config" / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        self.environments = {
            "development": self.config_dir / "development",
            "production": self.config_dir / "production",
            "sandbox": self.config_dir / "sandbox",
        }

        # Ensure directories exist
        for env_dir in self.environments.values():
            env_dir.mkdir(exist_ok=True)

    def list_strategies(self, environment="all"):
        """List strategies in specified environment(s)"""
        print(f"\n📋 Strategy Inventory:")

        if environment == "all":
            envs_to_check = self.environments.keys()
        else:
            envs_to_check = [environment]

        for env in envs_to_check:
            env_path = self.environments[env]
            strategies = list(env_path.glob("*.json"))

            print(f"\n🏷️  {env.upper()} ({len(strategies)} strategies):")

            if not strategies:
                print("   (no strategies)")
                continue

            for strategy_file in strategies:
                try:
                    with open(strategy_file) as f:
                        config = json.load(f)

                    name = config.get("strategy_name", strategy_file.stem)
                    strategy_type = config.get("strategy_type", "UNKNOWN")
                    description = config.get("description", "No description")

                    # Get universe info
                    universe = config.get("universe", {})
                    universe_file = universe.get("universe_file", "N/A")
                    max_symbols = universe.get("max_symbols", "N/A")

                    print(f"   ✅ {name}")
                    print(f"      Type: {strategy_type}")
                    print(
                        f"      Universe: {universe_file} (max {max_symbols} symbols)"
                    )
                    print(f"      Description: {description[:60]}...")

                except Exception as e:
                    print(f"   ❌ {strategy_file.name} (Error: {e})")

    def validate_strategy(self, strategy_path):
        """Validate strategy configuration"""
        try:
            with open(strategy_path) as f:
                config = json.load(f)

            required_fields = [
                "strategy_name",
                "strategy_type",
                "universe",
                "position_parameters",
                "entry_signals",
            ]

            missing_fields = []
            for field in required_fields:
                if field not in config:
                    missing_fields.append(field)

            if missing_fields:
                return False, f"Missing required fields: {missing_fields}"

            # Validate universe configuration
            universe = config.get("universe", {})
            if "universe_file" not in universe:
                return False, "Universe must specify universe_file"

            # Handle relative paths correctly
            universe_file_path = universe["universe_file"]
            if universe_file_path.startswith("backend/"):
                # Remove backend/ prefix since we're already in backend directory
                universe_file_path = universe_file_path[8:]
            universe_file = self.base_dir / universe_file_path
            if not universe_file.exists():
                return False, f"Universe file not found: {universe_file}"

            return True, "Configuration valid"

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
        except Exception as e:
            return False, f"Validation error: {e}"

    def backup_strategy(self, environment, strategy_name):
        """Create backup of strategy before promotion"""
        source_path = self.environments[environment] / f"{strategy_name}.json"

        if not source_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{strategy_name}_{environment}_{timestamp}.json"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(source_path, backup_path)
        return backup_path

    def promote_strategy(self, strategy_name, from_env, to_env):
        """Promote strategy from one environment to another"""
        print(f"\n🚀 Promoting {strategy_name}: {from_env} → {to_env}")

        source_path = self.environments[from_env] / f"{strategy_name}.json"
        target_path = self.environments[to_env] / f"{strategy_name}.json"

        # Validate source exists
        if not source_path.exists():
            print(f"❌ Source strategy not found: {source_path}")
            return False

        # Validate source configuration
        valid, message = self.validate_strategy(source_path)
        if not valid:
            print(f"❌ Source validation failed: {message}")
            return False

        # Backup target if it exists
        if target_path.exists():
            backup_path = self.backup_strategy(to_env, strategy_name)
            print(f"💾 Created backup: {backup_path}")

        # Load source configuration
        with open(source_path) as f:
            config = json.load(f)

        # Apply environment-specific modifications
        if to_env == "production":
            # Production-specific settings
            config = self._apply_production_settings(config)
        elif to_env == "development":
            # Development-specific settings
            config = self._apply_development_settings(config)

        # Write promoted configuration
        with open(target_path, "w") as f:
            json.dump(config, f, indent=2)

        # Validate promoted configuration
        valid, message = self.validate_strategy(target_path)
        if not valid:
            print(f"❌ Promoted configuration invalid: {message}")
            return False

        print(f"✅ Successfully promoted {strategy_name} to {to_env}")
        print(f"📄 Configuration saved: {target_path}")

        return True

    def _apply_production_settings(self, config):
        """Apply production-specific settings"""
        # Ensure conservative production limits
        if "position_parameters" in config:
            config["position_parameters"]["max_positions"] = min(
                config["position_parameters"].get("max_positions", 5), 10
            )

        # Ensure universe limits for production
        if "universe" in config:
            config["universe"]["max_symbols"] = min(
                config["universe"].get("max_symbols", 10), 15
            )

        # Add production metadata
        config["environment"] = "production"
        config["deployed_at"] = datetime.now().isoformat()

        return config

    def _apply_development_settings(self, config):
        """Apply development-specific settings"""
        # More relaxed limits for testing
        if "position_parameters" in config:
            config["position_parameters"]["max_positions"] = min(
                config["position_parameters"].get("max_positions", 3), 5
            )

        # Smaller universe for faster testing
        if "universe" in config:
            config["universe"]["max_symbols"] = min(
                config["universe"].get("max_symbols", 10), 10
            )

        # Add development metadata
        config["environment"] = "development"
        config["deployed_at"] = datetime.now().isoformat()

        return config

    def set_environment(self, environment):
        """Set the active trading environment"""
        env_file = self.base_dir / ".env"

        # Read existing .env file
        env_vars = {}
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        env_vars[key] = value

        # Update environment
        env_vars["TRADING_ENVIRONMENT"] = environment.upper()

        # Write updated .env file
        with open(env_file, "w") as f:
            f.write("# Dynamic Options Pilot v2 Environment Configuration\n")
            f.write(f"# Updated: {datetime.now().isoformat()}\n\n")

            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")

        print(f"✅ Environment set to: {environment.upper()}")
        print(f"📄 Configuration saved: {env_file}")

        # Restart reminder
        print("\n⚠️  Backend restart required for environment change to take effect")
        print("   Run: python main.py")


def main():
    parser = argparse.ArgumentParser(
        description="Strategy Deployment Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all strategies
  python deploy_strategy.py list
  
  # List production strategies
  python deploy_strategy.py list --environment production
  
  # Promote strategy from development to production
  python deploy_strategy.py promote ThetaCropWeekly --from development --to production
  
  # Set active environment
  python deploy_strategy.py set-env production
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List strategies")
    list_parser.add_argument(
        "--environment",
        default="all",
        choices=["all", "development", "production", "sandbox"],
        help="Environment to list",
    )

    # Promote command
    promote_parser = subparsers.add_parser(
        "promote", help="Promote strategy between environments"
    )
    promote_parser.add_argument("strategy_name", help="Name of strategy to promote")
    promote_parser.add_argument(
        "--from",
        dest="from_env",
        required=True,
        choices=["development", "production", "sandbox"],
        help="Source environment",
    )
    promote_parser.add_argument(
        "--to",
        dest="to_env",
        required=True,
        choices=["development", "production", "sandbox"],
        help="Target environment",
    )

    # Set environment command
    env_parser = subparsers.add_parser("set-env", help="Set active trading environment")
    env_parser.add_argument(
        "environment",
        choices=["development", "production", "sandbox"],
        help="Environment to activate",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    deployer = StrategyDeployer()

    if args.command == "list":
        deployer.list_strategies(args.environment)
    elif args.command == "promote":
        deployer.promote_strategy(args.strategy_name, args.from_env, args.to_env)
    elif args.command == "set-env":
        deployer.set_environment(args.environment)


if __name__ == "__main__":
    main()
