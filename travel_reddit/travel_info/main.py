"""
Korea Travel Reddit Scraper - Main Script
Uses modular classes for extensible Reddit scraping
Interactive mode selection via terminal input
"""

from datetime import datetime, timedelta
from reddit_scraper import RedditScraper
from data_manager import DataManager
import pandas as pd
from typing import Optional

def get_user_choices():
    """Get user choices through terminal input"""
    print("🇰🇷 Korea Travel Reddit Scraper")
    print("=" * 50)
    print()
    
    # Choose mode
    print("📋 Select scraping mode:")
    print("1. Daily mode (today's posts only)")
    print("2. Custom mode (specify number of posts)")
    print("3. Original mode (default behavior)")
    print()
    
    while True:
        mode_choice = input("Enter your choice (1-3): ").strip()
        if mode_choice == "1":
            mode = "daily"
            break
        elif mode_choice == "2":
            mode = "custom"
            break
        elif mode_choice == "3":
            mode = "original"
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    print()
    
    # Choose sort method
    print("🔄 Select sorting method:")
    print("1. New (newest posts first)")
    print("2. Hot (trending posts)")
    print("3. Top (highest scored posts)")
    print("4. Rising (rising posts)")
    print()
    
    while True:
        sort_choice = input("Enter your choice (1-4): ").strip()
        if sort_choice == "1":
            sort_type = "new"
            break
        elif sort_choice == "2":
            sort_type = "hot"
            break
        elif sort_choice == "3":
            sort_type = "top"
            break
        elif sort_choice == "4":
            sort_type = "rising"
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
    
    print()
    
    # Get subreddit
    subreddit = input("Enter subreddit name (default: koreatravel): ").strip()
    if not subreddit:
        subreddit = "koreatravel"
    
    print()
    
    # Get number of posts for custom mode
    post_count = 100  # default
    if mode == "custom":
        while True:
            try:
                post_input = input("Enter number of posts to scrape (default: 100): ").strip()
                if not post_input:
                    post_count = 100
                    break
                post_count = int(post_input)
                if post_count > 0:
                    break
                else:
                    print("❌ Please enter a positive number.")
            except ValueError:
                print("❌ Please enter a valid number.")
        print()
    
    return mode, sort_type, subreddit, post_count

def daily_mode(subreddit, sort_type, output_dir="data"):
    """Daily mode - gets posts from today only"""
    print(f"📅 Daily Mode: r/{subreddit} - {sort_type} posts from today")
    print("=" * 60)

    # NEW: Initialize with empty DataFrames instead of None.
    # This ensures the variables are always valid DataFrames.
    today_posts = pd.DataFrame()
    today_comments = pd.DataFrame()

    scraper = RedditScraper()
    data_manager = DataManager(output_dir=output_dir)
    
    if not scraper.check_credentials():
        return
    
    try:
        print("🔍 Searching for today's posts...")
        
        posts_df, comments_df = scraper.scrape_subreddit(
            subreddit_name=subreddit,
            limit=50,
            sort_type=sort_type,
            include_comments=True
        )
        
        today = datetime.now().date()
        posts_df['created_date'] = pd.to_datetime(posts_df['created_date'])
        posts_df['post_date'] = posts_df['created_date'].dt.date
        
        # CHANGED: Using .copy() ensures the result is always a new DataFrame,
        # resolving the "Series" ambiguity for the type checker.
        today_posts = posts_df[posts_df['post_date'] == today].copy()
        
        # This check now works perfectly, as today_posts is always a DataFrame.
        if not today_posts.empty:
            today_post_ids = today_posts['post_id'].tolist()
            today_comments = comments_df[comments_df['post_id'].isin(today_post_ids)].copy()
        else:
            # If no posts, ensure comments_df is also an empty DataFrame with correct columns
            today_comments = pd.DataFrame(columns=comments_df.columns)
        
        print(f"📊 Found {len(today_posts)} posts from today out of {len(posts_df)} total posts checked")
        
        today_str = datetime.now().strftime("%Y%m%d")
        timestamp = datetime.now().strftime("%H%M%S")
        prefix = f"daily_{sort_type}_{subreddit}_{today_str}_{timestamp}"

        # Ensure we're passing DataFrames, not Series
        if isinstance(today_posts, pd.DataFrame) and isinstance(today_comments, pd.DataFrame):
            data_manager.save_data(today_posts, today_comments, prefix=prefix)
            data_manager.analyze_data(today_posts, today_comments)
        else:
            print("❌ Error: Expected DataFrames but got different types")
            
        print("✅ Daily scraping completed!")

    except Exception as e:
        print(f"❌ Daily scraping failed: {e}")

