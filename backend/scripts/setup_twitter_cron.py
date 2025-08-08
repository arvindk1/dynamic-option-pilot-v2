#!/usr/bin/env python3
"""
Setup automated Twitter posting via cron jobs
"""
import os
import subprocess
from datetime import datetime

def setup_twitter_cron_jobs():
    """Setup cron jobs for automated Twitter posting."""
    
    # Get the current directory path
    backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_path = os.path.dirname(backend_path)
    
    # Define cron jobs for different posting times (Eastern Time)
    cron_jobs = [
        # Pre-market intelligence - 6:30 AM ET (11:30 UTC during EST, 10:30 UTC during EDT)
        {
            "time": "30 11 * * 1-5",  # Mon-Fri 11:30 UTC (EST)
            "command": f"curl -X POST http://localhost:8000/api/social/twitter/post-premarket",
            "description": "Pre-market intelligence tweet"
        },
        
        # Market open reaction - 9:35 AM ET (14:35 UTC during EST, 13:35 UTC during EDT) 
        {
            "time": "35 14 * * 1-5",  # Mon-Fri 14:35 UTC (EST)
            "command": f"curl -X POST http://localhost:8000/api/social/twitter/post-market-open",
            "description": "Market open reaction tweet"
        },
        
        # Market close wrap - 4:05 PM ET (21:05 UTC during EST, 20:05 UTC during EDT)
        {
            "time": "5 21 * * 1-5",   # Mon-Fri 21:05 UTC (EST)
            "command": f"curl -X POST http://localhost:8000/api/social/twitter/post-market-close",
            "description": "Market close wrap tweet"
        },
        
        # Educational content - 12:00 PM ET (17:00 UTC during EST, 16:00 UTC during EDT)
        {
            "time": "0 17 * * 1-5",   # Mon-Fri 17:00 UTC (EST)
            "command": f"curl -X POST 'http://localhost:8000/api/social/twitter/post-educational?topic=daily'",
            "description": "Educational content tweet"
        },
        
        # Weekend recap - Saturday 10:00 AM ET
        {
            "time": "0 15 * * 6",     # Saturday 15:00 UTC (EST)
            "command": f"curl -X POST http://localhost:8000/api/social/twitter/post-weekend-recap",
            "description": "Weekend market recap"
        }
    ]
    
    # Generate crontab entries
    crontab_entries = []
    for job in cron_jobs:
        entry = f"{job['time']} {job['command']} # {job['description']}"
        crontab_entries.append(entry)
    
    return crontab_entries

def install_cron_jobs():
    """Install the cron jobs to system crontab."""
    
    try:
        # Get existing crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        existing_crontab = result.stdout if result.returncode == 0 else ""
        
        # Generate new cron jobs
        new_jobs = setup_twitter_cron_jobs()
        
        # Create new crontab content
        crontab_content = existing_crontab
        
        # Add header comment
        crontab_content += "\n# Dynamic Options Pilot - Twitter Automation\n"
        
        # Add each job
        for job in new_jobs:
            crontab_content += job + "\n"
        
        # Write to temporary file
        temp_cron_file = "/tmp/twitter_crontab"
        with open(temp_cron_file, 'w') as f:
            f.write(crontab_content)
        
        # Install new crontab
        subprocess.run(['crontab', temp_cron_file], check=True)
        
        # Clean up
        os.remove(temp_cron_file)
        
        print("✅ Twitter cron jobs installed successfully!")
        print("\nScheduled posts:")
        for job in new_jobs:
            print(f"  {job}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing cron jobs: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def remove_twitter_cron_jobs():
    """Remove Twitter automation cron jobs."""
    
    try:
        # Get existing crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("No existing crontab found")
            return True
        
        existing_lines = result.stdout.split('\n')
        
        # Filter out Twitter automation lines
        filtered_lines = []
        skip_section = False
        
        for line in existing_lines:
            if "Dynamic Options Pilot - Twitter Automation" in line:
                skip_section = True
                continue
            elif skip_section and line.strip() and not line.startswith('#'):
                # This is a cron job line in our section
                if any(keyword in line for keyword in ['twitter', 'premarket', 'market-open', 'market-close']):
                    continue  # Skip this line
                else:
                    skip_section = False  # End of our section
            
            if not skip_section:
                filtered_lines.append(line)
        
        # Write filtered crontab
        temp_cron_file = "/tmp/filtered_crontab"
        with open(temp_cron_file, 'w') as f:
            f.write('\n'.join(filtered_lines))
        
        # Install filtered crontab
        subprocess.run(['crontab', temp_cron_file], check=True)
        
        # Clean up
        os.remove(temp_cron_file)
        
        print("✅ Twitter cron jobs removed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error removing cron jobs: {e}")
        return False

def show_cron_status():
    """Show current cron job status."""
    
    try:
        # Get current crontab
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode != 0:
            print("No crontab found")
            return
        
        lines = result.stdout.split('\n')
        twitter_jobs = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['twitter', 'premarket', 'market-open', 'market-close']):
                twitter_jobs.append(line)
        
        if twitter_jobs:
            print("📅 Current Twitter automation cron jobs:")
            for job in twitter_jobs:
                print(f"  {job}")
        else:
            print("📅 No Twitter automation cron jobs found")
            
        # Check if backend is running
        try:
            import requests
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print("✅ Backend server is running")
            else:
                print("⚠️ Backend server responded with error")
        except:
            print("❌ Backend server is not accessible")
            
    except Exception as e:
        print(f"❌ Error checking cron status: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python setup_twitter_cron.py install   # Install cron jobs")
        print("  python setup_twitter_cron.py remove    # Remove cron jobs")
        print("  python setup_twitter_cron.py status    # Show current status")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    if action == "install":
        install_cron_jobs()
    elif action == "remove":
        remove_twitter_cron_jobs()
    elif action == "status":
        show_cron_status()
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)