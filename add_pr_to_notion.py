#!/usr/bin/env python3
"""
Fetch PR details and add directly to Notion page.
Usage: python add_pr_to_notion.py <repo_owner> <repo_name> <pr_number>
"""
import sys
import os
from dotenv import load_dotenv
from github_integration import fetch_pr_changes
from notion_client import Client
import traceback

# Load environment variables
load_dotenv()

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

def add_to_notion_direct(repo_owner: str, repo_name: str, pr_number: int, pr_info: dict, summary: str) -> bool:
    """Add PR summary to Notion page directly."""
    try:
        notion_api_key = os.getenv("NOTION_API_KEY")
        notion_page_id = os.getenv("NOTION_PAGE_ID")
        
        if not notion_api_key or not notion_page_id:
            print("❌ Error: Missing Notion API key or page ID in environment variables")
            return False
        
        notion = Client(auth=notion_api_key)
        
        # Create title
        title = f"PR #{pr_number}: {pr_info.get('title', 'GitHub PR Review')}"
        
        # Create rich blocks for Notion
        blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": title}
                    }]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": f"Repository: {repo_owner}/{repo_name}"},
                        "annotations": {"bold": True}
                    }]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": summary}
                    }]
                }
            }
        ]
        
        # Create page in Notion
        response = notion.pages.create(
            parent={"type": "page_id", "page_id": notion_page_id},
            properties={
                "title": {
                    "title": [{
                        "text": {"content": title}
                    }]
                }
            },
            children=blocks
        )
        
        print(f"✅ Successfully added PR to Notion!")
        print(f"   Page ID: {response['id']}")
        print(f"   URL: https://notion.so/{response['id'].replace('-', '')}")
        return True
        
    except Exception as e:
        print(f"❌ Error adding to Notion: {str(e)}")
        traceback.print_exc()
        return False

def main():
    if len(sys.argv) != 4:
        print("Usage: python add_pr_to_notion.py <repo_owner> <repo_name> <pr_number>")
        print("Example: python add_pr_to_notion.py adam-ben-rhaiem car-damage-inspection-system 1")
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
    
    # Add to Notion
    print("\n📌 Adding to Notion...")
    success = add_to_notion_direct(repo_owner, repo_name, pr_number, pr_info, summary)
    
    if success:
        print(f"\n✅ Successfully completed! PR summary added to Notion.")
    else:
        print(f"\n❌ Failed to add PR summary to Notion.")
        sys.exit(1)

if __name__ == "__main__":
    main()
