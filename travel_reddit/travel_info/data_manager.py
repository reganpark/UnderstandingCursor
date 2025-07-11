"""
Data Manager Class
Handles saving, loading, and analyzing scraped Reddit data
"""

import pandas as pd
from datetime import datetime
import os
from typing import Tuple, Optional

class DataManager:
    """A class to handle data operations for scraped Reddit data"""
    
    def __init__(self, output_dir: str = "data"):
        """
        Initialize the data manager
        
        Args:
            output_dir: Directory to save data files
        """
        self.output_dir = output_dir
        self._ensure_output_dir()
    
    def _ensure_output_dir(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📁 Created output directory: {self.output_dir}")
    
    def save_data(self, 
                  posts_df: pd.DataFrame, 
                  comments_df: pd.DataFrame,
                  prefix: str = "reddit_data") -> Tuple[str, str]:
        """
        Save scraped data to CSV files
        
        Args:
            posts_df: DataFrame containing posts data
            comments_df: DataFrame containing comments data
            prefix: Prefix for filename
            
        Returns:
            Tuple of (posts_filename, comments_filename)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        posts_filename = os.path.join(self.output_dir, f"{prefix}_posts_{timestamp}.csv")
        comments_filename = os.path.join(self.output_dir, f"{prefix}_comments_{timestamp}.csv")
        
        posts_df.to_csv(posts_filename, index=False)
        comments_df.to_csv(comments_filename, index=False)
        
        print(f"\n📄 Data saved:")
        print(f"  Posts: {posts_filename}")
        print(f"  Comments: {comments_filename}")
        
        self._print_summary(posts_df, comments_df)
        
        return posts_filename, comments_filename
    
    def _print_summary(self, posts_df: pd.DataFrame, comments_df: pd.DataFrame):
        """Print summary statistics of the scraped data"""
        print(f"\n📊 Summary:")
        print(f"  Total posts: {len(posts_df)}")
        print(f"  Total comments: {len(comments_df)}")
        
        if len(posts_df) > 0:
            print(f"  Average comments per post: {len(comments_df)/len(posts_df):.1f}")
            print(f"  Average post score: {posts_df['score'].mean():.1f}")
            
            if 'subreddit' in posts_df.columns:
                print(f"  Subreddits covered: {posts_df['subreddit'].nunique()}")
                print(f"  Top subreddits by posts:")
                top_subs = posts_df['subreddit'].value_counts().head(5)
                for sub, count in top_subs.items():
                    print(f"    r/{sub}: {count} posts")
    
    def load_data(self, posts_file: str, comments_file: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load data from CSV files
        
        Args:
            posts_file: Path to posts CSV file
            comments_file: Path to comments CSV file
            
        Returns:
            Tuple of (posts_dataframe, comments_dataframe)
        """
        posts_df = pd.read_csv(posts_file)
        comments_df = pd.read_csv(comments_file)
        
        print(f"📖 Loaded data:")
        print(f"  Posts: {len(posts_df)} rows from {posts_file}")
        print(f"  Comments: {len(comments_df)} rows from {comments_file}")
        
        return posts_df, comments_df
    
    def analyze_data(self, posts_df: pd.DataFrame, comments_df: pd.DataFrame):
        """
        Perform basic analysis on the scraped data
        
        Args:
            posts_df: DataFrame containing posts data
            comments_df: DataFrame containing comments data
        """
        print("\n📈 Data Analysis:")
        print("=" * 40)
        
        # Posts analysis
        if not posts_df.empty:
            print("Posts Analysis:")
            print(f"  Date range: {posts_df['created_date'].min()} to {posts_df['created_date'].max()}")
            print(f"  Score statistics:")
            print(f"    Mean: {posts_df['score'].mean():.1f}")
            print(f"    Median: {posts_df['score'].median():.1f}")
            print(f"    Max: {posts_df['score'].max()}")
            
            print(f"  Post types:")
            print(f"    Self posts: {posts_df['is_self'].sum()}")
            print(f"    Link posts: {(~posts_df['is_self']).sum()}")
        
        # Comments analysis
        if not comments_df.empty:
            print(f"\nComments Analysis:")
            print(f"  Date range: {comments_df['created_date'].min()} to {comments_df['created_date'].max()}")
            print(f"  Score statistics:")
            print(f"    Mean: {comments_df['score'].mean():.1f}")
            print(f"    Median: {comments_df['score'].median():.1f}")
            print(f"    Max: {comments_df['score'].max()}")
            
            print(f"  Comment depth distribution:")
            depth_counts = comments_df['depth'].value_counts().sort_index().head(5)
            for depth, count in depth_counts.items():
                print(f"    Depth {depth}: {count} comments")
    
    def export_to_json(self, posts_df: pd.DataFrame, comments_df: pd.DataFrame, prefix: str = "reddit_data"):
        """Export data to JSON format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        posts_json = os.path.join(self.output_dir, f"{prefix}_posts_{timestamp}.json")
        comments_json = os.path.join(self.output_dir, f"{prefix}_comments_{timestamp}.json")
        
        posts_df.to_json(posts_json, orient='records', indent=2)
        comments_df.to_json(comments_json, orient='records', indent=2)
        
        print(f"📄 JSON files saved:")
        print(f"  Posts: {posts_json}")
        print(f"  Comments: {comments_json}") 