def custom_mode(subreddit, sort_type, post_count, output_dir="data"):
    """Custom mode - gets specified number of posts"""
    print(f"⚙️ Custom Mode: r/{subreddit} - {post_count} {sort_type} posts")
    print("=" * 60)
    
    scraper = RedditScraper()
    data_manager = DataManager(output_dir=output_dir)
    
    if not scraper.check_credentials():
        return
    
    try:
        print(f"🔍 Scraping {post_count} {sort_type} posts...")
        
        posts_df, comments_df = scraper.scrape_subreddit(
            subreddit_name=subreddit,
            limit=post_count,
            sort_type=sort_type,
            include_comments=True
        )
        
        # Save with mode and method in filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"custom_{sort_type}_{subreddit}_{post_count}posts_{timestamp}"
        
        data_manager.save_data(posts_df, comments_df, prefix=prefix)
        data_manager.analyze_data(posts_df, comments_df)
        
        print("✅ Custom scraping completed!")
        
    except Exception as e:
        print(f"❌ Custom scraping failed: {e}")

def original_mode(sort_type):
    """Original mode with chosen sort type"""
    print(f"🔄 Original Mode with {sort_type} sorting")
    print("=" * 60)
    
    scraper = RedditScraper()
    data_manager = DataManager(output_dir="data")
    
    if not scraper.check_credentials():
        return
    
    try:
        print("🔍 Starting original scraping process...")
        
        posts_df, comments_df = scraper.scrape_subreddit(
            subreddit_name='koreatravel',
            limit=100,
            sort_type=sort_type,
            include_comments=True
        )
        
        # Save with mode and method in filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"original_{sort_type}_koreatravel_{timestamp}"
        
        data_manager.save_data(posts_df, comments_df, prefix=prefix)
        data_manager.analyze_data(posts_df, comments_df)
        
        print("\n✅ Original scraping completed successfully!")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")

def scrape_multiple_travel_subreddits():
    """Example function to scrape multiple travel subreddits"""
    print("🌍 Multiple Travel Subreddits Scraper")
    print("=" * 50)
    
    scraper = RedditScraper()
    data_manager = DataManager(output_dir="data")
    
    if not scraper.check_credentials():
        return
    
    travel_subreddits = [
        'koreatravel',
        'japantravel', 
        'solotravel',
        'backpacking'
    ]
    
    try:
        posts_df, comments_df = scraper.scrape_multiple_subreddits(
            subreddits=travel_subreddits,
            posts_per_sub=100,
            sort_type='new',
            include_comments=True
        )
        
        data_manager.save_data(posts_df, comments_df, prefix="travel_subreddits")
        data_manager.analyze_data(posts_df, comments_df)
        
        print("✅ Multiple subreddits scraping completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        # Get user choices through terminal input
        mode, sort_type, subreddit, post_count = get_user_choices()
        
        print(f"🚀 Starting scraper with:")
        print(f"   Mode: {mode}")
        print(f"   Sort: {sort_type}")
        print(f"   Subreddit: r/{subreddit}")
        if mode == "custom":
            print(f"   Posts: {post_count}")
        print()
        
        # Execute based on chosen mode
        if mode == "daily":
            daily_mode(subreddit, sort_type)
        elif mode == "custom":
            custom_mode(subreddit, sort_type, post_count)
        elif mode == "original":
            original_mode(sort_type)
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Scraping cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
