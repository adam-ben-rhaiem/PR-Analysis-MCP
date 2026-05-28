#!/usr/bin/env python3
"""
Batch process PR summaries and add them to Notion using the configured MCP server.
Reads from local pr_summaries.json and attempts to create Notion pages.
"""
import json
import os
import sys
from dotenv import load_dotenv
from notion_client import Client
import traceback

# Load environment variables
load_dotenv()

def load_pr_summaries(db_file: str = "pr_summaries.json") -> list:
    """Load PR summaries from local JSON database."""
    if not os.path.exists(db_file):
        print(f"❌ Database file not found: {db_file}")
        return []
    
    try:
        with open(db_file, 'r') as f:
            data = json.load(f)
        print(f"✅ Loaded {len(data)} PR summaries from {db_file}")
        return data
    except Exception as e:
        print(f"❌ Error loading database: {str(e)}")
        return []

def create_notion_blocks(pr_data: dict) -> list:
    """Create rich Notion blocks from PR data."""
    blocks = []
    
    # Title as heading
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{
                "type": "text",
                "text": {"content": f"PR #{pr_data['pr_number']}: {pr_data['pr_title']}"}
            }]
        }
    })
    
    # Metadata
    metadata_text = f"Repository: {pr_data['repo_owner']}/{pr_data['repo_name']} | Author: {pr_data['pr_author']} | Created: {pr_data['created_at']}"
    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": metadata_text},
                "annotations": {"italic": True}
            }]
        }
    })
    
    # Summary
    blocks.append({
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{
                "type": "text",
                "text": {"content": pr_data['summary']}
            }]
        }
    })
    
    # Divider
    blocks.append({
        "object": "block",
        "type": "divider"
    })
    
    return blocks

def add_prs_to_notion(pr_summaries: list) -> None:
    """Add all PR summaries to Notion page."""
    try:
        notion_api_key = os.getenv("NOTION_API_KEY")
        notion_page_id = os.getenv("NOTION_PAGE_ID")
        
        if not notion_api_key or not notion_page_id:
            print("❌ Error: Missing Notion API key or page ID in environment variables")
            return
        
        notion = Client(auth=notion_api_key)
        print(f"\n📌 Notion Integration:")
        print(f"   API Key: {notion_api_key[:20]}...")
        print(f"   Page ID: {notion_page_id}")
        
        success_count = 0
        failed_count = 0
        
        for i, pr_data in enumerate(pr_summaries, 1):
            try:
                print(f"\n[{i}/{len(pr_summaries)}] Processing PR #{pr_data['pr_number']} from {pr_data['repo_name']}...")
                
                # Create blocks
                blocks = create_notion_blocks(pr_data)
                
                # Create page in Notion
                response = notion.pages.create(
                    parent={"type": "page_id", "page_id": notion_page_id},
                    properties={
                        "title": {
                            "title": [{
                                "text": {
                                    "content": f"PR #{pr_data['pr_number']}: {pr_data['pr_title']}"
                                }
                            }]
                        }
                    },
                    children=blocks
                )
                
                print(f"✅ Successfully added to Notion: {response['id']}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ Failed to add PR to Notion: {str(e)}")
                failed_count += 1
        
        print(f"\n{'='*60}")
        print(f"📊 BATCH PROCESSING RESULTS")
        print(f"{'='*60}")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"Total: {len(pr_summaries)}")
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        traceback.print_exc()

def main():
    print("🚀 GitHub PR Batch Processor with Notion Integration")
    print("="*60)
    
    # Load summaries from local database
    pr_summaries = load_pr_summaries()
    
    if not pr_summaries:
        print("❌ No PR summaries to process")
        sys.exit(1)
    
    # Display loaded PRs
    print(f"\n📋 Loaded PR Summaries:")
    for pr in pr_summaries:
        print(f"   - {pr['repo_owner']}/{pr['repo_name']} PR #{pr['pr_number']}: {pr['pr_title']}")
    
    # Add to Notion
    print(f"\n📌 Adding to Notion...")
    add_prs_to_notion(pr_summaries)

if __name__ == "__main__":
    main()
