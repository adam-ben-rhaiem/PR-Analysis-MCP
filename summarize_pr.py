#!/usr/bin/env python3
"""
Script to fetch a GitHub PR, summarize changes, and add to Notion.
Usage: python summarize_pr.py <repo_owner> <repo_name> <pr_number>
"""
import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from github_integration import fetch_pr_changes
from notion_client import Client
import traceback

# Load environment variables
load_dotenv()

# Local database file for storing PR summaries
PR_DB_FILE = "pr_summaries.json"

def summarize_pr_changes(pr_info: dict) -> str:
    """Generate a summary of PR changes."""
    if not pr_info:
        return "Unable to fetch PR information"
    
    summary = f"PR #{pr_info.get('title', 'Unknown')}\n"
    summary += f"Author: {pr_info.get('author', 'Unknown')}\n"
    summary += f"Created: {pr_info.get('created_at', 'Unknown')}\n"
    summary += f"State: {pr_info.get('state', 'Unknown')}\n\n"
    
    summary += f"Description:\n{pr_info.get('description', 'No description provided')}\n\n"
    
    summary += f"Changes Summary:\n"
    summary += f"Total Files Changed: {pr_info.get('total_changes', 0)}\n\n"
    
    changes = pr_info.get('changes', [])
    for change in changes:
        summary += f"- {change['filename']} ({change['status']}): +{change['additions']} -{change['deletions']}\n"
    
    return summary

def save_to_local_db(repo_owner: str, repo_name: str, pr_number: int, pr_info: dict, summary: str) -> bool:
    """Save PR summary to local JSON database."""
    try:
        # Load existing data
        if os.path.exists(PR_DB_FILE):
            with open(PR_DB_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = []
        
        # Create new entry
        entry = {
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "pr_number": pr_number,
            "pr_title": pr_info.get('title', 'Unknown'),
            "pr_author": pr_info.get('author', 'Unknown'),
            "created_at": pr_info.get('created_at', ''),
            "summary": summary,
            "added_to_db_at": datetime.now().isoformat()
        }
        
        data.append(entry)
        
        # Save to file
        with open(PR_DB_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Saved PR summary to local database: {PR_DB_FILE}")
        return True
    except Exception as e:
        print(f"❌ Error saving to local database: {str(e)}")
        traceback.print_exc()
        return False

def add_to_notion(title: str, summary: str) -> bool:
    """Add the PR summary to Notion."""
    try:
        notion_api_key = os.getenv("NOTION_API_KEY")
        notion_page_id = os.getenv("NOTION_PAGE_ID")
        
        if not notion_api_key or not notion_page_id:
            print("❌ Error: Missing Notion API key or page ID in environment variables")
            return False
        
        notion = Client(auth=notion_api_key)
        
        # Create a new page in Notion
        response = notion.pages.create(
            parent={"type": "page_id", "page_id": notion_page_id},
            properties={
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": summary
                                }
                            }
                        ]
                    }
                }
            ]
        )
        
        print(f"✅ Successfully added PR summary to Notion: {response['id']}")
        return True
    except Exception as e:
        print(f"❌ Error adding to Notion: {str(e)}")
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) != 4:
        print("Usage: python summarize_pr.py <repo_owner> <repo_name> <pr_number>")
        print("Example: python summarize_pr.py Amir-Jribi plant-health 2")
        sys.exit(1)
    
    repo_owner = sys.argv[1]
    repo_name = sys.argv[2]
    pr_number = int(sys.argv[3])
    
    print(f"\n📊 Fetching PR #{pr_number} from {repo_owner}/{repo_name}...")
    
    # Fetch PR changes
    pr_info = fetch_pr_changes(repo_owner, repo_name, pr_number)
    
    if not pr_info:
        print("❌ Failed to fetch PR information")
        sys.exit(1)
    
    # Generate summary
    print("\n📝 Generating summary...")
    summary = summarize_pr_changes(pr_info)
    
    print("\n" + "="*60)
    print("PR SUMMARY")
    print("="*60)
    print(summary)
    print("="*60)
    
    # Save to local database (always works)
    print("\n💾 Saving to local database...")
    local_saved = save_to_local_db(repo_owner, repo_name, pr_number, pr_info, summary)
    
    # Try to add to Notion (optional)
    print("\n📌 Adding to Notion...")
    title = f"PR #{pr_number}: {pr_info.get('title', 'GitHub PR Review')}"
    notion_saved = add_to_notion(title, summary)
    
    if local_saved:
        print(f"\n✅ Successfully completed! PR summary saved to local database.")
        if notion_saved:
            print("✅ Also added to Notion!")
    else:
        print(f"\n❌ Failed to save PR summary.")
        sys.exit(1)

if __name__ == "__main__":
    main()
