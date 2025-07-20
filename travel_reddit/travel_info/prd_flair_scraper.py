"""
PRD Flair-Based Reddit Scraper
Specialized scraper for r/koreatravel analysis by flair categories
Timeframe: January 1, 2025 - June 30, 2025
"""

import praw
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import time
from typing import Dict, List, Tuple, Optional

class PRDFlairScraper:
    """Specialized scraper for PRD analysis by flair categories"""
    
    def __init__(self, load_env: bool = True):
        """Initialize the PRD flair scraper"""
        if load_env:
            load_dotenv()
        
        self.reddit = self._initialize_reddit()
        
        # PRD timeframe: Jan 1 - June 30, 2025
        self.start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        self.end_date = datetime(2025, 6, 30, 23, 59, 59, tzinfo=timezone.utc)
        
        # PRD required flair categories
        self.target_flairs = [
            "Emergency",
            "Places to Visit", 
            "Itinerary",
            "Activities & Events",
            "Trip Report",
            "Money & Budget",
            "Shopping & Services",
            "K-Beauty",
            "Transit & Flight"
        ]
    
    def _initialize_reddit(self) -> praw.Reddit:
        """Initialize Reddit API connection"""
        return praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
    
    def check_credentials(self) -> bool:
        """Check if required environment variables are set"""
        required_vars = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            print("Please update the .env file with your Reddit API credentials")
            return False
        
        print("✅ Reddit API credentials found")
        return True
    
    def _is_in_date_range(self, post_timestamp: float) -> bool:
        """Check if post is within PRD timeframe"""
        post_date = datetime.fromtimestamp(post_timestamp, tz=timezone.utc)
        return self.start_date <= post_date <= self.end_date
    
    def _extract_post_data(self, post, subreddit_name: str) -> dict:
        """Extract data from a Reddit post with full URL"""
        return {
            'subreddit': subreddit_name,
            'post_id': post.id,
            'title': post.title,
            'author': str(post.author) if post.author else 'Unknown',
            'score': post.score,
            'upvote_ratio': post.upvote_ratio,
            'url': post.url,
            'selftext': post.selftext,
            'created_utc': post.created_utc,
            'created_date': datetime.fromtimestamp(post.created_utc),
            'num_comments': post.num_comments,
            'is_self': post.is_self,
            'flair': post.link_flair_text,
            'permalink': f"https://reddit.com{post.permalink}",
            'full_reddit_url': f"https://www.reddit.com{post.permalink}",  # PRD requirement
            'domain': post.domain,
            'is_video': post.is_video,
            'over_18': post.over_18
        }
    
    def _extract_comments_data(self, post) -> List[dict]:
        """Extract all comments from a Reddit post"""
        comments_data = []
        
        try:
            # Replace "more comments" links to get all comments
            post.comments.replace_more(limit=None)
            
            for comment in post.comments.list():
                if hasattr(comment, 'body'):
                    comment_info = {
                        'post_id': post.id,
                        'comment_id': comment.id,
                        'parent_id': comment.parent_id,
                        'author': str(comment.author) if comment.author else 'Unknown',
                        'body': comment.body,
                        'score': comment.score,
                        'created_utc': comment.created_utc,
                        'created_date': datetime.fromtimestamp(comment.created_utc),
                        'is_root': comment.parent_id == post.fullname,
                        'depth': self._calculate_comment_depth(comment),
                        'permalink': f"https://reddit.com{comment.permalink}",
                        'full_reddit_url': f"https://www.reddit.com{comment.permalink}",  # PRD requirement
                        'controversiality': comment.controversiality,
                        'edited': bool(comment.edited)
                    }
                    comments_data.append(comment_info)
        except Exception as e:
            print(f"⚠️ Error extracting comments for post {post.id}: {e}")
        
        return comments_data
    
    def _calculate_comment_depth(self, comment) -> int:
        """Calculate the depth of a comment in the thread"""
        try:
            return len(comment.permalink.split('/')) - 7
        except:
            return 0
    
    def scrape_by_flair(self, flair: str, limit: int = 1000) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Scrape posts by specific flair within PRD timeframe
        Note: Flair filtering only works with 'new' sorting on Reddit API
        
        Args:
            flair: Target flair to search for
            limit: Maximum posts to check (will filter by date and flair)
            
        Returns:
            Tuple of (posts_dataframe, comments_dataframe)
        """
        print(f"🏷️ Scraping r/koreatravel for flair: '{flair}'")
        print(f"📅 Date range: {self.start_date.date()} to {self.end_date.date()}")
        print("⚠️ Note: Using 'new' sorting only (flair filtering limitation)")
        
        subreddit = self.reddit.subreddit('koreatravel')
        posts_data = []
        comments_data = []
        
        # Only use 'new' sorting since flair filtering doesn't work with hot/top
        posts = subreddit.new(limit=limit)
        
        processed_count = 0
        found_count = 0
        
        for post in posts:
            processed_count += 1
            
            # Check if post is in date range
            if not self._is_in_date_range(post.created_utc):
                continue
            
            # Check if flair matches (case-insensitive)
            post_flair = post.link_flair_text
            if not post_flair or flair.lower() not in post_flair.lower():
                continue
            
            found_count += 1
            
            print(f"✅ Found ({found_count}): {post.title[:60]}... [Score: {post.score}]")
            
            # Extract post data
            post_info = self._extract_post_data(post, 'koreatravel')
            posts_data.append(post_info)
            
            # Extract comments
            post_comments = self._extract_comments_data(post)
            comments_data.extend(post_comments)
            
            # Rate limiting
            time.sleep(1)
        
        print(f"📊 Processed {processed_count} posts, found {found_count} with flair '{flair}'")
        print(f"📊 Total: {len(posts_data)} posts, {len(comments_data)} comments")
        
        return pd.DataFrame(posts_data), pd.DataFrame(comments_data)
    
    def scrape_all_prd_flairs(self, posts_per_flair: int = 1000) -> Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Scrape all PRD required flairs
        
        Args:
            posts_per_flair: Maximum posts to check per flair
            
        Returns:
            Dictionary with flair as key and (posts_df, comments_df) as value
        """
        if not self.check_credentials():
            return {}
        
        print("🚀 Starting PRD flair scraping for r/koreatravel")
        print(f"📋 Target flairs: {', '.join(self.target_flairs)}")
        print("⚠️ Note: Using 'new' sorting only due to Reddit API flair limitations")
        print("=" * 60)
        
        results = {}
        
        for i, flair in enumerate(self.target_flairs, 1):
            try:
                print(f"[{i}/{len(self.target_flairs)}] Processing: {flair}")
                posts_df, comments_df = self.scrape_by_flair(flair, posts_per_flair)
                results[flair] = (posts_df, comments_df)
                
                print(f"✅ Completed: {flair}")
                print("-" * 40)
                
                # Longer pause between flairs to be respectful to API
                time.sleep(3)
                
            except Exception as e:
                print(f"❌ Error scraping flair '{flair}': {e}")
                results[flair] = (pd.DataFrame(), pd.DataFrame())
                continue
        
        self._print_summary(results)
        return results
    
    def _print_summary(self, results: Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]):
        """Print summary of scraping results"""
        print("\n📊 PRD SCRAPING SUMMARY")
        print("=" * 50)
        
        total_posts = 0
        total_comments = 0
        
        for flair, (posts_df, comments_df) in results.items():
            posts_count = len(posts_df)
            comments_count = len(comments_df)
            total_posts += posts_count
            total_comments += comments_count
            
            print(f"{flair:<20} | Posts: {posts_count:<4} | Comments: {comments_count:<5}")
        
        print("-" * 50)
        print(f"{'TOTAL':<20} | Posts: {total_posts:<4} | Comments: {total_comments:<5}")
    
    def save_flair_data(self, results: Dict[str, Tuple[pd.DataFrame, pd.DataFrame]], output_dir: str = "prd_data"):
        """
        Save scraped data organized by flair
        
        Args:
            results: Results from scrape_all_prd_flairs
            output_dir: Directory to save files
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"📁 Created directory: {output_dir}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for flair, (posts_df, comments_df) in results.items():
            if posts_df.empty:
                continue
                
            # Clean flair name for filename
            clean_flair = flair.replace(" ", "_").replace("&", "and").lower()
            
            posts_file = os.path.join(output_dir, f"prd_{clean_flair}_posts_{timestamp}.csv")
            comments_file = os.path.join(output_dir, f"prd_{clean_flair}_comments_{timestamp}.csv")
            
            posts_df.to_csv(posts_file, index=False)
            comments_df.to_csv(comments_file, index=False)
            
            print(f"💾 Saved {flair}: {posts_file}")


def main():
    """Main execution function"""
    scraper = PRDFlairScraper()
    
    if not scraper.check_credentials():
        return
    
    print("🇰🇷 PRD Korea Travel Flair Scraper")
    print("=" * 50)
    print("This will scrape r/koreatravel by flair categories for PRD analysis")
    print(f"Timeframe: Jan 1 - June 30, 2025")
    print("⚠️ Note: Only 'new' sorting available for flair filtering")
    print()
    
    proceed = input("Do you want to proceed? (y/n): ").strip().lower()
    if proceed != 'y':
        print("👋 Scraping cancelled")
        return
    
    # Scrape all PRD flairs
    results = scraper.scrape_all_prd_flairs(posts_per_flair=1500)  # Increased limit
    
    # Save the data
    scraper.save_flair_data(results)
    
    print("\n✅ PRD flair scraping completed!")
    print("📂 Data saved in 'prd_data' directory")


if __name__ == "__main__":
    main() 