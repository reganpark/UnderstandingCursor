"""
Reddit Scraper Class
Modular Reddit scraper for posts and comments
"""

import praw
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime
import time
from typing import Tuple, Optional

class RedditScraper:
    """A class to handle Reddit scraping operations"""
    
    def __init__(self, load_env: bool = True):
        """
        Initialize the Reddit scraper
        
        Args:
            load_env: Whether to load environment variables
        """
        if load_env:
            load_dotenv()
        
        self.reddit = self._initialize_reddit()
        self.posts_data = []
        self.comments_data = []
    
    def _initialize_reddit(self) -> praw.Reddit:
        """Initialize Reddit API connection for read-only access"""
        return praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )
    
    def check_credentials(self) -> bool:
        """
        Check if required environment variables are set
        
        Returns:
            bool: True if all required credentials are available
        """
        required_vars = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USER_AGENT']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            print("Please update the .env file with your Reddit API credentials")
            return False
        
        print("✅ Reddit API credentials found")
        return True
    
    def scrape_subreddit(self, 
                        subreddit_name: str, 
                        limit: int = 100,  # Changed from 25 to 100
                        sort_type: str = 'hot',
                        include_comments: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Scrape posts and optionally comments from a subreddit
        
        Args:
            subreddit_name: Name of the subreddit to scrape
            limit: Number of posts to scrape
            sort_type: Type of sorting ('hot', 'new', 'top', 'rising')
            include_comments: Whether to scrape comments
            
        Returns:
            Tuple of (posts_dataframe, comments_dataframe)
        """
        print(f"🔍 Scraping r/{subreddit_name}...")
        print(f"Getting {sort_type} {limit} posts{'with all comments' if include_comments else ''}...")
        
        subreddit = self.reddit.subreddit(subreddit_name)
        
        # Get posts based on sort type
        if sort_type == 'hot':
            posts = subreddit.hot(limit=limit)
        elif sort_type == 'new':
            posts = subreddit.new(limit=limit)
        elif sort_type == 'top':
            posts = subreddit.top(limit=limit)
        elif sort_type == 'rising':
            posts = subreddit.rising(limit=limit)
        else:
            raise ValueError(f"Invalid sort_type: {sort_type}")
        
        posts_data = []
        comments_data = []
        
        for i, post in enumerate(posts, 1):
            print(f"Processing post {i}/{limit}: {post.title[:50]}...")
            
            # Collect post data
            post_info = self._extract_post_data(post, subreddit_name)
            posts_data.append(post_info)
            
            # Get comments if requested
            if include_comments:
                post_comments = self._extract_comments_data(post)
                comments_data.extend(post_comments)
                print(f"  Collected {len(post_comments)} comments")
            
            # Rate limiting
            time.sleep(2)
        
        self.posts_data = posts_data
        self.comments_data = comments_data
        
        return pd.DataFrame(posts_data), pd.DataFrame(comments_data)
    
    def _extract_post_data(self, post, subreddit_name: str) -> dict:
        """Extract data from a Reddit post"""
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
            'domain': post.domain,
            'is_video': post.is_video,
            'over_18': post.over_18
        }
    
    def _extract_comments_data(self, post) -> list:
        """Extract all comments from a Reddit post"""
        comments_data = []
        
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
                    'controversiality': comment.controversiality,
                    'edited': bool(comment.edited)
                }
                comments_data.append(comment_info)
        
        return comments_data
    
    def _calculate_comment_depth(self, comment) -> int:
        """Calculate the depth of a comment in the thread"""
        try:
            return len(comment.permalink.split('/')) - 7
        except:
            return 0
    
    def scrape_multiple_subreddits(self, 
                                  subreddits: list, 
                                  posts_per_sub: int = 100,  # Changed from 25 to 100
                                  sort_type: str = 'hot',
                                  include_comments: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Scrape multiple subreddits
        
        Args:
            subreddits: List of subreddit names
            posts_per_sub: Number of posts per subreddit
            sort_type: Sorting method
            include_comments: Whether to include comments
            
        Returns:
            Combined dataframes for posts and comments
        """
        all_posts = []
        all_comments = []
        
        for subreddit in subreddits:
            try:
                posts_df, comments_df = self.scrape_subreddit(
                    subreddit, posts_per_sub, sort_type, include_comments
                )
                all_posts.append(posts_df)
                all_comments.append(comments_df)
                print(f"✅ Completed r/{subreddit}")
            except Exception as e:
                print(f"❌ Error scraping r/{subreddit}: {e}")
                continue
        
        combined_posts = pd.concat(all_posts, ignore_index=True) if all_posts else pd.DataFrame()
        combined_comments = pd.concat(all_comments, ignore_index=True) if all_comments else pd.DataFrame()
        
        return combined_posts, combined_comments 