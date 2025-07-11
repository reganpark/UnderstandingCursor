"""
Korea Travel Reddit Scraper - Main Script
Uses modular classes for extensible Reddit scraping
"""

from reddit_scraper import RedditScraper
from data_manager import DataManager

def main():
    """Main function to run the Korea Travel Reddit scraper"""
    print("🇰🇷 Korea Travel Reddit Scraper")
    print("=" * 50)
    
    # Initialize components
    scraper = RedditScraper()
    data_manager = DataManager(output_dir="data")
    
    # Check credentials
    if not scraper.check_credentials():
        return
    
    try:
        print("🔍 Starting scraping process...")
        
        # Scrape r/koreatravel
        posts_df, comments_df = scraper.scrape_subreddit(
            subreddit_name='koreatravel',
            limit=25,
            sort_type='hot',
            include_comments=True
        )
        
        # Save data
        data_manager.save_data(posts_df, comments_df, prefix="koreatravel")
        
        # Perform analysis
        data_manager.analyze_data(posts_df, comments_df)
        
        print("\n✅ Scraping completed successfully!")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("Make sure your Reddit API credentials are correct in the .env file")

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
            posts_per_sub=10,
            sort_type='hot',
            include_comments=True
        )
        
        data_manager.save_data(posts_df, comments_df, prefix="travel_subreddits")
        data_manager.analyze_data(posts_df, comments_df)
        
        print("✅ Multiple subreddits scraping completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Run the main Korea Travel scraper
    main()
    
    # Uncomment to run multiple subreddits scraper
    # scrape_multiple_travel_subreddits()
